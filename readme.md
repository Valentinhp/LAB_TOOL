# LabTool 🛠️

Una herramienta gráfica para automatizar tareas administrativas en Windows.

## ¿Qué es?

LabTool es un programa con interfaz gráfica hecho para ayudar a técnicos de sistemas a automatizar tareas comunes en computadoras con Windows. Entre sus funciones están:

- Crear usuarios locales sin contraseña  
- Eliminar uno o varios usuarios existentes  
- Reemplazar un usuario por otro nuevo  
- Aplicar un fondo de pantalla y bloquearlo para que no lo cambien  
- Borrar carpetas de usuarios huérfanos (residuos en C:\Users)  
- Copiar accesos directos útiles al escritorio  

## Tecnologías utilizadas

- Hecho en Python con interfaz Tkinter  
- Scripts automatizados con PowerShell  
- Empaquetado con PyInstaller  
- Requiere permisos de administrador para funcionar correctamente  

## Instalación

1. Clonar el repositorio desde GitHub  
2. Crear un entorno virtual con Python  
3. Activar el entorno e instalar dependencias desde requirements.txt  
4. Ejecutar el archivo `main.py`  

## Compilación a .exe

Se puede generar un ejecutable único con PyInstaller usando los siguientes parámetros:

- Empaquetado en un solo archivo  
- Ventana sin consola  
- Elevación automática de permisos (UAC)  
- Incluye carpetas: `resources`, `powershell`, `modules`, `utils`  
- Icono personalizado desde `resources/app.ico`  

## Funcionalidades disponibles

**Módulo:** Crear usuario  
**Descripción:** Crea un nuevo usuario local sin contraseña  

**Módulo:** Borrar usuario  
**Descripción:** Permite eliminar uno o varios usuarios del sistema  

**Módulo:** Reemplazar usuario  
**Descripción:** Borra un usuario y crea otro con el mismo acceso  

**Módulo:** Fondo de pantalla  
**Descripción:** Aplica una imagen como fondo y bloquea los cambios  

**Módulo:** Limpieza de perfiles  
**Descripción:** Elimina carpetas huérfanas que quedan en `C:\Users`  

**Módulo:** Atajos de escritorio  
**Descripción:** Copia accesos directos seleccionados al escritorio  

## Estructura del proyecto

LabTool/
├── main.py
├── modules/
├── powershell/
├── resources/
├── utils/
├── requirements.txt
├── README.md
├── .gitignore 




## Autor: Valen 
**Versión actual:** 3.1  
**Descripción:** Este proyecto fue creado para facilitar la administración de computadoras en laboratorios, escuelas o espacios donde se gestionan muchos usuarios en Windows.
