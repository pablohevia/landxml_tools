@echo off
REM LandXML Tools Launcher
REM Activates 'geo_interp' environment and runs the unified suite.

call C:\tools\miniconda3\Scripts\activate.bat geo_interp
if %errorlevel% neq 0 (
    echo Error activating conda environment 'geo_interp'.
    pause
    exit /b %errorlevel%
)

start "LandXML Tools" /B pythonw "e:\GitHub\landxml_tools\landxml_suite.py"
