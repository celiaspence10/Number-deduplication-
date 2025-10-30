#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
LOG_FILE="$DIR/self_check.log"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "未找到 python3" message "请先安装：brew install python"'
  exit 127
fi

echo "[Start] $(date)" > "$LOG_FILE"
python3 --version >> "$LOG_FILE" 2>&1
python3 self_check.py >> "$LOG_FILE" 2>&1

tail -n 100 "$LOG_FILE" | sed 's/"/\"/g' | osascript -e 'display alert "自检结果" message (do shell script "cat")'


