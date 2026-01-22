#!/bin/bash

echo "========================================"
echo "スペースマーケット お気に入り収集ツール"
echo "========================================"
echo ""
echo "サーバーを起動しています..."
echo "ブラウザで以下のURLを開いてください:"
echo ""
echo "  http://localhost:8080"
echo ""
echo "終了するには Ctrl+C を押してください"
echo "========================================"
echo ""

# ブラウザを自動で開く（Mac）
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open http://localhost:8080 &
# ブラウザを自動で開く（Linux）
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sleep 2
    xdg-open http://localhost:8080 &
fi

# Flaskアプリを起動
python3 app.py
