@echo off
REM Name of the virtual environment directory
set VENV_DIR=venv

REM Check if the virtual environment already exists
if exist %VENV_DIR% (
    echo Virtual environment '%VENV_DIR%' already exists.
    
    REM Activate the virtual environment
    call %VENV_DIR%\Scripts\activate
) else (
    REM Create the virtual environment
    python -m venv %VENV_DIR%
    echo Virtual environment '%VENV_DIR%' created.

    REM Activate the virtual environment and install local packages
    call %VENV_DIR%\Scripts\activate
    echo Installing requirements.txt...
    pip install -r requirements.txt
    echo requirements.txt installed.
)

REM Run python -m speech_to_text
echo Running python -m speech-to-text...
python -m speech-to-text

REM Keep the command prompt open
cmd /K