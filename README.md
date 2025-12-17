# SL-UNLA-LAB-2025-GRUPO-N8

API REST para **gestión de Personas, Contactos y Turnos**, con **reportes descargables en PDF y CSV**.

---

## Integrantes (Grupo 8)

- Micaela Insfran  
- Gaston Madeo  
- Rodrigo Emanuel Sanchez  
- Manuel Shocron  

---

## Requisitos previos

- **Python 3.10+** instalado.
- **pip** instalado y actualizado.

> Ejecutar siempre los comandos desde la **carpeta raíz** del proyecto.

---

## Crear y activar el entorno virtual

1) Crear el entorno virtual en la raíz del proyecto:

```bash
python -m venv .venv
```

2) Activar el entorno:

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

---

## Instalar dependencias

Con el entorno virtual activo:

```bash
pip install -r requirements.txt
```

---

## Ejecutar la aplicación

Con el entorno virtual activo:

```bash
uvicorn app:app --reload
```

Cuando Uvicorn levanta, verás algo como:

```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Acceso a la API

- **Swagger UI:** `http://127.0.0.1:8000/docs`

---

## Postman

El archivo de colección de Postman debe estar en la **raíz del proyecto**:

- `Postman Turnos Grupo 8.postman_collection`

---

# Endpoints implementados y responsables

## ABM Personas

1. **POST** `/personas` — Micaela Insfran  
2. **GET** `/personas` — Micaela Insfran  
3. **GET** `/personas/{persona_id}` — Rodrigo Emanuel Sanchez  
4. **PUT** `/personas/{persona_id}` — Rodrigo Emanuel Sanchez  
5. **DELETE** `/personas/{persona_id}` — Micaela Insfran  

---

## ABM Turnos

6. **POST** `/turnos` — Manuel Shocron  
7. **GET** `/turnos` — Manuel Shocron  
8. **GET** `/turnos/{turno_id}` — Manuel Shocron  
9. **GET** `/turnos-disponibles` — Manuel Shocron  
10. **PUT** `/turnos/{turno_id}` — Rodrigo Emanuel Sanchez  
11. **DELETE** `/turnos/{turno_id}` — Gaston Madeo  

---

## ABM Contactos

12. **POST** `/contactos` — Micaela Insfran  
13. **GET** `/contactos` — Micaela Insfran  
14. **PUT** `/contactos/{contacto_id}` — Micaela Insfran  
15. **DELETE** `/contactos/{contacto_id}` — Micaela Insfran  
16. **GET** `/contactos/{contacto_id}` — Gaston Madeo  

---

## Reportes en PDF (Borb)

- **GET** `/reportes/pdf/turnos-por-fecha?fecha=YYYY-MM-DD` — Micaela Insfran  
- **GET** `/reportes/pdf/turnos-cancelados-por-mes` — Micaela Insfran  
- **GET** `/reportes/pdf/turnos-por-persona?dni=12345678` — Micaela Insfran  
- **GET** `/reportes/pdf/turnos-cancelados?min=5` — Rodrigo Emanuel Sanchez  
- **GET** `/reportes/pdf/turnos-confirmados?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` — Rodrigo Emanuel Sanchez  
- **GET** `/reportes/pdf/estado-personas?habilitada=true/false` — Rodrigo Emanuel Sanchez  

---

## Reportes en CSV (Pandas)

- **GET** `/reportes/csv/turnos-por-fecha?fecha=YYYY-MM-DD` — Micaela Insfran  
- **GET** `/reportes/csv/turnos-cancelados-por-mes` — Micaela Insfran  
- **GET** `/reportes/csv/turnos-por-persona?dni=12345678` — Micaela Insfran  
- **GET** `/reportes/csv/turnos-cancelados?min=5` — Rodrigo Emanuel Sanchez  
- **GET** `/reportes/csv/turnos-confirmados?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` — Rodrigo Emanuel Sanchez  
- **GET** `/reportes/csv/estado-personas?habilitada=true/false` — Rodrigo Emanuel Sanchez  
