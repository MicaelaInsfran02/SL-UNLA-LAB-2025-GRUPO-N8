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
    persona_id: int

    class Config:
        orm_mode = True
