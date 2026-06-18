@echo off
title FBVA - Servico WhatsApp
cd /d "%~dp0"

echo.
echo  ================================================
echo   FBVA - Servico WhatsApp (whatsapp-web.js)
echo  ================================================
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo  [ERRO] Node.js nao encontrado!
  echo.
  echo  Instale o Node.js em: https://nodejs.org
  echo  Recomendado: versao LTS (ex: 20.x)
  echo.
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo  Instalando dependencias pela primeira vez...
  echo  (Isso pode demorar alguns minutos na 1a vez)
  echo.
  npm install
  echo.
)

echo  Iniciando servico WhatsApp na porta 3001...
echo  Acesse o sistema e va em Mensageiro para escanear o QR Code.
echo.
echo  Pressione Ctrl+C para encerrar.
echo.
node server.js
pause
