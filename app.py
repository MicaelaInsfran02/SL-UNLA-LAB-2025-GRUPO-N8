from fastapi import FastAPI , Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db, Persona, Contacto, Turno
from models import PersonaIn, PersonaOut, ContactoIn, ContactoOut
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import date
from sqlalchemy.exc import SQLAlchemyError

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