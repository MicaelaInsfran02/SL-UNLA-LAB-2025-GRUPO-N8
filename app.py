import re
from fastapi import FastAPI , Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from database import get_db, Persona, Contacto, Turno
from models import PersonaIn, PersonaOut, ContactoIn, ContactoOut, PersonaConCancelados, TurnoCancelado, TurnoIn, TurnoOut, PersonaConTurnos, TurnoSinFecha, PersonaConTurnos, TurnoSinFecha, UsuarioConfirmado, TurnosConfirmadosPorDia
from datetime import date, datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from utils import calcular_edad, generar_horarios_posibles, persona_limite_cancelados, generar_csv, turnos_to_dict, pdf_response
from config import HORARIO_INICIO, HORARIO_FIN, INTERVALO_MINUTOS, LIMITE_CANCELACIONES, ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO, ESTADO_TURNO_CONFIRMADO, ESTADO_TURNO_PENDIENTE
from calendar import month_name
from sqlalchemy import extract, func, and_
from math import ceil
from fastapi import Query
from sqlalchemy import func
import pandas as pd
from fastapi.responses import StreamingResponse



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

     #Valido cancelaciones en los últimos 6 meses.
    seis_meses_atras = datetime.today() - timedelta(days=180)
    cancelados = db.query(Turno).filter(
        Turno.persona_id == persona.id,
        Turno.estado == ESTADO_TURNO_CANCELADO, 
        Turno.fecha >= seis_meses_atras.date()
    ).count()

    if cancelados >= LIMITE_CANCELACIONES:
        persona.habilitado = False
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="La persona no puede sacar turnos: tiene {LIMITE_CANCELACIONES} o más cancelaciones en los últimos 6 meses"
    )

    
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

   

    #Crear el turno con estado "pendiente".
    nuevo_turno = Turno(
        fecha=datos.fecha,
        hora=datos.hora,
        estado=ESTADO_TURNO_PENDIENTE,
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
        Turno.estado != ESTADO_TURNO_CANCELADO
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
    if turno.estado in (ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO):
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
        Turno.estado != ESTADO_TURNO_CANCELADO
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
#confirmar turno
@app.put("/turnos/{id}/confirmar")
def confirmar_turno(id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado in [ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO]:
        raise HTTPException(status_code=400, detail="No se puede confirmar un turno cancelado o asistido")

    turno.estado = ESTADO_TURNO_CONFIRMADO
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

#cancelar turno
@app.put("/turnos/{id}/cancelar")
def cancelar_turno(id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado in [ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO]:
        raise HTTPException(status_code=400, detail="No se puede cancelado un turno cancelado o asistido")

    turno.estado = ESTADO_TURNO_CANCELADO
    db.commit()
    db.refresh(turno)  
    return {
        "mensaje": "Turno cancelado correctamente",
        "turno": {
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado,
            "persona_id": turno.persona_id
        }
    }

#asistir turno
@app.put("/turnos/{id}/asistido")
def asistir_turno(id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado in [ESTADO_TURNO_CANCELADO]:
        raise HTTPException(status_code=400, detail="No se puede pasar al estado asistido un turno cancelado")

    turno.estado = ESTADO_TURNO_ASISTIDO
    db.commit()
    db.refresh(turno)  
    return {
        "mensaje": "Turno marcado como asistido correctamente",
        "turno": {
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado,
            "persona_id": turno.persona_id
        }
    }

#Endpoints de reportes

@app.get("/reportes/turnos-por-fecha",response_model=list[PersonaConTurnos])
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

    resultado = []
    personas_dict = {}

    for turno in turnos:
        persona = turno.persona
        if persona.id not in personas_dict:
            personas_dict[persona.id] = {
                "id": persona.id,
                "nombre": persona.nombre,
                "turnos": []
            }
        personas_dict[persona.id]["turnos"].append({
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado
        })

    for datos in personas_dict.values():
        # Convertimos el diccionario en un objeto Pydantic usando el constructor con desempaquetado (**datos)
        resultado.append(PersonaConTurnos(**datos))

    return resultado


@app.get("/reportes/turnos-por-persona/{dni}", response_model=PersonaConTurnos)
def obtener_turnos_por_persona(dni: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.dni == dni).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    turnos = db.query(Turno).filter(Turno.persona_id == persona.id).all()

    return {
        "id": persona.id,
        "nombre": persona.nombre,
        "turnos": [
            {
                "id": turno.id,
                "fecha": turno.fecha,
                "hora": turno.hora,
                "estado": turno.estado
            } for turno in turnos
        ]
    }


#GET reportes: turnos cancelados en el mes actual.

@app.get("/reportes/turnos-cancelados-mes-actual")
def turnos_cancelados_mes_actual(db: Session = Depends(get_db)):
    hoy = date.today()
    turnos = db.query(Turno).filter(
        Turno.estado == ESTADO_TURNO_CANCELADO,
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
            Turno.estado == ESTADO_TURNO_CANCELADO
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
        raise HTTPException(status_code=404, detail="No hay personas con más de {LIMITE_CANCELACIONES} turnos cancelados")

    return resultado

# GET reportes: turnos confirmados en un período con paginación
@app.get("/reportes/turnos-confirmados", response_model=list[TurnosConfirmadosPorDia])  
def turnos_confirmados_en_periodo(
    desde: date = Query(..., description="Fecha desde (YYYY-MM-DD)"),  # Query param obligatorio: fecha inicio 
    hasta: date = Query(..., description="Fecha hasta (YYYY-MM-DD)"),  # Query param obligatorio: fecha fin 
    page: int = Query(1, ge=1, description="Página (>=1)"),            # Query param opcional: número de página (>=1)
    db: Session = Depends(get_db),                                     # Inyección de la sesión de base de datos
):
    if desde > hasta:  # Validación de rango de fechas
        raise HTTPException(status_code=400, detail="'desde' no puede ser mayor que 'hasta'.")

    FECHAS_POR_PAGINA = 5  # Cantidad de FECHAS distintas por página

    # 1) Calcula cuántos DÍAS distintos tienen al menos un turno en estado "confirmado" dentro del rango [desde, hasta].
    total_fechas = (
        db.query(func.count(func.distinct(Turno.fecha)))               # COUNT(DISTINCT fecha)
          .filter(
              Turno.estado == ESTADO_TURNO_CONFIRMADO,                            # Solo turnos confirmados
              Turno.fecha >= desde,                                    # Dentro del rango (desde)
              Turno.fecha <= hasta,                                    # Dentro del rango (hasta)
          )
          .scalar()                                                    # Ejecuta y obtiene escalar
    ) or 0                                                             # Si None, usar 0

    if total_fechas == 0:  # Si no hay fechas con confirmados en el período
        raise HTTPException(status_code=404, detail="No hay turnos confirmados en el período indicado.")

    total_paginas = ceil(total_fechas / FECHAS_POR_PAGINA)  # Total de páginas de FECHAS
    if page > total_paginas:  # Si la página pedida no existe
        raise HTTPException(status_code=404, detail=f"Página fuera de rango. total de paginas={total_paginas}")

    # 2) Obtiene las FECHAS que corresponden a la página actual: selecciona únicamente Turno.fecha, filtra por estado y rango,
    fechas_pagina = [
        fila[0]                                                        # Extraemos la columna fecha de la fila
        for fila in (
            db.query(Turno.fecha)                                     # Seleccionamos la fecha
              .filter(
                  Turno.estado == ESTADO_TURNO_CONFIRMADO,                       # Solo confirmados
                  Turno.fecha >= desde,                               # Rango desde
                  Turno.fecha <= hasta,                               # Rango hasta
              )
              .group_by(Turno.fecha)                                  # Distintas fechas (GROUP BY)
              .order_by(Turno.fecha.asc())                            # Orden cronológico
              .offset((page - 1) * FECHAS_POR_PAGINA)                    # Desplazamiento por página
              .limit(FECHAS_POR_PAGINA)                                  # Límite de 5 FECHAS
              .all()                                                  # Ejecuta
        )
    ]                                                                  # Resultado: lista de fechas para esta página

    # 3) Construye una subconsulta que deduplica por (persona_id, fecha) eligiendo la hora mínima del día (primer turno confirmado).
    dedup = (
        db.query(
            Turno.persona_id.label("persona_id"),                      # Persona
            Turno.fecha.label("fecha"),                                # Fecha
            func.min(Turno.hora).label("hora_min"),                    # Hora mínima (primer turno confirmado del día)
        )
        .filter(
            Turno.estado == ESTADO_TURNO_CONFIRMADO,                   # Solo confirmados
            Turno.fecha.in_(fechas_pagina),                            # Solo las fechas de esta página
        )
        .group_by(Turno.persona_id, Turno.fecha)                       # Dedup por persona/fecha
        .subquery()                                                    # Subconsulta para hacer el join
    )

    # 4)  Reagrupa los turnos obtenidos por fecha siguiendo exactamente el orden de 'fechas_pagina' y construye la salida final.
    filas = (
        db.query(Turno)
          .options(joinedload(Turno.persona))                          # Eager load de persona (evita N+1)
          .join(
              dedup,
              and_(
                  Turno.persona_id == dedup.c.persona_id,              # Match persona
                  Turno.fecha == dedup.c.fecha,                        # Match fecha
                  Turno.hora == dedup.c.hora_min,                      # Match hora mínima de ese día
              )
          )
          .order_by(Turno.fecha.asc(), Turno.hora.asc(), Turno.id.asc())  # Orden consistente por día/hora/id
          .all()                                                       # Ejecuta y obtiene los turnos concretos
    )

    # 5) Agrupar por fecha (en el mismo orden de 'fechas_pagina')
    por_fecha = {f: [] for f in fechas_pagina}                         # Inicializa dict con claves = fechas de la página
    for t in filas:                                                     # Recorre turnos deduplicados
        por_fecha[t.fecha].append({                                    # Agrega el usuario confirmado a la fecha correspondiente
            "turno_id": t.id,                                          # ID del turno elegido (hora más temprana)
            "hora": t.hora,                                            # Hora del turno
            "persona": {                                               # Datos de la persona (alineado a PersonaOut)
                "id": t.persona.id,
                "nombre": t.persona.nombre,
                "dni": t.persona.dni,
                "fecha_nacimiento": t.persona.fecha_nacimiento,
                "habilitado": t.persona.habilitado,
            }
        })

    return [{"fecha": f, "usuarios": por_fecha[f]} for f in fechas_pagina]  # Devuelve lista ordenada de {fecha, usuarios}


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

# GET reportes: personas habilitadas o inhabilitadas en CSV --------------------------
@app.get("/reportes/csv/estado-personas")
def descargar_csv_estado_personas(
    # query param obligatorio: true para habilitadas, false para inhabilitadas
    habilitada: bool = Query(..., description="true para habilitadas, false para inhabilitadas"),
    # inyección de la sesión de base de datos
    db: Session = Depends(get_db)
):
    # Buscar en la base todas las personas con el estado pedido (habilitada / inhabilitada)
    personas = db.query(Persona).filter(Persona.habilitado == habilitada).all()

    # Si no se encontró ninguna persona con ese estado, devolvemos 404
    if not personas:
        estado_txt = "habilitadas" if habilitada else "inhabilitadas"
        raise HTTPException(
            status_code=404,
            detail=f"No hay personas {estado_txt} para sacar turno."
        )

    # Convertimos la lista de objetos Persona en una lista de diccionarios
    # Cada diccionario va a ser una fila del CSV
    datos = []
    for p in personas:
        datos.append(
            {
                "id": p.id,                                # id de la persona
                "nombre": p.nombre,                        # nombre completo
                "dni": p.dni,                              # documento
                "fecha_nacimiento": str(p.fecha_nacimiento),  # fecha de nacimiento (string)
                "edad": calcular_edad(p.fecha_nacimiento), # edad calculada
                "habilitado": p.habilitado                 # True / False
            }
        )

    # Armamos título y nombre de archivo según el estado
    if habilitada:
        titulo = "Personas habilitadas para sacar turno"
        nombre_archivo = "personas_habilitadas"
    else:
        titulo = "Personas inhabilitadas para sacar turno"
        nombre_archivo = "personas_inhabilitadas"

    # Generar el CSV en memoria usando la función utilitaria generar_csv
    csv_buffer = generar_csv(datos, titulo=titulo)

    # Devolver el CSV como archivo descargable (sin guardarlo en disco)
    return StreamingResponse(
        csv_buffer,                   # buffer en memoria con el CSV
        media_type="text/csv",        # tipo de contenido CSV
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}.csv"
        }
    )


# GET reportes: personas habilitadas o inhabilitadas para sacar turno (PDF) --------------------------
@app.get("/reportes/pdf/estado-personas")
def descargar_pdf_estado_personas(
    # query param obligatorio: true para habilitadas, false para inhabilitadas
    habilitada: bool = Query(..., description="true para habilitadas, false para inhabilitadas"),
    # inyección de la sesión de base de datos
    db: Session = Depends(get_db)
):
    # Buscar en la base todas las personas con el estado pedido (habilitada / inhabilitada)
    personas = db.query(Persona).filter(Persona.habilitado == habilitada).all()

    # Si no se encontró ninguna persona con ese estado, devolvemos 404
    if not personas:
        estado_txt = "habilitadas" if habilitada else "inhabilitadas"
        raise HTTPException(
            status_code=404,
            detail=f"No hay personas {estado_txt} para sacar turno."
        )

    # Convertimos la lista de objetos Persona en una lista de diccionarios
    # Cada diccionario representa una fila de la tabla del PDF
    datos = []
    for p in personas:
        datos.append(
            {
                "id": p.id,                                # id de la persona
                "nombre": p.nombre,                        # nombre completo
                "dni": p.dni,                              # documento
                "fecha_nacimiento": str(p.fecha_nacimiento),  # fecha de nacimiento (como string)
                "edad": calcular_edad(p.fecha_nacimiento), # edad calculada con la función utils.calcular_edad
                "habilitado": p.habilitado                 # True / False
            }
        )

    # Armamos el título del reporte según el estado
    if habilitada:
        titulo = "Personas habilitadas para sacar turno"
        nombre_archivo = "personas_habilitadas"
    else:
        titulo = "Personas inhabilitadas para sacar turno"
        nombre_archivo = "personas_inhabilitadas"

    # Generamos y devolvemos el PDF usando la función utilitaria pdf_response
    return pdf_response(datos, titulo, nombre_archivo)


#GET reportes: turnos cancelados por mes en PDF con paginación --------------------------
@app.get("/reportes/pdf/turnos-cancelados-por-mes")
def descargar_pdf_turnos_cancelados_por_mes(
    anio: int = Query(..., description="Año en formato AAAA"), #parametro obligatorio
    mes: int = Query(..., ge=1, le=12, description="Mes en formato 1-12"), #parametro obligatorio
    pagina: int = Query(1, ge=1, description="Número de página (>=1)"), #número de página, mínimo 1, empezando desde la 1.
    pagina_limite: int = Query(20, ge=1, le=20, description="Cantidad de registros por página"), #cantidad de registros por página, mínimo 1 y máximo 20.
    db: Session = Depends(get_db)
):
    # Calcular desde qué registro empezar
    inicio = (pagina - 1) * pagina_limite

    # Consulta ORM con paginación
    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.persona))
        .filter(Turno.estado == "cancelado")
        .filter(extract("year", Turno.fecha) == anio)
        .filter(extract("month", Turno.fecha) == mes)
        .order_by(Turno.fecha.asc(), Turno.hora.asc(), Turno.id.asc()) # ordena por fecha, hora e id
        .offset(inicio) # indica desde qué registro empezar
        .limit(pagina_limite) # limita la cantidad de registros traídos
        .all() # ejecuta la consulta
    )

    # En caso de que no haya turnos cancelados en esa página
    if not turnos:
        raise HTTPException( status_code=404,  detail=f"No hay turnos cancelados para {anio}-{mes:02d} en la página {pagina}" )

    # Transformar ORM a diccionario
    datos = turnos_to_dict(turnos)

    # Generar PDF y devolver respuesta
    return pdf_response(
        datos, f"Turnos cancelados - {anio}-{mes:02d} (página {pagina})", f"turnos_cancelados_{anio}_{mes:02d}_p{pagina}")



#GET reportes: turnos por fecha en PDF con paginación --------------------------
@app.get("/reportes/pdf/turnos-por-fecha")
def descargar_pdf_turnos_por_fecha(
    fecha: date = Query(..., description="Fecha en formato AAAA-MM-DD"), #parametro obligatorio
    pagina: int = Query(1, ge=1, description="Número de página (>=1)"), #número de página, mínimo 1, empezando desde la 1.
    pagina_limite: int = Query(20, ge=1, le=20, description="Cantidad de registros por página"), #cantidad de registros por página, mínimo 1 y máximo 20.
    db: Session = Depends(get_db) #inyección de la sesión de base de datos
):
    
    inicio = (pagina - 1) * pagina_limite  #  indica desde qué registro empezar.- cuántos registros se deben saltar antes de empezar a traer los de la página actual.


    # Consulta ORM con paginación
    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.persona))
        .filter(Turno.fecha == fecha)
        .order_by(Turno.hora.asc(), Turno.id.asc())
        .offset(inicio) # indica desde qué registro empezar
        .limit(pagina_limite) # limita la cantidad de registros traídos
        .all() # ejecuta la consulta
    )
    # En caso de que no haya turnos en esa página
    if not turnos:
        raise HTTPException(status_code=404,detail=f"No hay turnos para la fecha {fecha} en la página {pagina}")

    datos = turnos_to_dict(turnos)     # Transformar ORM a diccionario

    # Generar PDF y devolver respuesta
    return pdf_response(datos, f"Turnos del día {fecha} (página {pagina})", f"turnos_{fecha}_p{pagina}"
    )

@app.get("/reportes/csv/turnos-por-fecha")
def descargar_csv_turnos_por_fecha(
    fecha: date = Query(..., description="Fecha en formato AAAA-MM-DD"),
    pagina: int = Query(1, ge=1, description="Número de página (>=1)"),
    pagina_limite: int = Query(20, ge=1, le=20, description="Cantidad de registros por página"),
    db: Session = Depends(get_db)
):
    # Calcular desde qué registro empezar
    inicio = (pagina - 1) * pagina_limite

    # Consulta ORM con paginación
    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.persona))
        .filter(Turno.fecha == fecha)
        .order_by(Turno.hora.asc(), Turno.id.asc())
        .offset(inicio)
        .limit(pagina_limite)
        .all()
    )

    if not turnos:
        raise HTTPException(
            status_code=404, detail=f"No hay turnos para la fecha {fecha} en la página {pagina}" )

    # Transformar ORM → dict
    datos = turnos_to_dict(turnos)

    # Generar CSV en memoria con Pandas
    csv_buffer = generar_csv( datos, titulo=f"Turnos del día {fecha} (página {pagina})")

    # Devolver archivo CSV
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=turnos_{fecha}_p{pagina}.csv"
        }
    )

# GET reportes: turnos confirmados en un período en CSV --------------------------
@app.get("/reportes/csv/turnos-confirmados")
def descargar_csv_turnos_confirmados(
    # parámetro obligatorio: fecha desde (formato AAAA-MM-DD)
    desde: date = Query(..., description="Fecha desde (AAAA-MM-DD)"),
    # parámetro obligatorio: fecha hasta (formato AAAA-MM-DD)
    hasta: date = Query(..., description="Fecha hasta (AAAA-MM-DD)"),
    # inyección de la sesión de base de datos
    db: Session = Depends(get_db)
):
    # Validar que la fecha "desde" no sea mayor que "hasta"
    if desde > hasta:
        raise HTTPException(
            status_code=400,
            detail="'desde' no puede ser mayor que 'hasta'."
        )

    # Consultar todos los turnos con estado "confirmado" dentro del período
    turnos = (
        db.query(Turno)                               # armo la query sobre la tabla Turno
        .options(joinedload(Turno.persona))          # cargo también la relación persona en la misma consulta
        .filter(
            Turno.estado == ESTADO_TURNO_CONFIRMADO, # solo turnos confirmados
            Turno.fecha >= desde,                    # fecha mayor o igual a "desde"
            Turno.fecha <= hasta                     # fecha menor o igual a "hasta"
        )
        .order_by(
            Turno.fecha.asc(),                       # ordeno por fecha ascendente
            Turno.hora.asc(),                        # luego por hora ascendente
            Turno.id.asc()                           # y por id para desempatar
        )
        .all()                                       # ejecuto la consulta y obtengo una lista de Turno
    )

    # Si no hay turnos confirmados en ese período, devolvemos 404
    if not turnos:
        raise HTTPException(
            status_code=404,
            detail="No hay turnos confirmados en el período indicado."
        )

    # Transformar la lista de objetos Turno a una lista de diccionarios
    # con los campos id, fecha, hora, estado y persona (nombre)
    datos = turnos_to_dict(turnos)

    # Armamos un título descriptivo para el CSV (primera línea del archivo)
    titulo = f"Turnos confirmados desde {desde} hasta {hasta}"

    # Generamos el CSV en memoria usando la función utilitaria generar_csv
    csv_buffer = generar_csv(datos, titulo=titulo)

    # Devolver el CSV como archivo descargable
    return StreamingResponse(
        csv_buffer,                                  # buffer en memoria con el CSV
        media_type="text/csv",                       # tipo de contenido CSV
        headers={
            # nombre del archivo que se descargará
            "Content-Disposition": f"attachment; filename=turnos_confirmados_{desde}_a_{hasta}.csv"
        }
    )


# GET reportes: turnos confirmados en un período en PDF --------------------------
@app.get("/reportes/pdf/turnos-confirmados")
def descargar_pdf_turnos_confirmados(
    # parámetro obligatorio: fecha desde (formato AAAA-MM-DD)
    desde: date = Query(..., description="Fecha desde (AAAA-MM-DD)"),
    # parámetro obligatorio: fecha hasta (formato AAAA-MM-DD)
    hasta: date = Query(..., description="Fecha hasta (AAAA-MM-DD)"),
    # inyección de la sesión de base de datos
    db: Session = Depends(get_db)
):
    # Validar que la fecha "desde" no sea mayor que "hasta"
    if desde > hasta:
        raise HTTPException(
            status_code=400,
            detail="'desde' no puede ser mayor que 'hasta'."
        )

    # Consultar todos los turnos con estado "confirmado" dentro del período
    turnos = (
        db.query(Turno)                               # armo la query sobre la tabla Turno
        .options(joinedload(Turno.persona))          # cargo también la relación persona en la misma consulta
        .filter(
            Turno.estado == ESTADO_TURNO_CONFIRMADO, # solo turnos confirmados
            Turno.fecha >= desde,                    # fecha mayor o igual a "desde"
            Turno.fecha <= hasta                     # fecha menor o igual a "hasta"
        )
        .order_by(
            Turno.fecha.asc(),                       # primero ordeno por fecha ascendente
            Turno.hora.asc(),                        # luego por hora ascendente
            Turno.id.asc()                           # y por id para desempatar
        )
        .all()                                       # ejecuto la consulta y obtengo una lista de Turno
    )

    # Si no hay turnos confirmados en ese período, devuelvo 404
    if not turnos:
        raise HTTPException(
            status_code=404,
            detail="No hay turnos confirmados en el período indicado."
        )

    # Transformo la lista de objetos Turno a una lista de diccionarios
    # con los campos id, fecha, hora, estado y persona (nombre)
    datos = turnos_to_dict(turnos)

    # Armamos un título descriptivo para el reporte
    titulo = f"Turnos confirmados desde {desde} hasta {hasta}"
    # Armamos el nombre del archivo a descargar (sin extensión)
    nombre_archivo = f"turnos_confirmados_{desde}_a_{hasta}"

    # Generamos el PDF usando la función utilitaria pdf_response
    # que devuelve un StreamingResponse con el archivo PDF
    return pdf_response(datos, titulo, nombre_archivo)


@app.get("/reportes/csv/turnos-cancelados-por-mes")
def descargar_csv_turnos_cancelados_por_mes(
    anio: int = Query(..., description="Año en formato AAAA"),
    mes: int = Query(..., ge=1, le=12, description="Mes en formato 1-12"),
    pagina: int = Query(1, ge=1, description="Número de página (>=1)"),
    pagina_limite: int = Query(20, ge=1, le=20, description="Cantidad de registros por página"),
    db: Session = Depends(get_db)
):
    # Calcular desde qué registro empezar
    inicio = (pagina - 1) * pagina_limite

    # Consulta ORM con paginación
    turnos = (
        db.query(Turno)
        .options(joinedload(Turno.persona))
        .filter(Turno.estado == "cancelado")
        .filter(extract("year", Turno.fecha) == anio)
        .filter(extract("month", Turno.fecha) == mes)
        .order_by(Turno.fecha.asc(), Turno.hora.asc(), Turno.id.asc())
        .offset(inicio)
        .limit(pagina_limite)
        .all()
    )

    if not turnos:
        raise HTTPException( status_code=404, detail=f"No hay turnos cancelados para {anio}-{mes:02d} en la página {pagina}")

    # Transformar ORM → dict
    datos = turnos_to_dict(turnos)

    # Generar CSV en memoria con Pandas
    csv_buffer = generar_csv( datos, titulo=f"Turnos cancelados - {anio}-{mes:02d} (Página {pagina})")

    # Devolver archivo CSV
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=turnos_cancelados_{anio}_{mes:02d}_p{pagina}.csv"
        }
    )