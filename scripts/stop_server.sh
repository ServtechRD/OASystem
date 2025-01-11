#!/bin/bash

# 定义虚拟环境路径和 PID 文件路径
VENV_PATH="/home/oa/backend/venv"
PID_FILE="/home/oa/scripts/uvicorn.pid"

# 激活虚拟环境
if [ -d "$VENV_PATH" ]; then
  source "$VENV_PATH/bin/activate"
  echo "Virtual environment activated."
else
  echo "Virtual environment not found at $VENV_PATH"
  exit 1
fi

# 检查是否有运行进程
if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found. Uvicorn may not be running."
  exit 1
fi

# 停止进程
PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Uvicorn stopped (PID: $PID)"
  rm -f "$PID_FILE"
else
  echo "Process $PID not running. Cleaning up PID file."
  rm -f "$PID_FILE"
fi
