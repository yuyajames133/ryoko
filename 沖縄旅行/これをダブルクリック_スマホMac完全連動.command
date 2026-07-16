#!/bin/bash
cd "$(dirname "$0")"

APP_DIR="$(pwd)"
VENV_DIR="$APP_DIR/.venv"
PORT="8567"
LOCAL_URL="http://127.0.0.1:$PORT"
CF_DIR="$APP_DIR/.cloudflared"
CF_BIN="$CF_DIR/cloudflared"
STREAMLIT_LOG="$APP_DIR/streamlit.log"
TUNNEL_LOG="$APP_DIR/cloudflare_tunnel.log"
PUBLIC_URL_FILE="$APP_DIR/スマホ用URL.txt"

clear
echo "旅ゲームメーカー 全国版【スマホMac完全連動版】"
echo "Macの電源・Wi-Fi・このターミナルは切らないでください。"
echo

if ! command -v python3 >/dev/null 2>&1; then
  open "https://www.python.org/downloads/macos/"
  exit 1
fi

mkdir -p "$CF_DIR"

if [ ! -x "$CF_BIN" ]; then
  echo "Cloudflare Tunnelを初回準備しています..."
  TMP_DIR="$(mktemp -d)"
  if [ "$(uname -m)" = "arm64" ]; then
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
  else
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
  fi

  curl -L --fail "$CF_URL" -o "$TMP_DIR/cloudflared.tgz" || exit 1
  tar -xzf "$TMP_DIR/cloudflared.tgz" -C "$TMP_DIR" || exit 1
  FOUND_BIN="$(find "$TMP_DIR" -type f -name cloudflared | head -n 1)"
  [ -z "$FOUND_BIN" ] && exit 1
  cp "$FOUND_BIN" "$CF_BIN"
  chmod +x "$CF_BIN"
  rm -rf "$TMP_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

STAMP="$VENV_DIR/.requirements_installed"
REQ_HASH="$(shasum -a 256 requirements.txt | awk '{print $1}')"
OLD_HASH=""
[ -f "$STAMP" ] && OLD_HASH="$(cat "$STAMP")"

if [ "$REQ_HASH" != "$OLD_HASH" ]; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt || exit 1
  echo "$REQ_HASH" > "$STAMP"
fi

OLD_PID="$(lsof -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null)"
[ -n "$OLD_PID" ] && kill "$OLD_PID" >/dev/null 2>&1
pkill -f "$CF_BIN tunnel --url $LOCAL_URL" >/dev/null 2>&1

rm -f "$STREAMLIT_LOG" "$TUNNEL_LOG" "$PUBLIC_URL_FILE"

python -m streamlit run app.py   --server.address 127.0.0.1   --server.port "$PORT"   --server.headless true   --browser.gatherUsageStats false   > "$STREAMLIT_LOG" 2>&1 &
STREAMLIT_PID=$!

cleanup() {
  kill "$TUNNEL_PID" >/dev/null 2>&1
  kill "$STREAMLIT_PID" >/dev/null 2>&1
}
trap cleanup EXIT INT TERM

for i in {1..90}; do
  curl -s "$LOCAL_URL/_stcore/health" >/dev/null 2>&1 && break
  kill -0 "$STREAMLIT_PID" >/dev/null 2>&1 || { open "$STREAMLIT_LOG"; exit 1; }
  sleep 1
done

curl -s "$LOCAL_URL/_stcore/health" >/dev/null 2>&1 || { open "$STREAMLIT_LOG"; exit 1; }

"$CF_BIN" tunnel --no-autoupdate --url "$LOCAL_URL" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

PUBLIC_URL=""
for i in {1..90}; do
  PUBLIC_URL="$(grep -Eo 'https://[-a-zA-Z0-9]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -n 1)"
  [ -n "$PUBLIC_URL" ] && break
  kill -0 "$TUNNEL_PID" >/dev/null 2>&1 || { open "$TUNNEL_LOG"; exit 1; }
  sleep 1
done

[ -z "$PUBLIC_URL" ] && { open "$TUNNEL_LOG"; exit 1; }

echo "$PUBLIC_URL" > "$PUBLIC_URL_FILE"

echo
echo "スマホ用URL"
echo "$PUBLIC_URL"
echo
echo "このURLをスマホへ送って開いてください。"
echo "URLは起動するたびに変わります。"
echo "Macの電源・Wi-Fi・このターミナルを切ると使えなくなります。"

open "$PUBLIC_URL_FILE"
open "$LOCAL_URL"
osascript -e "display dialog \"外出先スマホ用URLを作成しました。\\n\\n$PUBLIC_URL\\n\\nURLは『スマホ用URL.txt』にも保存しています。\" buttons {\"OK\"} default button \"OK\""

wait "$STREAMLIT_PID"
