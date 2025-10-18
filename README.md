Integrantes grupo8:

Micaela Insfran, Gaston Madeo, Rodrigo Emanuel Sanchez, Manuel Shocron

Enlace al video: https://drive.google.com/drive/folders/1mTIaz2h3PuNo7JZDkSKzSBnjYAwAM1o_?usp=sharing

Enlace a postman: https://rodridev22-215338.postman.co/workspace/Rodrigo-Sanchez's-Workspace~52e74b2b-410f-4ef0-8975-f2b0cbe860e8/collection/48652798-15125a2a-4a8c-4703-a7d7-5b3c21ebf490?action=share&creator=48652798

# SL-UNLA-LAB-2025-GRUPO-N8

## Requisitos previos
- Python 3.10 o superior instalado en el sistema.
- pip instalado y actualizado (verificar con `python -m pip --version`; actualiza con `python -m pip install --upgrade pip` si es necesario).

## Crear y activar el entorno virtual
1. Crear el venv en la raiz del proyecto:
```bash
python -m venv .venv
```
2. Activar el entorno:

- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

- Linux / macOS:
```bash
source .venv/bin/activate
```

> Ejecutar siempre los comandos desde la carpeta raiz del proyecto.

## Instalar las librerias del proyecto
Con el entorno virtual activo:
```bash
pip install -r requirements.txt
```

## Ejecutar la aplicacion
Con el entorno virtual activo:
```bash
uvicorn app:app --reload
```



ABM PERSONAS:

1- POST: Micaela Insfran

2- GET: Micaela Insfran

3- GET/por id: Rodrigo Sanchez

4- PUT: Rodrigo Sanchez

5- DELETE: Micaela Insfran

ABM TURNO:

6- POST: Manuel Shocron

7- GET: Manuel Shocron

8- GET/ por id: Manuel Shocron

9- GET/Turnos disponibles: Manuel Shocron

10- PUT: Rodrigo Sanchez

11- DELETE: Gaston Madeo


ABM CONTACTO:

12- POST: Micaela Insfran

13- GET: Micaela Insfran

14- PUT: Micaela Insfran

15- DELETE: Micaela Insfran

16- GET por ID: Gaston Madeo
