from fastapi import FastAPI , Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db, Persona, Contacto, Turno
from models import PersonaIn, PersonaOut, ContactoIn, ContactoOut
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import date
from sqlalchemy.exc import SQLAlchemyError
from models import TurnoIn, TurnoOut
from datetime import datetime, timedelta
from sqlalchemy import and_



app = FastAPI()

#lo probamos con http://localhost:8000/personas en el navegador
#obtener todas las personas
@app.get("/personas")
def listar_personas(db: Session = Depends(get_db)):
    personas = db.query(Persona).all()

    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "edad": calcular_edad(p.fecha_nacimiento),
            "dni": p.dni,
            "fecha_nacimiento": str(p.fecha_nacimiento),
            "habilitado": p.habilitado
        }
        for p in personas
    ]

#obtener todos los contactos
@app.get("/contactos")
def listar_contactos(db: Session = Depends(get_db)):
    contactos = db.query(Contacto).all()
    return [
        {
            "id": c.id,
            "email": c.email,
            "telefono": c.telefono,
            "direccion": c.direccion,
            "localidad": c.localidad,
            "persona_id": c.persona_id
        }
        for c in contactos
    ]

#crear una nueva persona
@app.post ("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(datos: PersonaIn, db: Session = Depends(get_db)):
    # Validar que no exista una persona con el mismo DNI
    existente = db.query(Persona).filter(Persona.dni == datos.dni).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con ese DNI")

    persona = Persona(**datos.dict())  # convierte el modelo Pydantic en kwargs
    db.add(persona)
    try:
        db.commit()
        db.refresh(persona)
    except SQLAlchemyError as e:

        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear la persona: {str(e)}")

    return persona

#crear un nuevo contacto
@app.post("/contactos", response_model=ContactoOut, status_code=status.HTTP_201_CREATED)
def crear_contacto(datos: ContactoIn, db: Session = Depends(get_db)):
    # Validamos que la persona con ese id exista
    persona = db.query(Persona).filter(Persona.id == datos.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="No se encontro la persona con id: {}".format(datos.persona_id))

    # Validamos que no tenga un contacto asignado
    if persona.contacto:
        raise HTTPException(status_code=400, detail="La persona ya tiene un contacto asignado")

    contacto = Contacto(**datos.dict())
    db.add(contacto)

    try:
        db.commit()
        db.refresh(contacto)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear la persona: {str(e)}")

    return contacto

#eliminar una persona 
@app.delete("/personas/{persona_id}", status_code=status.HTTP_200_OK)
def eliminar_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    db.delete(persona)
    db.commit()

    return {"mensaje": f"La persona con ID {persona_id} fue eliminada correctamente."}

#capturamos error de mail y lanzamos mensaje personalizado
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = exc.errors()
    mensajes = []

    for error in errores:
        loc = error.get("loc", [])
        msg = error.get("msg", "")
        if "email" in loc:
            mensajes.append("El email ingresado no tiene un formato válido.")
        else:
            mensajes.append(msg)

    return JSONResponse(
        status_code=422,
        content={"detail": mensajes}
    )


#función calcular edad
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        #Esto devuelve  (que equivale a ) si todavía no cumplió años este año, y  () si ya los cumplió.
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

#POST turnos.
@app.post("/turnos", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(datos: TurnoIn, db: Session = Depends(get_db)):
    # validamos que la persona exista
    persona = db.query(Persona).filter(Persona.id == datos.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    #calculo fecha limite ultimos 6 meses.
    seis_meses_atras = datetime.today() - timedelta(days=180)

    #contador de turnos cancelados en ese período de 6 meses / utilizando and_ de sqlalchemy para que cuente cuando todas las condiciones se cumplan.
    cancelados = db.query(Turno).filter(
        and_(
            Turno.persona_id == persona.id,
            Turno.estado == "cancelado",
            Turno.fecha >= seis_meses_atras.date()
        )
    ).count()

    if cancelados >= 5:
        raise HTTPException(
            status_code=400,
            detail="La persona tiene 5 o más turnos cancelados en los últimos 6 meses"
        )

    # Crear el turno con estado pendiente
    nuevo_turno = Turno(
        fecha=datos.fecha,
        hora=datos.hora,
        estado="pendiente",
        persona_id=persona.id
    )

    db.add(nuevo_turno)
    try:
        db.commit()
        db.refresh(nuevo_turno)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el turno: {str(e)}")

    return nuevo_turno

#GET listar todos los turnos.
@app.get("/turnos", response_model=list[TurnoOut])
def listar_turnos(db: Session = Depends(get_db)):
    turnos = db.query(Turno).all()
    return turnos
#GET turnos por id.
@app.get("/turnos/{turno_id}", response_model=TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return turno