#!/bin/bash
# 编译 SCAD → STL（低精度预览版）并启动本地服务器

SCAD_FILE="${1:-model/example.scad}"
STL_FILE="${SCAD_FILE%.scad}.stl"
PORT="${2:-8080}"

echo "编译 $SCAD_FILE → $STL_FILE ..."

openscad -o "$STL_FILE" \
  -D '$fn=16' \
  "$SCAD_FILE"

if [ $? -ne 0 ]; then
  echo "编译失败"
  exit 1
fi

echo "完成：$STL_FILE"

# 检查端口是否已在运行
if lsof -ti:$PORT > /dev/null 2>&1; then
  echo "服务器已在运行：http://localhost:$PORT/viewer/index.html"
else
  echo "启动服务器：http://localhost:$PORT/viewer/index.html"
  cd "$(dirname "$0")"
  python3 server.py $PORT &
  echo "服务器 PID: $!"
fi
