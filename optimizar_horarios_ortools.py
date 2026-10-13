"""
optimizar_horarios_ortools.py
Solucionador exacto de horarios universitarios para la EII (GCID - ULPGC) usando Google OR-Tools (CP-SAT).
Genera el horario desde cero respetando restricciones.md y minimizando los huecos libres para el alumnado.
"""

import time
import pandas as pd
from ortools.sat.python import cp_model
from evaluador import EvaluadorHorario, DIAS, HORAS_INICIO, NUM_SLOTS_DIA

# 1. INFRAESTRUCTURA DE LA ESCUELA (EII - ULPGC)
AULAS_TEORIA = ['A2-5']
AULAS_LAB = ['L1-1', 'L1-2', 'L1-3', 'L2-1', 'L2-2', 'L2-3']
TODAS_AULAS = AULAS_TEORIA + AULAS_LAB

SUBGRUPOS = ['3GCID_41', '3GCID_42']


def resolver_horario_ortools(ruta_csv: str = 'datos_horarios.csv', tiempo_limite_seg: float = 30.0):
    print("=" * 75)
    print(" OPTIMIZACIÓN DE HORARIOS DESDE CERO CON GOOGLE OR-TOOLS (CP-SAT)")
    print(" Escuela de Ingeniería Informática (EII) · Grado en Ciencia e Ingeniería de Datos")
    print("=" * 75)

    df_sesiones = pd.read_csv(ruta_csv)
    print(f"[1] Datos cargados: {len(df_sesiones)} sesiones docentes semanales a planificar.")

    model = cp_model.CpModel()

    # 2. VARIABLES DE DECISIÓN
    # x[(s_id, d, h, r)] = 1 si la sesión s empieza en el día d, hora h, en el aula r.
    x = {}
    sesiones_dict = {}

    for _, row in df_sesiones.iterrows():
        s_id = row['id_sesion']
        dur = int(row['duracion'])
        tipo = str(row['tipo']).strip().lower()
        sesiones_dict[s_id] = row

        # Aulas válidas según el tipo de sesión
        aulas_validas = AULAS_LAB if tipo == 'laboratorio' else AULAS_TEORIA

        # Horas de inicio válidas (para que no sobrepase las 14:30)
        max_inicio = NUM_SLOTS_DIA - dur

        for d in range(len(DIAS)):
            for h in range(max_inicio + 1):
                for r in aulas_validas:
                    var_name = f"x_{s_id}_{d}_{h}_{r}"
                    x[(s_id, d, h, r)] = model.NewBoolVar(var_name)

    print(f"[2] Variables de decisión generadas: {len(x)} variables booleanas.")

    # 3. RESTRICCIONES DURAS (restricciones.md)

    # R1: Cada sesión debe programarse exactamente una vez a la semana
    for s_id, row in df_sesiones.iterrows():
        s_name = row['id_sesion']
        vars_sesion = [var for (s, d, h, r), var in x.items() if s == s_name]
        model.Add(sum(vars_sesion) == 1)

    # R2: No solapamiento de Aulas
    # Un aula física r no puede albergar más de una sesión a la vez en el slot (d, t)
    for r in TODAS_AULAS:
        for d in range(len(DIAS)):
            for t in range(NUM_SLOTS_DIA):
                sesiones_en_slot = []
                for (s_id, s_d, h, s_r), var in x.items():
                    if s_r == r and s_d == d:
                        dur = int(sesiones_dict[s_id]['duracion'])
                        if h <= t < h + dur:
                            sesiones_en_slot.append(var)
                if sesiones_en_slot:
                    model.Add(sum(sesiones_en_slot) <= 1)

    # R3: No solapamiento de Profesores
    # Un profesor p no puede dar dos clases en el mismo slot (d, t)
    profesores_unicos = df_sesiones['profesor'].unique()
    for prof in profesores_unicos:
        for d in range(len(DIAS)):
            for t in range(NUM_SLOTS_DIA):
                sesiones_prof = []
                for (s_id, s_d, h, r), var in x.items():
                    if s_d == d and sesiones_dict[s_id]['profesor'] == prof:
                        dur = int(sesiones_dict[s_id]['duracion'])
                        if h <= t < h + dur:
                            sesiones_prof.append(var)
                if sesiones_prof:
                    model.Add(sum(sesiones_prof) <= 1)

    # R4: No solapamiento de Estudiantes (Jerarquía Grupo-Subgrupo)
    # Subgrupo 41 participa en sesiones de 3GCID_41 y sesiones de teoría 3GCID_G1
    # Subgrupo 42 participa en sesiones de 3GCID_42 y sesiones de teoría 3GCID_G1
    for sg in SUBGRUPOS:
        for d in range(len(DIAS)):
            for t in range(NUM_SLOTS_DIA):
                sesiones_sg = []
                for (s_id, s_d, h, r), var in x.items():
                    if s_d == d:
                        grupo_ses = str(sesiones_dict[s_id]['grupo'])
                        if (grupo_ses == sg) or ('G1' in grupo_ses):
                            dur = int(sesiones_dict[s_id]['duracion'])
                            if h <= t < h + dur:
                                sesiones_sg.append(var)
                if sesiones_sg:
                    model.Add(sum(sesiones_sg) <= 1)

    print("[3] Restricciones duras modeladas: No solape de Aulas, Profesores ni Grupos.")

    # 4. RESTRICCIONES BLANDAS / FUNCIÓN OBJETIVO (restricciones.md)
    # «Un alumno debe tener el número mínimo posible de horas libres» (Minimizar huecos)
    
    # u[(sg, d, t)] = 1 si el subgrupo sg tiene clase en el día d, slot t
    u = {}
    for sg in SUBGRUPOS:
        for d in range(len(DIAS)):
            for t in range(NUM_SLOTS_DIA):
                u[(sg, d, t)] = model.NewBoolVar(f"u_{sg}_{d}_{t}")
                sesiones_activas = []
                for (s_id, s_d, h, r), var in x.items():
                    if s_d == d:
                        grupo_ses = str(sesiones_dict[s_id]['grupo'])
                        if (grupo_ses == sg) or ('G1' in grupo_ses):
                            dur = int(sesiones_dict[s_id]['duracion'])
                            if h <= t < h + dur:
                                sesiones_activas.append(var)
                model.Add(u[(sg, d, t)] == sum(sesiones_activas))

    # Definir huecos para cada subgrupo y día:
    # Si tiene clase antes del slot t y clase después del slot t, pero u[t] == 0 => HUECO
    huecos_vars = []
    for sg in SUBGRUPOS:
        for d in range(len(DIAS)):
            for t in range(1, NUM_SLOTS_DIA - 1):
                # has_before = 1 si hay clase en algún slot t' < t
                has_before = model.NewBoolVar(f"has_before_{sg}_{d}_{t}")
                model.AddMaxEquality(has_before, [u[(sg, d, t_prev)] for t_prev in range(0, t)])

                # has_after = 1 si hay clase en algún slot t' > t
                has_after = model.NewBoolVar(f"has_after_{sg}_{d}_{t}")
                model.AddMaxEquality(has_after, [u[(sg, d, t_post)] for t_post in range(t + 1, NUM_SLOTS_DIA)])

                # gap = 1 si has_before == 1, has_after == 1 y u[t] == 0
                gap = model.NewBoolVar(f"gap_{sg}_{d}_{t}")
                model.Add(gap >= has_before + has_after - u[(sg, d, t)] - 1)
                huecos_vars.append(gap)

    # Preferencia por bloques estándar (inicios en 08:30, 10:30, 12:30 -> horas pares)
    desviacion_bloque = []
    for (s_id, d, h, r), var in x.items():
        if h % 2 != 0:  # penaliza ligeramente empezar a las 09:30, 11:30 o 13:30
            desviacion_bloque.append(var)

    # FUNCIÓN OBJETIVO: Minimizar huecos de alumnos con prioridad máxima (peso 100),
    # y modularmente mantener bloques horarios estándar (peso 1)
    coste_objetivo = 100 * sum(huecos_vars) + sum(desviacion_bloque)
    model.Minimize(coste_objetivo)

    print("[4] Función objetivo configurada: Minimizar huecos libres de los alumnos.")

    # 5. RESOLUCIÓN
    print(f"\n[5] Resolviendo con Google OR-Tools CP-SAT (límite: {tiempo_limite_seg}s)...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tiempo_limite_seg
    solver.parameters.num_search_workers = 8

    inicio_tiempo = time.time()
    status = solver.Solve(model)
    duracion_solucion = time.time() - inicio_tiempo

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        estado_str = "ÓPTIMO MATEMÁTICO" if status == cp_model.OPTIMAL else "FACTIBLE"
        print(f"\n ¡Solución encontrada con éxito en {duracion_solucion:.2f} segundos! Estado: {estado_str}")
        print(f" Valor de la función objetivo: {solver.ObjectiveValue():.0f}")

        # Reconstruir el DataFrame de la solución
        solucion_filas = []
        for (s_id, d, h, r), var in x.items():
            if solver.Value(var) == 1:
                row_orig = sesiones_dict[s_id]
                solucion_filas.append({
                    'id_sesion': s_id,
                    'curso': row_orig['curso'],
                    'asignatura': row_orig['asignatura'],
                    'tipo': row_orig['tipo'],
                    'grupo': row_orig['grupo'],
                    'profesor': row_orig['profesor'],
                    'duracion': row_orig['duracion'],
                    'dia': DIAS[d],
                    'hora': HORAS_INICIO[h],
                    'aula': r
                })

        df_sol = pd.DataFrame(solucion_filas)
        df_sol.to_csv('horario_optimizado_ortools.csv', index=False)
        print(" Horario generado guardado en: horario_optimizado_ortools.csv")

        # 6. MOSTRAR CUADRÍCULA VISUAL POR SUBGRUPO
        imprimir_cuadriculas(df_sol)

        # 7. CERTIFICAR CON EL EVALUADOR INDEPENDIENTE
        print("\n" + "=" * 75)
        print(" CERTIFICACIÓN CON EL EVALUADOR INDEPENDIENTE (evaluador.py)")
        print("=" * 75)
        evaluador = EvaluadorHorario('horario_optimizado_ortools.csv')
        res = evaluador.evaluar(df_sol)
        from evaluador import imprimir_informe
        imprimir_informe(res, "AUDITORÍA DEL HORARIO GENERADO POR OR-TOOLS")

        return df_sol
    else:
        print(" No se encontró ninguna solución factible dentro del límite de tiempo.")
        return None


def imprimir_cuadriculas(df_sol: pd.DataFrame):
    """Muestra cuadrículas horarias legibles para ambos subgrupos."""
    for sg in SUBGRUPOS:
        print("\n" + "=" * 75)
        print(f" CUADRÍCULA SEMANAL PARA EL SUBGRUPO {sg} (Generada por OR-Tools)")
        print("=" * 75)

        # Matriz: 6 franjas x 5 días
        tabla = {dia: ['---'] * NUM_SLOTS_DIA for dia in DIAS}

        for _, row in df_sol.iterrows():
            grupo_ses = str(row['grupo'])
            if (grupo_ses == sg) or ('G1' in grupo_ses):
                dia = row['dia']
                h_idx = HORAS_INICIO.index(row['hora'])
                dur = int(row['duracion'])
                etiqueta = f"{row['asignatura']} ({row['aula']})"
                for i in range(dur):
                    tabla[dia][h_idx + i] = etiqueta

        grid_df = pd.DataFrame(tabla, index=[f"{h}-{(int(h[:2])+1):02d}:30" for h in HORAS_INICIO])
        print(grid_df.to_string())


if __name__ == "__main__":
    resolver_horario_ortools()
