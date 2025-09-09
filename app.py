from fastapi import FastAPI , Depends
from sqlalchemy.orm import Session
from database import Session as DBSession, Persona, Contacto, Turno

app = FastAPI()

# obtenemos la sesión de base de datos

get_db = DBSession()
def get_db():
    db = DBSession()  
    try:
        yield db
    finally:
        db.close()

#lo probamos con http://localhost:8000/personas en el navegador
@app.get("/personas")
def listar_personas(db: Session = Depends(get_db)):
    personas = db.query(Persona).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "edad": p.edad,
            "dni": p.dni,
            "fecha_nacimiento": str(p.fecha_nacimiento),
            "habilitado": p.habilitado
        }
        for p in personas
    ]



