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

#obtener persona por id
@app.get("/personas/{persona_id}")
def obtener_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return {
        "id": persona.id,
        "nombre": persona.nombre,
        "edad": calcular_edad(persona.fecha_nacimiento),
        "dni": persona.dni,
        "fecha_nacimiento": str(persona.fecha_nacimiento),
        "habilitado": persona.habilitado
    }

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
    #Valido que la persona exista.
    persona = db.query(Persona).filter(Persona.id == datos.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    #Valido que la fecha no sea en fechas pasadas.
    if datos.fecha < date.today():
        raise HTTPException(status_code=400, detail="No se pueden sacar turnos en fechas pasadas")

    #Valido que el horario esté dentro del rango permitido (09:00 a 17:00).
    if not (time(9, 0) <= datos.hora <= time(17, 0)):
        raise HTTPException(status_code=400, detail="Horario fuera del rango permitido (09:00–17:00)")

    #Valido que el horario esté en intervalos de 30 minutos.
    if datos.hora.minute not in [0, 30]:
        raise HTTPException(status_code=400, detail="Los turnos deben ser en intervalos de 30 minutos")

    #Valido que no exista otro turno en el mismo día y horario.
    turno_existente = db.query(Turno).filter(
        Turno.fecha == datos.fecha,
        Turno.hora == datos.hora
    ).first()

    if turno_existente:
        raise HTTPException(status_code=400, detail="Ya existe un turno en ese día y horario")

    #Valido cancelaciones en los últimos 6 meses.
    seis_meses_atras = datetime.today() - timedelta(days=180)
    cancelados = db.query(Turno).filter(
        Turno.persona_id == persona.id,
        Turno.estado == "cancelado",
        Turno.fecha >= seis_meses_atras.date()
    ).count()

    if cancelados >= 5:
        raise HTTPException(
            status_code=400,
            detail="La persona tiene 5 o más turnos cancelados en los últimos 6 meses"
        )

    #Crear el turno con estado "pendiente".
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
  
#GET fecha/horarios disponibles.
@app.get("/turnos-disponibles")
def turnos_disponibles(fecha: date, db: Session = Depends(get_db)):
    # Generar horarios posibles entre 09:00 y 17:00 en intervalos de 30 minutos
    horarios_posibles = []
    hora_actual = datetime.combine(fecha, time(9, 0))
    fin = datetime.combine(fecha, time(17, 0))

    while hora_actual <= fin:
        horarios_posibles.append(hora_actual.time())
        hora_actual += timedelta(minutes=30)

    #Obtener horarios ocupados (excepto cancelados).
    turnos_ocupados = db.query(Turno.hora).filter(
        Turno.fecha == fecha,
        Turno.estado != "cancelado"
    ).all()

    horarios_ocupados = {t.hora for t in turnos_ocupados}
    disponibles = [str(h) for h in horarios_posibles if h not in horarios_ocupados]

    return {"fecha": str(fecha), "horarios_disponibles": disponibles}
  
# DELETE turno por ID
@app.delete("/turnos/{turno_id}", status_code=status.HTTP_200_OK)
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    try:
        db.delete(turno)
        db.commit()
        return {"mensaje": f"El turno con ID {turno_id} fue eliminado correctamente."}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el turno: {str(e)}"
        )

