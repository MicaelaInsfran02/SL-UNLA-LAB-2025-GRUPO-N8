from datetime import datetime,date, timedelta
from sqlalchemy import or_, func
from config import HORARIO_INICIO, HORARIO_FIN, INTERVALO_MINUTOS, LIMITE_CANCELACIONES, ESTADO_TURNO_CANCELADO
from sqlalchemy.orm import Session
from database import Turno

from io import BytesIO
from borb.pdf import Document, Page, PDF
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.table.flexible_column_width_table import FlexibleColumnWidthTable
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.layout_element import Alignment
import pandas as pd
from io import StringIO
from fastapi.responses import StreamingResponse


#función calcular edad
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

#Generar horarios disponibles, rango (9-17), intervalo de 30 min.
def generar_horarios_posibles():
    inicio = HORARIO_INICIO
    fin = HORARIO_FIN
    intervalo = INTERVALO_MINUTOS
    horarios = []
    hora_actual = datetime.combine(date.today(), inicio)
    limite = datetime.combine(date.today(), fin)

    while hora_actual <= limite:
        horarios.append(hora_actual.time())
        hora_actual += timedelta(minutes=intervalo)

    return horarios

#Personas con un minimo 5 turnos cancelados.

def persona_limite_cancelados(db: Session):
    return db.query(
        Turno.persona_id,
        func.count(Turno.id).label("cancelados")
    ).filter(
        Turno.estado == ESTADO_TURNO_CANCELADO
    ).group_by(
        Turno.persona_id
    ).having(
        func.count(Turno.id) >= LIMITE_CANCELACIONES
    ).subquery()




# Generar CSV desde lista de diccionarios
def generar_csv(datos: list[dict]) -> str:

   #Recibe una lista de diccionarios y devuelve el contenido CSV como string.
    df = pd.DataFrame(datos)
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def generar_pdf_tabla(datos: list[dict], titulo: str) -> BytesIO:
    # Crear buffer en memoria
    buffer = BytesIO()  
    doc = Document() 
    page = Page() 
    doc.add_page(page) 
    layout = SingleColumnLayout(page)

    # Título
    layout.add(
        Paragraph(
            titulo,
            font="Helvetica-Bold", #fuente
            font_size=14, #tamaño
            horizontal_alignment=Alignment.LEFT #alineación
        )
    )

    if not datos:
        layout.add(Paragraph("No hay registros", font="Helvetica", font_size=11))
        PDF.dumps(buffer, doc)
        buffer.seek(0) # volver al inicio del stream
        return buffer

    columnas = list(datos[0].keys()) # Obtener nombres de columnas desde las claves del primer diccionario
    tabla = FlexibleColumnWidthTable( 
        number_of_rows=len(datos) + 1,  # +1 para la fila de encabezados
        number_of_columns=len(columnas) # de columnas
    )
    # Encabezados
    for col in columnas:
        tabla.add(
            TableCell(
                Paragraph(str(col).capitalize(), font="Helvetica-Bold", font_size=11, horizontal_alignment=Alignment.CENTERED),
                background_color=HexColor("EAEAEA")
            )
        )
    # Filas
    for fila in datos:
        for col in columnas:
            valor = fila.get(col, "")
            tabla.add(
                TableCell(
                    Paragraph(str(valor), font="Helvetica", font_size=10, horizontal_alignment=Alignment.CENTERED),
                    padding_top=10,
                    padding_bottom=10,
                    padding_left=20,
                    padding_right=20
                )
            )

    layout.add(tabla) # Agregar tabla al layout

    # Guardar en buffer en memoria
    PDF.dumps(buffer, doc)
    buffer.seek(0)  # volver al inicio del stream
    return buffer

# Convertir lista de turnos a lista de diccionarios
def turnos_to_dict(turnos):
    return [
        {
            "id": t.id,
            "fecha": str(t.fecha),
            "hora": str(t.hora),
            "estado": t.estado,
            "persona": t.persona.nombre if t.persona else None
        }
        for t in turnos
    ]

#- Generación de PDF en memoria y respuesta. El resultado es un BytesIo (un buffer en memoria, no en disco)
def pdf_response(datos, titulo, nombre_archivo):
    pdf_buffer = generar_pdf_tabla(datos, titulo) # El resultado es un BytesIo (un buffer en memoria, no en disco)
    return StreamingResponse( 
        pdf_buffer, # Devolver como respuesta de streaming
        media_type="application/pdf", #  indica al navegador que el contenido es un archivo PDF.
        headers={ # Indicar que es un archivo adjunto con nombre
            "Content-Disposition": f"attachment; filename={nombre_archivo}.pdf" # Nombre del archivo
        }
    )
