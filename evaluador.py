"""
evaluador.py
Módulo de evaluación y validación de horarios para la EII (GCID - ULPGC).
Implementa las restricciones definidas en restricciones.md:
  - Restricciones Duras: Factibilidad (solapamientos de docentes, alumnos, aulas e idoneidad).
  - Restricciones Blandas: Función objetivo (minimización de huecos libres para alumnos).
"""

import pandas as pd
from typing import Dict, List, Tuple, Any

# Mapeo de franjas horarias estándar de la EII (turno de mañana: 08:30 a 14:30)
DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
HORAS_INICIO = ['08:30', '09:30', '10:30', '11:30', '12:30', '13:30']
HORA_A_SLOT = {hora: idx for idx, hora in enumerate(HORAS_INICIO)}
SLOT_A_HORA = {idx: hora for idx, hora in enumerate(HORAS_INICIO)}
NUM_SLOTS_DIA = len(HORAS_INICIO)  # 6 slots diarios


def cargar_datos(ruta_csv: str = 'datos_horarios.csv') -> pd.DataFrame:
    """Carga el dataset de sesiones del horario."""
    df = pd.read_csv(ruta_csv)
    return df


def obtener_slots_ocupados(hora_inicio: str, duracion: int) -> List[int]:
    """Devuelve los índices de slots que ocupa una sesión."""
    if hora_inicio not in HORA_A_SLOT:
        raise ValueError(f"Hora de inicio no válida: {hora_inicio}")
    inicio_idx = HORA_A_SLOT[hora_inicio]
    return [inicio_idx + i for i in range(duracion)]


class EvaluadorHorario:
    def __init__(self, ruta_csv: str = 'datos_horarios.csv'):
        self.ruta_csv = ruta_csv
        self.datos = cargar_datos(ruta_csv)
        self.sesiones = self.datos.to_dict(orient='records')

    def evaluar(self, horario_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Evalúa un horario completo. Si no se pasa horario_df, usa las columnas
        'dia', 'hora', 'aula' presentes en el CSV (horario oficial de referencia).
        """
        df = horario_df if horario_df is not None else self.datos.copy()

        violaciones_duras = []
        
        # 1. Validación de franja válida (no salirse de las 14:30)
        for _, row in df.iterrows():
            if pd.isna(row['dia']) or pd.isna(row['hora']) or pd.isna(row['aula']):
                violaciones_duras.append(f"Sesión {row['id_sesion']} incompleta (falta día, hora o aula).")
                continue
            
            slots = obtener_slots_ocupados(row['hora'], int(row['duracion']))
            if max(slots) >= NUM_SLOTS_DIA:
                violaciones_duras.append(
                    f"Sesión {row['id_sesion']} excede la jornada (empieza a las {row['hora']} con {row['duracion']}h)."
                )

        # 2. Idoneidad de aula (Laboratorio -> 'L...', Teoria -> 'A...')
        for _, row in df.iterrows():
            aula = str(row['aula']).strip()
            tipo = str(row['tipo']).strip().lower()
            if tipo == 'laboratorio' and not aula.startswith('L'):
                violaciones_duras.append(
                    f"Idoneidad: {row['id_sesion']} requiere Laboratorio pero está en aula {aula}."
                )
            elif tipo == 'teoria' and not aula.startswith('A'):
                violaciones_duras.append(
                    f"Idoneidad: {row['id_sesion']} requiere Aula de Teoría pero está en {aula}."
                )

        # 3. Solapamiento de Profesores
        # profesor -> (dia, slot) -> [sesiones]
        ocupacion_profesores = {}
        for _, row in df.iterrows():
            prof = row['profesor']
            dia = row['dia']
            for slot in obtener_slots_ocupados(row['hora'], int(row['duracion'])):
                clave = (prof, dia, slot)
                ocupacion_profesores.setdefault(clave, []).append(row['id_sesion'])

        for (prof, dia, slot), ses_list in ocupacion_profesores.items():
            if len(ses_list) > 1:
                violaciones_duras.append(
                    f"Solapamiento Profesor {prof} en {dia} {SLOT_A_HORA[slot]}: sesiones {ses_list}."
                )

        # 4. Solapamiento de Aulas
        # aula -> (dia, slot) -> [sesiones]
        ocupacion_aulas = {}
        for _, row in df.iterrows():
            aula = row['aula']
            dia = row['dia']
            for slot in obtener_slots_ocupados(row['hora'], int(row['duracion'])):
                clave = (aula, dia, slot)
                ocupacion_aulas.setdefault(clave, []).append(row['id_sesion'])

        for (aula, dia, slot), ses_list in ocupacion_aulas.items():
            if len(ses_list) > 1:
                violaciones_duras.append(
                    f"Solapamiento Aula {aula} en {dia} {SLOT_A_HORA[slot]}: sesiones {ses_list}."
                )

        # 5. Solapamiento de Estudiantes (Jerarquía de grupos)
        # Subgrupo 41 asiste a: 3GCID_41 y 3GCID_G1 (teoría)
        # Subgrupo 42 asiste a: 3GCID_42 y 3GCID_G1 (teoría)
        subgrupos = ['3GCID_41', '3GCID_42']
        for subgrupo in subgrupos:
            ocupacion_subgrupo = {}
            for _, row in df.iterrows():
                grupo_sesion = str(row['grupo'])
                # El subgrupo participa si la clase es de su subgrupo o de teoría general (G1)
                participa = (grupo_sesion == subgrupo) or ('G1' in grupo_sesion)
                if participa:
                    dia = row['dia']
                    for slot in obtener_slots_ocupados(row['hora'], int(row['duracion'])):
                        clave = (dia, slot)
                        ocupacion_subgrupo.setdefault(clave, []).append(row['id_sesion'])

            for (dia, slot), ses_list in ocupacion_subgrupo.items():
                if len(ses_list) > 1:
                    violaciones_duras.append(
                        f"Solapamiento Estudiantes {subgrupo} en {dia} {SLOT_A_HORA[slot]}: sesiones {ses_list}."
                    )

        # RESTRICCIONES BLANDAS (Cálculo de Huecos / Ventanas para Alumnos)
        huecos_por_subgrupo = {sg: 0 for sg in subgrupos}
        detalle_huecos = []
        dias_sobrecargados = 0

        for subgrupo in subgrupos:
            for dia in DIAS:
                slots_ocupados = set()
                for _, row in df.iterrows():
                    grupo_sesion = str(row['grupo'])
                    if ((grupo_sesion == subgrupo) or ('G1' in grupo_sesion)) and (row['dia'] == dia):
                        for s in obtener_slots_ocupados(row['hora'], int(row['duracion'])):
                            slots_ocupados.add(s)

                if len(slots_ocupados) > 0:
                    min_slot = min(slots_ocupados)
                    max_slot = max(slots_ocupados)
                    span = max_slot - min_slot + 1
                    horas_clase = len(slots_ocupados)
                    huecos = span - horas_clase
                    if huecos > 0:
                        huecos_por_subgrupo[subgrupo] += huecos
                        detalle_huecos.append(
                            f"{subgrupo} el {dia}: {huecos}h hueco libre (clase de {SLOT_A_HORA[min_slot]} a {SLOT_A_HORA[max_slot]}, {horas_clase}h lectivas)"
                        )
                    if horas_clase > 4:
                        dias_sobrecargados += 1

        total_huecos = sum(huecos_por_subgrupo.values())
        coste_total = total_huecos * 1.0 + dias_sobrecargados * 2.0

        return {
            'es_factible': len(violaciones_duras) == 0,
            'num_violaciones_duras': len(violaciones_duras),
            'violaciones_duras': violaciones_duras,
            'coste_total': coste_total,
            'total_huecos_estudiantes': total_huecos,
            'huecos_por_subgrupo': huecos_por_subgrupo,
            'detalle_huecos': detalle_huecos,
            'dias_sobrecargados': dias_sobrecargados
        }


def imprimir_informe(resultado: Dict[str, Any], titulo: str = "INFORME DE EVALUACIÓN DEL HORARIO"):
    """Imprime un resumen visual del resultado de la evaluación."""
    print("=" * 70)
    print(f" {titulo} ")
    print("=" * 70)
    
    if resultado['es_factible']:
        print(" [OK] FACTIBILIDAD: El horario es 100% FACTIBLE (0 violaciones duras).")
    else:
        print(f" [FALLO] FACTIBILIDAD: Se encontraron {resultado['num_violaciones_duras']} violaciones duras:")
        for v in resultado['violaciones_duras']:
            print(f"    - {v}")
    
    print("-" * 70)
    print(" CALIDAD Y RESTRICCIONES BLANDAS (A OPTIMIZAR):")
    print(f"  • Coste Total de la Función Objetivo : {resultado['coste_total']:.1f}")
    print(f"  • Horas totales de huecos (ventanas) : {resultado['total_huecos_estudiantes']} horas libres")
    for sg, h in resultado['huecos_por_subgrupo'].items():
        print(f"      - {sg}: {h} horas de hueco en la semana")
    
    if resultado['detalle_huecos']:
        print("  • Detalle de huecos encontrados:")
        for det in resultado['detalle_huecos']:
            print(f"      * {det}")
    else:
        print("  • No hay ningún hueco libre entre clases (horario ultra-compacto).")
        
    print(f"  • Días con sobrecarga (>4 horas de clase) : {resultado['dias_sobrecargados']}")
    print("=" * 70)


if __name__ == "__main__":
    evaluador = EvaluadorHorario('datos_horarios.csv')
    res = evaluador.evaluar()
    imprimir_informe(res, "EVALUACIÓN DEL HORARIO OFICIAL DE LA EII (3º GCID)")
