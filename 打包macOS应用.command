#!/bin/zsh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1

APP_NAME="美国号码去重"
ICON_PATH="assets/icon.icns"

if ! command -v python3 >/dev/null 2>&1; then
  echo "未检测到 python3，请先安装 (brew install python)"
  exit 127
fi

python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install pyinstaller >/dev/null 2>&1 || {
  echo "安装 PyInstaller 失败，请检查网络或稍后重试"
  exit 1
}

if [ ! -f "$ICON_PATH" ]; then
  echo "未找到图标 $ICON_PATH，将使用默认图标"
  ICON_ARG=""
else
  ICON_ARG="--icon=$ICON_PATH"
fi

pyinstaller --noconfirm --windowed $ICON_ARG \
  --name "$APP_NAME" gui_dedupe.py

# 清理同名可执行文件（PyInstaller 可能会同时生成一个无扩展名的同名文件）
if [ -f "dist/$APP_NAME" ] && [ ! -d "dist/$APP_NAME" ]; then
  rm -f "dist/$APP_NAME"
fi

echo "打包完成：dist/$APP_NAME.app"
open "dist/$APP_NAME.app" || open dist || true


