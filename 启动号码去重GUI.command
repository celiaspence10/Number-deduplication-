#!/bin/zsh

# Resolve this script directory even if double-clicked
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1

LOG_FILE="$DIR/last_run.log"

# Use macOS default python3
if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "未找到 python3" message "请先安装 Python 3 再重试。建议在终端执行：brew install python"'
  exit 127
fi

# Clear previous log
echo "[Start] $(date)" > "$LOG_FILE"
echo "DIR=$DIR" >> "$LOG_FILE"
python3 --version >> "$LOG_FILE" 2>&1

# Launch GUI and capture errors
python3 gui_dedupe.py >> "$LOG_FILE" 2>&1 || {
  tail -n 50 "$LOG_FILE" | sed 's/"/\"/g' | osascript -e 'display alert "启动失败" message (do shell script "cat")'
  exit 1
}


