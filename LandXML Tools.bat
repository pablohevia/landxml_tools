@echo off
REM LandXML Tools Suite — PySide6 Launcher
REM Activa el entorno 'geo_interp' y lanza la suite GUI unificada.

call C:\tools\miniconda3\Scripts\activate.bat geo_interp
if %errorlevel% neq 0 (
    echo Error: No se pudo activar el entorno conda 'geo_interp'.
    echo Asegurate de que conda esta instalado en C:\tools\miniconda3\
    pause
    exit /b %errorlevel%
)

start "LandXML Tools" /B pythonw "e:\GitHub\landxml_tools\landxml_suite.py"
