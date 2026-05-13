@echo off
setlocal

set SCAD_FILE=%1
if "%SCAD_FILE%"=="" set SCAD_FILE=model\example.scad

set STL_FILE=%SCAD_FILE:.scad=.stl%
set PORT=8080

set OPENSCAD="C:\Program Files\OpenSCAD\openscad.exe"
if not exist %OPENSCAD% set OPENSCAD="C:\Program Files (x86)\OpenSCAD\openscad.exe"

echo Compiling %SCAD_FILE% to %STL_FILE% ...

%OPENSCAD% -o "%STL_FILE%" -D "$fn=16" "%SCAD_FILE%"

if %errorlevel% neq 0 (
  echo Compilation failed.
  pause
  exit /b 1
)

echo Done: %STL_FILE%

netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
  echo Server already running: http://localhost:%PORT%/viewer/index.html
) else (
  echo Starting server: http://localhost:%PORT%/viewer/index.html
  start /b python server.py %PORT%
  echo Server started.
)

echo.
echo Open in browser: http://localhost:%PORT%/viewer/index.html
endlocal
