@echo off
:: 启动本地服务器（首次运行时自动下载 openscad-wasm，约 20MB）
:: SCAD 编译已移至浏览器端，无需本地安装 OpenSCAD

set PORT=8080

netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
  echo 服务器已在运行：http://localhost:%PORT%/viewer/index.html
) else (
  echo 启动服务器：http://localhost:%PORT%/viewer/index.html
  start /b python server.py %PORT%
  echo 服务器已启动。
)

echo.
echo 浏览器访问：http://localhost:%PORT%/viewer/index.html
