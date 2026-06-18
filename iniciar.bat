@echo off
title FBVA - Sistema de Gestao de Clubes
cd /d "%~dp0"

echo.
echo  ================================================
echo   FBVA - Federacao Brasileira de Veiculos Antigos
echo   Sistema de Gestao de Clubes
echo  ================================================
echo.

rem Carrega variaveis de ambiente do arquivo .env, se existir
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
  )
  echo  Configuracoes carregadas do arquivo .env
)

echo  Iniciando servidor...
echo  Acesse: http://localhost:5000
echo.
echo  Login inicial:
echo    E-mail : admin@fbva.org.br
echo    Senha  : Admin@2024
echo.
echo  Pressione Ctrl+C para encerrar.
echo.
python app.py
pause
