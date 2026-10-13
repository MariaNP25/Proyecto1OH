import csv
import os

os.makedirs('data', exist_ok=True)

# 1. FRANJAS HORARIAS (30 slots semanales: 5 dias x 6 horas)
dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']
horas = [
    ('08:30', '09:30'),
    ('09:30', '10:30'),
    ('10:30', '11:30'),
    ('11:30', '12:30'),
    ('12:30', '13:30'),
    ('13:30', '14:30'),
]

franjas = []
franja_id = 0
for dia_idx, dia in enumerate(dias):
    for hora_idx, (h_ini, h_fin) in enumerate(horas):
        franjas.append({
            'id_franja': franja_id,
            'dia': dia,
            'dia_idx': dia_idx,
            'hora_idx': hora_idx,
            'hora_inicio': h_ini,
            'hora_fin': h_fin,
            'etiqueta': f"{dia[:3]}_{h_ini}-{h_fin}"
        })
        franja_id += 1

with open('data/franjas.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=franjas[0].keys())
    writer.writeheader()
    writer.writerows(franjas)

print(f"Creado data/franjas.csv con {len(franjas)} slots.")

# 2. ESPACIOS (AULAS Y LABORATORIOS)
espacios = [
    {'id_espacio': 'A2-5', 'tipo': 'Teoria', 'capacidad': 55, 'descripcion': 'Aula de Teoria 3º GCID'},
    {'id_espacio': 'A2-1', 'tipo': 'Teoria', 'capacidad': 60, 'descripcion': 'Aula de Teoria 1º GCID'},
    {'id_espacio': 'A3-1', 'tipo': 'Teoria', 'capacidad': 55, 'descripcion': 'Aula de Teoria 2º GCID'},
    {'id_espacio': 'A3-2', 'tipo': 'Teoria', 'capacidad': 50, 'descripcion': 'Aula de Teoria 4º GCID'},
    {'id_espacio': 'L1-1', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 1-1'},
    {'id_espacio': 'L1-2', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 1-2'},
    {'id_espacio': 'L1-3', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 1-3'},
    {'id_espacio': 'L2-1', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 2-1'},
    {'id_espacio': 'L2-2', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 2-2'},
    {'id_espacio': 'L2-3', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 2-3'},
    {'id_espacio': 'L2-4', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 2-4'},
    {'id_espacio': 'L3-1', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 3-1'},
    {'id_espacio': 'L3-2', 'tipo': 'Laboratorio', 'capacidad': 28, 'descripcion': 'Laboratorio Informática 3-2'},
]

with open('data/espacios.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=espacios[0].keys())
    writer.writeheader()
    writer.writerows(espacios)

print(f"Creado data/espacios.csv con {len(espacios)} aulas/laboratorios.")

# 3. ASIGNATURAS DE 3º GCID (1er Semestre)
asignaturas = [
    {'codigo': 'OH', 'nombre': 'Optimización y Heurística', 'curso': 3, 'semestre': 1, 'horas_teoria_semana': 2, 'horas_lab_semana': 2},
    {'codigo': 'BD', 'nombre': 'Big Data', 'curso': 3, 'semestre': 1, 'horas_teoria_semana': 2, 'horas_lab_semana': 2},
    {'codigo': 'BD2', 'nombre': 'Bases de Datos II', 'curso': 3, 'semestre': 1, 'horas_teoria_semana': 2, 'horas_lab_semana': 2},
    {'codigo': 'AA2', 'nombre': 'Aprendizaje Automático II', 'curso': 3, 'semestre': 1, 'horas_teoria_semana': 2, 'horas_lab_semana': 2},
    {'codigo': 'ASO', 'nombre': 'Administración de Sistemas Operativos', 'curso': 3, 'semestre': 1, 'horas_teoria_semana': 2, 'horas_lab_semana': 2},
]

with open('data/asignaturas.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=asignaturas[0].keys())
    writer.writeheader()
    writer.writerows(asignaturas)

print(f"Creado data/asignaturas.csv con {len(asignaturas)} asignaturas.")

# 4. PROFESORES
profesores = [
    {'id_profesor': 'P_OH', 'nombre': 'Profesorado OH', 'asignatura': 'OH'},
    {'id_profesor': 'P_BD', 'nombre': 'Profesorado BD', 'asignatura': 'BD'},
    {'id_profesor': 'P_BD2', 'nombre': 'Profesorado BD2', 'asignatura': 'BD2'},
    {'id_profesor': 'P_AA2', 'nombre': 'Profesorado AA2', 'asignatura': 'AA2'},
    {'id_profesor': 'P_ASO', 'nombre': 'Profesorado ASO', 'asignatura': 'ASO'},
]

with open('data/profesores.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=profesores[0].keys())
    writer.writeheader()
    writer.writerows(profesores)

print(f"Creado data/profesores.csv con {len(profesores)} docentes.")

# 5. SESIONES SEMANALES A PLANIFICAR (Instancia 3º GCID S1)
# Cada sesión representa una clase en bloques indivisibles (habitualmente bloques de 2 horas o de 1 hora)
sesiones = [
    # OH
    {'id_sesion': 'OH_TEO', 'asignatura': 'OH', 'tipo': 'Teoria', 'grupo': '3GCID_G1', 'profesor': 'P_OH', 'duracion': 2, 'tipo_espacio': 'Teoria'},
    {'id_sesion': 'OH_LAB_41', 'asignatura': 'OH', 'tipo': 'Laboratorio', 'grupo': '3GCID_41', 'profesor': 'P_OH', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
    {'id_sesion': 'OH_LAB_42', 'asignatura': 'OH', 'tipo': 'Laboratorio', 'grupo': '3GCID_42', 'profesor': 'P_OH', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},

    # BD
    {'id_sesion': 'BD_TEO', 'asignatura': 'BD', 'tipo': 'Teoria', 'grupo': '3GCID_G1', 'profesor': 'P_BD', 'duracion': 2, 'tipo_espacio': 'Teoria'},
    {'id_sesion': 'BD_LAB_41', 'asignatura': 'BD', 'tipo': 'Laboratorio', 'grupo': '3GCID_41', 'profesor': 'P_BD', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
    {'id_sesion': 'BD_LAB_42', 'asignatura': 'BD', 'tipo': 'Laboratorio', 'grupo': '3GCID_42', 'profesor': 'P_BD', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},

    # BD2
    {'id_sesion': 'BD2_TEO', 'asignatura': 'BD2', 'tipo': 'Teoria', 'grupo': '3GCID_G1', 'profesor': 'P_BD2', 'duracion': 2, 'tipo_espacio': 'Teoria'},
    {'id_sesion': 'BD2_LAB_41', 'asignatura': 'BD2', 'tipo': 'Laboratorio', 'grupo': '3GCID_41', 'profesor': 'P_BD2', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
    {'id_sesion': 'BD2_LAB_42', 'asignatura': 'BD2', 'tipo': 'Laboratorio', 'grupo': '3GCID_42', 'profesor': 'P_BD2', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},

    # AA2
    {'id_sesion': 'AA2_TEO', 'asignatura': 'AA2', 'tipo': 'Teoria', 'grupo': '3GCID_G1', 'profesor': 'P_AA2', 'duracion': 2, 'tipo_espacio': 'Teoria'},
    {'id_sesion': 'AA2_LAB_41', 'asignatura': 'AA2', 'tipo': 'Laboratorio', 'grupo': '3GCID_41', 'profesor': 'P_AA2', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
    {'id_sesion': 'AA2_LAB_42', 'asignatura': 'AA2', 'tipo': 'Laboratorio', 'grupo': '3GCID_42', 'profesor': 'P_AA2', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},

    # ASO
    {'id_sesion': 'ASO_TEO', 'asignatura': 'ASO', 'tipo': 'Teoria', 'grupo': '3GCID_G1', 'profesor': 'P_ASO', 'duracion': 2, 'tipo_espacio': 'Teoria'},
    {'id_sesion': 'ASO_LAB_41', 'asignatura': 'ASO', 'tipo': 'Laboratorio', 'grupo': '3GCID_41', 'profesor': 'P_ASO', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
    {'id_sesion': 'ASO_LAB_42', 'asignatura': 'ASO', 'tipo': 'Laboratorio', 'grupo': '3GCID_42', 'profesor': 'P_ASO', 'duracion': 2, 'tipo_espacio': 'Laboratorio'},
]

with open('data/sesiones_3gcid.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=sesiones[0].keys())
    writer.writeheader()
    writer.writerows(sesiones)

print(f"Creado data/sesiones_3gcid.csv con {len(sesiones)} sesiones semanales.")

# 6. HORARIO OFICIAL PUBLICADO (BASELINE DE REFERENCIA)
# Mapeo exacto del horario oficial de 3º GCID S1 del PDF
horario_oficial = [
    # Lunes
    {'id_sesion': 'OH_LAB_42', 'dia': 'Lunes', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'L1-2'},
    {'id_sesion': 'AA2_LAB_41', 'dia': 'Lunes', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'L2-2'},
    {'id_sesion': 'OH_LAB_41', 'dia': 'Lunes', 'hora_inicio': '11:30', 'duracion': 2, 'aula': 'L1-2'},

    # Martes
    {'id_sesion': 'ASO_LAB_42', 'dia': 'Martes', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'L1-1'},
    {'id_sesion': 'ASO_LAB_41', 'dia': 'Martes', 'hora_inicio': '12:30', 'duracion': 2, 'aula': 'L1-2'},

    # Miércoles
    {'id_sesion': 'BD2_TEO', 'dia': 'Miercoles', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'A2-5'},
    {'id_sesion': 'ASO_TEO', 'dia': 'Miercoles', 'hora_inicio': '10:30', 'duracion': 2, 'aula': 'A2-5'},
    {'id_sesion': 'BD_LAB_41', 'dia': 'Miercoles', 'hora_inicio': '12:30', 'duracion': 2, 'aula': 'L1-2'},
    {'id_sesion': 'BD_LAB_42', 'dia': 'Miercoles', 'hora_inicio': '12:30', 'duracion': 2, 'aula': 'L1-3'},

    # Jueves
    {'id_sesion': 'BD_TEO', 'dia': 'Jueves', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'A2-5'},
    {'id_sesion': 'AA2_TEO', 'dia': 'Jueves', 'hora_inicio': '10:30', 'duracion': 2, 'aula': 'A2-5'},
    {'id_sesion': 'OH_TEO', 'dia': 'Jueves', 'hora_inicio': '11:30', 'duracion': 2, 'aula': 'A2-5'},
    {'id_sesion': 'AA2_LAB_42', 'dia': 'Jueves', 'hora_inicio': '12:30', 'duracion': 2, 'aula': 'L2-1'},

    # Viernes
    {'id_sesion': 'BD2_LAB_41', 'dia': 'Viernes', 'hora_inicio': '08:30', 'duracion': 2, 'aula': 'L2-3'},
    {'id_sesion': 'BD2_LAB_42', 'dia': 'Viernes', 'hora_inicio': '12:30', 'duracion': 2, 'aula': 'L2-1'},
]

with open('data/horario_oficial_3gcid.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=horario_oficial[0].keys())
    writer.writeheader()
    writer.writerows(horario_oficial)

print(f"Creado data/horario_oficial_3gcid.csv con {len(horario_oficial)} asignaciones oficiales de referencia.")
