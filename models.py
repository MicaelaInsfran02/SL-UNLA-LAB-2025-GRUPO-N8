from pydantic import BaseModel, EmailStr
from datetime import date

# Entrada (POST/PUT)
class PersonaIn(BaseModel):
    nombre: str
    dni: int
    fecha_nacimiento: date
    habilitado: bool 

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
    email: EmailStr  #valida que el mail tenga un formato valido ;)
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
    hora: int
    estado: str

# Salida
class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: int
    estado: str

    class Config:
        orm_mode = True