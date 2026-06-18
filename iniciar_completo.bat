@echo off
title FBVA - Sistema Completo
cd /d "%~dp0"

echo.
echo  ================================================
echo   FBVA - Sistema Completo
echo   Flask (porta 5000) + WhatsApp (porta 3001)
echo  ================================================
echo.

rem Instala dependencias Python se necessario
pip show flask >nul 2>&1 || pip install -r requirements.txt

rem Instala dependencias Node se necessario
if not exist "wa_service\node_modules" (
  echo  Instalando dependencias do servico WhatsApp (primeira vez)...
  cd wa_service
  "C:\Program Files\nodejs\npm.cmd" install
  cd ..
  echo.
)

echo  Iniciando servico WhatsApp em segundo plano...
start "FBVA WhatsApp" /min "C:\Program Files\nodejs\node.exe" "wa_service\server.js"

echo  Aguardando inicializacao do WhatsApp (5s)...
timeout /t 5 /nobreak >nul

echo  Iniciando servidor principal...
echo.
echo  Acesse: http://localhost:5000
echo  Login : admin@fbva.org.br / Admin@2024
echo.
echo  Pressione Ctrl+C para encerrar o servidor principal.
echo  (A janela do WhatsApp ficara minimizada na barra de tarefas)
echo.
python app.py
pause
