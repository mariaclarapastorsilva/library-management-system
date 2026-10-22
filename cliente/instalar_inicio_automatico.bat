@echo off
rem Faz o cliente abrir sozinho quando o usuario do Windows entrar.
rem Rode uma vez em cada maquina, na conta que os alunos usam.
rem Para todas as contas, rode como administrador com o parametro "todos".

if /I "%~1"=="todos" (
    set "PASTA_INICIAR=%ProgramData%\Microsoft\Windows\Start Menu\Programs\StartUp"
) else (
    set "PASTA_INICIAR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)

> "%PASTA_INICIAR%\controle_de_uso.bat" echo @start "" pythonw "%~dp0cliente.py"
echo Instalado em "%PASTA_INICIAR%\controle_de_uso.bat"
