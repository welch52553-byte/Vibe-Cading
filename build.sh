#!/bin/bash
# 启动本地服务器（首次运行时自动下载 openscad-wasm，约 20MB）
# SCAD 编译已移至浏览器端，无需本地安装 OpenSCAD

PORT="${1:-8080}"

if lsof -ti:$PORT > /dev/null 2>&1; then
  echo "服务器已在运行：http://localhost:$PORT/viewer/index.html"
else
  echo "启动服务器：http://localhost:$PORT/viewer/index.html"
  cd "$(dirname "$0")"
  python3 server.py $PORT
fi
