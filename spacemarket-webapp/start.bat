@echo off
chcp 65001 > nul
echo ========================================
echo スペースマーケット お気に入り収集ツール
echo ========================================
echo.
echo サーバーを起動しています...
echo ブラウザで以下のURLを開いてください:
echo.
echo   http://localhost:8080
echo.
echo 終了するには Ctrl+C を押してください
echo ========================================
echo.

REM ブラウザを自動で開く
timeout /t 2 /nobreak > nul
start http://localhost:8080

REM Flaskアプリを起動
python app.py

pause
