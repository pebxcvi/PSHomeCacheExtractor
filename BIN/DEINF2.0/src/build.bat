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

ENDLOCAL
EXIT /B

:BUILD

REM == FROM ChatGPT 4.1 ==

REM === Check for .NET 6 SDK ===
dotnet --list-sdks | findstr /C:"6." >nul
if errorlevel 1 (
    echo .NET 6 SDK not found. Opening download page...
    start https://dotnet.microsoft.com/en-us/download/dotnet/6.0
    pause
    exit /b 1
)

REM === Clean and build ===
dotnet clean
dotnet build -c Release

REM === Find output folder (handles spaces) ===
set "BUILDDIR="
for /d %%D in ("bin\Release\*") do (
    set "BUILDDIR=%%~nxD"
    goto :break
)
:break

REM === Move build output one level up ===
cd ..
set "DEST=%cd%"
cd src

if not defined BUILDDIR (
    echo Build output folder not found!
    pause
    exit /b 1
)

echo Moving build output to "%DEST%"
xcopy /s /y /e "bin\Release\%BUILDDIR%\*" "%DEST%\" 

REM Delete the build output directory after moving
rmdir /s /q "bin\Release\%BUILDDIR%"

echo Done.
pause
cmd /k
