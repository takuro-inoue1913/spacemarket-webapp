#!/bin/bash

echo "========================================"
echo "スペースマーケット お気に入り収集ツール"
echo "セットアップスクリプト (Mac/Linux)"
echo "========================================"
echo ""

# Pythonのチェック
if ! command -v python3 &> /dev/null
then
    echo "[エラー] Python 3がインストールされていません。"
    echo ""
    echo "Macの場合:"
    echo "  brew install python3"
    echo ""
    echo "Ubuntuの場合:"
    echo "  sudo apt-get install python3 python3-pip"
    echo ""
    exit 1
fi

echo "[1/3] Pythonバージョン確認..."
python3 --version

echo ""
echo "[2/3] 必要なパッケージをインストール中..."
pip3 install -r requirements.txt

echo ""
echo "[3/3] セットアップ完了！"
echo ""
echo "========================================"
echo "使い方:"
echo "  bash start.sh を実行して起動"
echo "または:"
echo "  ./start.sh"
echo "========================================"
echo ""
