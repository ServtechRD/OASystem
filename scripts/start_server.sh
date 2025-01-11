#!/bin/bash

# 定义虚拟环境路径和 PID 文件路径
VENV_PATH="/home/oa/backend/venv"
SERVER_PATH="/home/oa/backend"
PID_FILE="/home/oa/scripts/uvicorn.pid"

# 激活虚拟环境
if [ -d "$VENV_PATH" ]; then
  source "$VENV_PATH/bin/activate"
  echo "Virtual environment activated."
else
  echo "Virtual environment not found at $VENV_PATH"
  exit 1
fi

# 检查是否已运行
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "Uvicorn is already running (PID: $(cat $PID_FILE))"
  exit 1
fi

cd $SERVER_PATH

# 启动 Uvicorn
uvicorn main:app --host 0.0.0.0 --port 39000 &
echo $! > "$PID_FILE"
echo "Uvicorn started (PID: $!)"

