from datetime import datetime,date, timedelta
from sqlalchemy import or_, func
from config import HORARIO_INICIO, HORARIO_FIN, INTERVALO_MINUTOS
from sqlalchemy.orm import Session
from database import Turno

#función calcular edad
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

#Generar horarios disponibles, rango (9-17), intervalo de 30 min.
def generar_horarios_posibles():
    inicio = HORARIO_INICIO
    fin = HORARIO_FIN
    intervalo = INTERVALO_MINUTOS
    horarios = []
    hora_actual = datetime.combine(date.today(), inicio)
    limite = datetime.combine(date.today(), fin)

    while hora_actual <= limite:
        horarios.append(hora_actual.time())
        hora_actual += timedelta(minutes=intervalo)

    return horarios

#Personas con un minimo 5 turnos cancelados.

def persona_limite_cancelados(db: Session):
    return db.query(
        Turno.persona_id,
        func.count(Turno.id).label("cancelados")
    ).filter(
        Turno.estado == "cancelado"
    ).group_by(
        Turno.persona_id
    ).having(
        func.count(Turno.id) >= 5
    ).subquery()



