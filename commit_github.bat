@echo off
setlocal enabledelayedexpansion
echo ==========================================
echo   Syncing MVP with GitHub...
echo ==========================================
echo.

:: 1. Adiciona todas as modificacoes
git add .

:: 2. Solicita o TITULO
set /p title="Enter commit TITLE: "

:: Cria o arquivo temporario com o titulo
echo !title! > .commit_msg_temp.txt
echo. >> .commit_msg_temp.txt

:: 3. Loop da DESCRICAO (Sai ao dar Enter com a linha vazia)
echo.
echo Enter detailed DESCRIPTION (Press ENTER on an empty line to finish):
echo -------------------------------------------------------------------------------

:loop
set "line="
set /p line="> "
if "!line!"=="" goto commit_phase
echo !line! >> .commit_msg_temp.txt
goto loop

:commit_phase
:: 4. Faz o commit lendo o arquivo temporario
git commit -F .commit_msg_temp.txt

:: 5. Limpa a sujeira
del .commit_msg_temp.txt

:: 6. Empurra para a nuvem
git push origin main

echo.
echo ==========================================
echo   Upload completed successfully!
echo ==========================================
pause