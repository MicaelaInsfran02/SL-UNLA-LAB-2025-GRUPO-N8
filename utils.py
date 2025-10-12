from datetime import datetime,date, time, timedelta

#función calcular edad
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

#Generar horarios disponibles, rango (9-17), intervalo de 30 min.
def generar_horarios_posibles():
    inicio = time(9, 0)
    fin = time(17, 0)
    horarios = []
    hora_actual = datetime.combine(date.today(), inicio)
    limite = datetime.combine(date.today(), fin)

    while hora_actual <= limite:
        horarios.append(hora_actual.time())
        hora_actual += timedelta(minutes=30)

    return horarios