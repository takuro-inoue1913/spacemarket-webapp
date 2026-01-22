@echo off
chcp 65001 > nul
echo ========================================
echo スペースマーケット お気に入り収集ツール
echo セットアップスクリプト (Windows)
echo ========================================
echo.

REM Pythonのチェック
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません。
    echo.
    echo Python 3.8以上をインストールしてください:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] Pythonバージョン確認...
python --version

echo.
echo [2/3] 必要なパッケージをインストール中...
pip install -r requirements.txt

echo.
echo [3/3] セットアップ完了！
echo.
echo ========================================
echo 使い方:
echo   start.bat をダブルクリックして起動
echo ========================================
echo.
pause
