from dotenv import load_dotenv
import os
from datetime import time

load_dotenv()

HORARIO_INICIO = time.fromisoformat(os.getenv("HORARIO_INICIO", "09:00"))
HORARIO_FIN = time.fromisoformat(os.getenv("HORARIO_FIN", "17:00"))
INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", "30"))