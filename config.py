from dotenv import load_dotenv
import os
from datetime import time

load_dotenv()

HORARIO_INICIO = time.fromisoformat(os.getenv("HORARIO_INICIO", "09:00"))
HORARIO_FIN = time.fromisoformat(os.getenv("HORARIO_FIN", "17:00"))
INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", "30"))

LIMITE_CANCELACIONES = int(os.getenv("LIMITE_CANCELACIONES", "5"))

ESTADO_TURNO_PENDIENTE = os.getenv("ESTADO_TURNO_PENDIENTE", "pendiente")
ESTADO_TURNO_CONFIRMADO = os.getenv("ESTADO_TURNO_CONFIRMADO", "confirmado")
ESTADO_TURNO_CANCELADO = os.getenv("ESTADO_TURNO_CANCELADO", "cancelado")
ESTADO_TURNO_ASISTIDO = os.getenv("ESTADO_TURNO_ASISTIDO", "asistido")
