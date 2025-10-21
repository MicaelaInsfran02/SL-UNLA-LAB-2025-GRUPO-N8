from typing import List
from pydantic import BaseModel
from datetime import date, time

# Entrada (POST/PUT)
class PersonaIn(BaseModel):
    nombre: str
    dni: int
    fecha_nacimiento: date
    

# Salida (GET)
class PersonaOut(BaseModel):
    id: int
    nombre: str
    dni: int
    fecha_nacimiento: date
    habilitado: bool

    class Config:
        orm_mode = True

# Entrada
class ContactoIn(BaseModel):
    email: str
    telefono: int
    direccion: str
    localidad: str
    persona_id: int

# Salida
class ContactoOut(BaseModel):
    id: int
    email: str
    telefono: int
    direccion: str
    localidad: str
    persona_id: int

    class Config:
        orm_mode = True
# Entrada
class TurnoIn(BaseModel):
    fecha: date
    hora: time
    persona_id: int
# Salida 
class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str
    persona: PersonaOut

    class Config:
        orm_mode = True

class TurnoCancelado(BaseModel):
    id: int
    fecha: str
    hora: str
    estado: str

class PersonaConCancelados(BaseModel):
    persona_id: int
    nombre: str
    dni: int
    cantidad_cancelados: int
    turnos: list[TurnoCancelado]   

class TurnoSimple(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str


class PersonaConTurnos(BaseModel):
    id: int
    nombre: str
    turnos: List[TurnoSimple]

#turno sin fecha
class TurnoSinFecha(BaseModel):
    id: int
    hora: time
    estado: str
    persona: PersonaOut

    class Config:
        orm_mode = True