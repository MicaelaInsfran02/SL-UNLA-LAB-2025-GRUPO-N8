import re
from fastapi import FastAPI , Depends, HTTPException, status,Query
from sqlalchemy.orm import Session
from database import get_db, Persona, Contacto, Turno
from models import PersonaIn, PersonaOut, ContactoIn, ContactoOut, PersonaConCancelados, TurnoCancelado, TurnoIn, TurnoOut
from datetime import date, datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from utils import calcular_edad, generar_horarios_posibles, persona_limite_cancelados
from config import HORARIO_INICIO, HORARIO_FIN, INTERVALO_MINUTOS
from calendar import month_name
from sqlalchemy import extract, func
from sqlalchemy.orm import joinedload


app = FastAPI()

HORARIOS_POSIBLES = generar_horarios_posibles()



#crear una nueva persona
@app.post ("/personas", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(datos: PersonaIn, db: Session = Depends(get_db)):
    # Validar que no exista una persona con el mismo DNI
    existente = db.query(Persona).filter(Persona.dni == datos.dni).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con ese DNI")
    # Validar que la fecha de nacimiento no sea futura
    if datos.fecha_nacimiento > date.today():
        raise HTTPException(status_code=422, detail="La fecha de nacimiento no puede ser futura")

    persona = Persona(
        nombre=datos.nombre,
        dni=datos.dni,
        fecha_nacimiento=datos.fecha_nacimiento,
        habilitado=True
    )
    db.add(persona)
    try:
        db.commit()
        db.refresh(persona)
    except SQLAlchemyError as e:

        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear la persona: {str(e)}")

    return persona

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

#actualizar persona por id
@app.put("/personas/{persona_id}")
def actualizar_persona(persona_id: int, datos: PersonaIn, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    # Validar que el DNI no esté duplicado en otra persona
    dni_duplicado = db.query(Persona).filter(
    Persona.dni == datos.dni,
    Persona.id != persona_id  # excluye la persona actual
    ).first()

    if dni_duplicado:
        raise HTTPException(status_code=400, detail="Ya existe otra persona con ese DNI")

    # Validar que la fecha de nacimiento no sea futura
    if datos.fecha_nacimiento > date.today():
        raise HTTPException(status_code=422, detail="La fecha de nacimiento no puede ser futura")
    
    # actualizar los campos
    persona.nombre = datos.nombre
    persona.dni = datos.dni
    persona.fecha_nacimiento = datos.fecha_nacimiento
  
    try:
        db.commit()
        db.refresh(persona)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar la persona: {str(e)}")
    # devolver de la misma forma que listar_personas
    return {
        "id": persona.id,
        "nombre": persona.nombre,
        "edad": calcular_edad(persona.fecha_nacimiento),
        "dni": persona.dni,
        "fecha_nacimiento": str(persona.fecha_nacimiento),
        "habilitado": persona.habilitado
    }

#eliminar una persona 
@app.delete("/personas/{persona_id}", status_code=status.HTTP_200_OK)
def eliminar_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    db.delete(persona)
    db.commit()

    return {"mensaje": f"La persona con ID {persona_id} fue eliminada correctamente."}


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
    
    # Validar que no exista un contacto con el mismo email
    email_existente = db.query(Contacto).filter(Contacto.email == datos.email).first()
    if email_existente:
        raise HTTPException(status_code=400, detail="Ya existe un contacto con ese email")
    
      # Validamos formato de email 
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", datos.email):
        raise HTTPException(status_code=422, detail="Ingrese mail con formato válido")
    
    contacto= Contacto(
        email=datos.email,
        telefono=datos.telefono,
        direccion=datos.direccion,
        localidad=datos.localidad,
        persona_id=datos.persona_id
    )
    db.add(contacto)

    try:
        db.commit()
        db.refresh(contacto)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear la persona: {str(e)}")

    return contacto

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

# GET contacto por ID
@app.get("/contactos/{contacto_id}", response_model=ContactoOut)
def obtener_contacto(contacto_id: int, db: Session = Depends(get_db)):
    contacto = db.query(Contacto).filter(Contacto.id == contacto_id).first()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contacto

#actualizar un contacto
@app.put("/contactos/{contacto_id}", status_code=status.HTTP_200_OK)
def actualizar_contacto(contacto_id: int, datos: ContactoIn, db: Session = Depends(get_db)):
    contacto = db.query(Contacto).filter(Contacto.id == contacto_id).first()

    if not contacto:
        raise HTTPException(status_code=404, detail=f"No se encontró el contacto con id: {contacto_id}")

    persona = db.query(Persona).filter(Persona.id == datos.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail=f"No se encontró la persona con id: {datos.persona_id}")

    # Validar que el email no esté duplicado en otro contacto
    email_duplicado = db.query(Contacto).filter(
    Contacto.email == datos.email,
    Contacto.id != contacto_id  # excluye el contacto actual
    ).first()

    if email_duplicado:
        raise HTTPException(status_code=400, detail="Ya existe un contacto con ese email")

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", datos.email):
        raise HTTPException(status_code=422, detail="Ingrese mail con formato válido")
    
    for campo, valor in datos.dict().items():
        setattr(contacto, campo, valor)

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar el contacto: {str(e)}")

    return {"mensaje": f"Contacto con id {contacto_id} actualizado correctamente"}

#eliminar un contacto
@app.delete("/contactos/{contacto_id}", status_code=status.HTTP_200_OK)
def eliminar_contacto(contacto_id: int, db: Session = Depends(get_db)):
    contacto = db.query(Contacto).filter(Contacto.id == contacto_id).first()

    if not contacto:
        raise HTTPException(status_code=404, detail=f"No se encontró el contacto con id: {contacto_id}")

    try:
        db.delete(contacto)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al eliminar el contacto: {str(e)}")

    return {"mensaje": f"Contacto con id {contacto_id} eliminado correctamente"}



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
    if not (HORARIO_INICIO <= datos.hora <= HORARIO_FIN):
        raise HTTPException(status_code=400, detail="Horario fuera del rango permitido (09:00-17:00)")

    #Valido que el horario esté en intervalos de 30 minutos.
    if datos.hora.minute % INTERVALO_MINUTOS != 0:
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
    turnos_ocupados = db.query(Turno.hora).filter(
        Turno.fecha == fecha,
        Turno.estado != "cancelado"
    ).all()

    horarios_ocupados = {t.hora for t in turnos_ocupados}
    disponibles = [str(h) for h in HORARIOS_POSIBLES if h not in horarios_ocupados]

    return {"fecha": str(fecha), "horarios_disponibles": disponibles}
  
# actualizar turno por id PUT /turnos/{turno_id}
@app.put("/turnos/{turno_id}")
def actualizar_turno(turno_id: int, datos: TurnoIn, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    # no permitir cambios si ya está cancelado o asistido
    if turno.estado in ("cancelado", "asistido"):
        raise HTTPException(status_code=400, detail="No se puede modificar un turno cancelado o asistido")

    # validar que la persona indicada exista
    persona = db.query(Persona).filter(Persona.id == datos.persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    # Validar rango horario (09:00 - 17:00)
    if not (HORARIO_INICIO <= datos.hora <= HORARIO_FIN):
        raise HTTPException(status_code=400, detail="Horario fuera del rango permitido (09:00-17:00)")

    # Validar intervalos de 30 minutos
    if datos.hora.minute % INTERVALO_MINUTOS != 0:
        raise HTTPException(status_code=400, detail="Los turnos deben ser en intervalos de 30 minutos")

    # Buscar otro turno en la misma fecha/hora que no sea 'cancelado' y que no sea este turno para evitar un solapamiento
    conflicto = db.query(Turno).filter(
        Turno.fecha == datos.fecha,
        Turno.hora == datos.hora,
        Turno.id != turno.id,
        Turno.estado != "cancelado"
    ).first()

    if conflicto:
        raise HTTPException(status_code=400, detail="El horario solicitado está ocupado por otro turno")

    # Aplicar cambios
    turno.fecha = datos.fecha
    turno.hora = datos.hora
    turno.persona_id = datos.persona_id

    try:
        db.commit()
        db.refresh(turno)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar el turno: {str(e)}")

    return {
        "id": turno.id,
        "fecha": str(turno.fecha),
        "hora": str(turno.hora),
        "estado": turno.estado,
        "persona_id": turno.persona_id
    }

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


# Gestion de estado de turno
@app.put("/turnos/{id}/confirmar")
def confirmar_turno(id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado in ["cancelado", "asistido"]:
        raise HTTPException(status_code=400, detail="No se puede confirmar un turno cancelado o asistido")

    turno.estado = "confirmado"
    db.commit()
    db.refresh(turno)  
    return {
        "mensaje": "Turno confirmado correctamente",
        "turno": {
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado,
            "persona_id": turno.persona_id
        }
    }

#Endpoints de reportes

@app.get("/reportes/turnos-por-fecha", response_model=list[TurnoOut])
def obtener_turnos_por_fecha(
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db) ):
    #convertimos la fecha de string a date, si el formato es incorrecto, lanza un error
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    
    #consultamos los turnos en esa fecha en la base de datos
    turnos = db.query(Turno).filter(Turno.fecha == fecha_obj).all()
    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos reservados para esa fecha.")

    return turnos

@app.get("/reportes/turnos-por-persona/{persona_id}", response_model=list[TurnoOut])
def obtener_turnos_por_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first() #.firts() devuelve la primera coincidencia o None)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    #buscamos turnos asociados a esa persona (dato: .all() devuelve una lista con los resultados
    turnos = db.query(Turno).filter(Turno.persona_id == persona_id).all()
    if not turnos:
        raise HTTPException(status_code=404, detail="La persona no tiene turnos asignados")

    return turnos

#GET reportes: turnos cancelados en el mes actual.

@app.get("/reportes/turnos-cancelados-mes-actual")
def turnos_cancelados_mes_actual(db: Session = Depends(get_db)):
    hoy = date.today()
    turnos = db.query(Turno).filter(
        Turno.estado == "cancelado",
        extract("month", Turno.fecha) == hoy.month,
        extract("year", Turno.fecha) == hoy.year
    ).all()

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos cancelados en el mes actual")

    informe_cancelados = {
        "anio": hoy.year,
        "mes": month_name[hoy.month].lower(),
        "cantidad": len(turnos),
        "turnos": [
            {
                "id": t.id,
                "persona_id": t.persona_id,
                "fecha": str(t.fecha),
                "hora": t.hora.strftime("%H:%M"),
                "estado": t.estado
            }
            for t in turnos
        ]
    }

    return informe_cancelados

#GET reportes: Personas con 5 turnos cancelados como mínimo

@app.get("/reportes/personas-con-muchos-turnos-cancelados", response_model=list[PersonaConCancelados])
def personas_con_muchos_turnos_cancelados(db: Session = Depends(get_db)):
    consulta = persona_limite_cancelados(db)

    personas = db.query(Persona).join(
        consulta, Persona.id == consulta.c.persona_id
    ).all()

    resultado = []
    for persona in personas:
        turnos_cancelados = db.query(Turno).filter(
            Turno.persona_id == persona.id,
            Turno.estado == "cancelado"
        ).all()

        resultado.append(PersonaConCancelados(
            persona_id=persona.id,
            nombre=persona.nombre,
            dni=persona.dni,
            cantidad_cancelados=len(turnos_cancelados),
            turnos=[
                TurnoCancelado(
                    id=t.id,
                    fecha=str(t.fecha),
                    hora=t.hora.strftime("%H:%M"),
                    estado=t.estado
                ) for t in turnos_cancelados
            ]
        ))

    if not resultado:
        raise HTTPException(status_code=404, detail="No hay personas con más de 5 turnos cancelados")

    return resultado

# GET reportes: turnos confirmados en un período (máx 5 resultados)
@app.get("/reportes/turnos-confirmados", response_model=list[TurnoOut])
def turnos_confirmados_en_periodo(  # define la función manejadora del endpoint; FastAPI la invoca cuando llega la request
    desde: str = Query(..., description="Fecha desde (YYYY-MM-DD)"),   # 'desde' es un query param OBLIGATORIO (... lo vuelve requerido) y se convierte a str
    hasta: str = Query(..., description="Fecha hasta (YYYY-MM-DD)"),   # 'hasta' es un query param OBLIGATORIO (... lo vuelve requerido) y se convierte a str
    db: Session = Depends(get_db)                                      # inyección de dependencia: crea/provee una Session de SQLAlchemy a través de get_db()
): 

    # parseo y validación de fechas
    try:
        desde_date = datetime.strptime(desde, "%Y-%m-%d").date()   # 'desde' -> date
        hasta_date = datetime.strptime(hasta, "%Y-%m-%d").date()   # 'hasta' -> date
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    if desde_date > hasta_date:
        raise HTTPException(status_code=400, detail="'desde' no puede ser mayor que 'hasta'.")

    # consulta: confirmados dentro del rango, ordenados ascendente, y limitar a 5
    turnos = (
        db.query(Turno)                                           # Query sobre Turno
        .filter(
            Turno.estado == "confirmado",                         # estado confirmado
            Turno.fecha >= desde_date,                            # fecha >= desde
            Turno.fecha <= hasta_date                             # fecha <= hasta
        )
        .order_by(Turno.fecha.asc(), Turno.hora.asc())            # orden por fecha/hora
        .limit(5)                                                 # devolver sólo 5
        .all()                                                    # ejecutar
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos confirmados en el período indicado.")

    return turnos                                                # devuelve lista de Turno (Pydantic la serializa)


# GET reportes: personas habilitadas o inhabilitadas para sacar turno
@app.get("/reportes/estado-personas")  # define la ruta y método HTTP
def reporte_estado_personas(
    habilitada: bool = Query(..., description="true para habilitadas, false para inhabilitadas"),  # query param booleano
    db: Session = Depends(get_db)                                                                   # sesión de base
):
    personas = db.query(Persona).filter(Persona.habilitado == habilitada).all()  # filtra por estado 'habilitado'

    if not personas:
        estado_txt = "habilitadas" if habilitada else "inhabilitadas"            # arma texto para el mensaje
        raise HTTPException(status_code=404, detail=f"No hay personas {estado_txt} para sacar turno.")  # sin resultados

    # mismo formato que /personas
    return [
        {
            "id": p.id,                                         # id de la persona
            "nombre": p.nombre,                                 # nombre
            "edad": calcular_edad(p.fecha_nacimiento),          # edad calculada
            "dni": p.dni,                                       # dni
            "fecha_nacimiento": str(p.fecha_nacimiento),        # fecha de nacimiento como string
            "habilitado": p.habilitado                          # estado de habilitación
        }
        for p in personas                                       # itera sobre todas las personas filtradas
    ]

