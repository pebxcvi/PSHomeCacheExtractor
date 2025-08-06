@ECHO OFF
SETLOCAL DISABLEDELAYEDEXPANSION
SET "CURDIR=%~DP0"
SET "REMSLASH=%CURDIR:~0,-1%"

REM == NOT FROM AI. Clearly doesn't understand batch script tricks. ==

FOR /F "TOKENS=*" %%A IN ('DIR /B "%REMSLASH%\build.bat" 2^>NUL') DO (
		SET "A=%%A"
		CALL :CONT
)

GOTO BUILD
CMD /K

:CONT

CALL SET "A=%%A%%"
SET "SRCFOLDER=%REMSLASH:\=" & SET "SRCFOLDER=%"

SETLOCAL ENABLEDELAYEDEXPANSION

SET "REMSRC=!REMSLASH:\%SRCFOLDER%=!"

FOR /F "TOKENS=*" %%B IN ('DIR /B /A:-D "%REMSRC%\*" 2^>NUL') DO (
		SET "B=%%B"
		IF EXIST "%REMSRC%\!B!" DEL "%REMSRC%\!B!"
)

FOR /F "TOKENS=*" %%C IN ('DIR /B /A:D "%REMSRC%\*lib*" 2^>NUL') DO (
		SET "C=%%C"
		IF EXIST "%REMSRC%\!C!" RMDIR /S /Q "%REMSRC%\!C!"
)

ENDLOCAL
EXIT /B

:BUILD
REM == FROM ChatGPT 4.1 ==

REM === Settings ===
set "PY_VER=3.11.7"
set "PY_DIR=%LocalAppData%\Programs\Python\Python311"
set "PY_EXE=%PY_DIR%\python.exe"
set "PY_EXE_SYS=C:\Python311\python.exe"
set "SETUP_EXE=%TEMP%\python311-setup.exe"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/python-%PY_VER%-amd64.exe"

REM === Check for per-user Python ===
set "FOUND_PY="
if exist "%PY_EXE%" (
    "%PY_EXE%" --version 2>NUL | find "%PY_VER%" >NUL
    if not errorlevel 1 (
        set "FOUND_PY=%PY_EXE%"
    )
)

REM === Check for system-wide Python in C:\Python311 ===
if not defined FOUND_PY (
    if exist "%PY_EXE_SYS%" (
        "%PY_EXE_SYS%" --version 2>NUL | find "%PY_VER%" >NUL
        if not errorlevel 1 (
            set "FOUND_PY=%PY_EXE_SYS%"
        )
    )
)

REM === Also check in PATH for python3.11 ===
if not defined FOUND_PY (
    for /f "delims=" %%p in ('where python 2^>nul') do (
        "%%p" --version 2>NUL | find "%PY_VER%" >NUL
        if not errorlevel 1 (
            set "FOUND_PY=%%p"
            goto :foundpy
        )
    )
)

:foundpy
if not defined FOUND_PY (
    echo Python %PY_VER% not found. Downloading...
    powershell -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%SETUP_EXE%'"
    echo Installing Python %PY_VER% for current user...
    "%SETUP_EXE%" /quiet InstallLauncherAllUsers=0 InstallAllUsers=0 PrependPath=1 Include_test=0
    if exist "%PY_EXE%" (
        set "FOUND_PY=%PY_EXE%"
    ) else (
        echo ERROR: Python did not install correctly!
        pause
        exit /b 1
    )
)

echo.
echo Using: "%FOUND_PY%"
"%FOUND_PY%" --version

REM === Ensure pip is installed ===
"%FOUND_PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Pip not found, installing...
    "%FOUND_PY%" -m ensurepip --upgrade
)

REM === Check Pillow ===
"%FOUND_PY%" -m pip show pillow >nul 2>&1
if errorlevel 1 (
    echo Installing Pillow...
    "%FOUND_PY%" -m pip install pillow --no-warn-script-location
)

REM === Check cx_Freeze ===
"%FOUND_PY%" -m pip show cx_Freeze >nul 2>&1
if errorlevel 1 (
    echo Installing cx_Freeze...
    "%FOUND_PY%" -m pip install cx_Freeze --no-warn-script-location
)

REM -- Cleanup installer
if exist "%SETUP_EXE%" del /f /q "%SETUP_EXE%"

REM === Everything installed. Run your build. ===
echo.
echo Running: setup.py build
"%FOUND_PY%" setup.py build

REM == NOT FROM AI. Clearly doesn't understand batch script tricks. ==

FOR /F "TOKENS=*" %%A IN ('DIR /B "%REMSLASH%\build.bat" 2^>NUL') DO (
		SET "A=%%A"
		CALL :CONT
)

GOTO END
CMD /K

:CONT

CALL SET "A=%%A%%"
SET "SRCFOLDER=%REMSLASH:\=" & SET "SRCFOLDER=%"

SETLOCAL ENABLEDELAYEDEXPANSION

SET "REMSRC=!REMSLASH:\%SRCFOLDER%=!"

FOR /F "TOKENS=*" %%B IN ('DIR /B /A:D "%REMSLASH%\build\*" 2^>NUL') DO (
		SET "B=%%B"
		IF EXIST "%REMSLASH%\build\!B!" ROBOCOPY "%REMSLASH%\build\!B!" "%REMSRC%" /S /MOVE > NUL
		IF EXIST "%REMSLASH%\build" RMDIR /S /Q "%REMSLASH%\build"
)


ENDLOCAL
EXIT /B

:END
ECHO.
ECHO ALL DONE.
CMD /K