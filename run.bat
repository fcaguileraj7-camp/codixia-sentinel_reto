@echo off
rem SentinelGuard AI - arranque de 1 comando (Windows). Equivalente para Linux y Mac: run.sh.
rem Los mensajes van sin acentos ni parentesis a proposito: se leen igual en cualquier consola
rem y los parentesis romperian los bloques de cmd.
rem
rem Lo que hace, en orden: busca Python 3.10+, crea .venv si falta, instala requirements.txt,
rem crea .env desde .env.example si falta, verifica la configuracion sin mostrar la llave
rem y levanta el agente. Es idempotente: se puede correr las veces que haga falta.
rem
rem SEGURIDAD DE COSTOS: por defecto fuerza GROK_MODE=mock en el proceso que lanza, aunque
rem el .env diga live, porque load_dotenv no pisa una variable que ya existe en el entorno.
rem Las llamadas reales a Grok gastan el saldo compartido del equipo y solo se activan
rem con --live explicito. Ejecutalo desde una consola: cmd o PowerShell.
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "MODE=web"
set "LIVE=0"

:parse
if "%~1"=="" goto parsed
if "%~1"=="--live" (
    set "LIVE=1"
    shift
    goto parse
)
if "%~1"=="-h" goto usage
if "%~1"=="--help" goto usage
if "%~1"=="--cli" (
    set "NEWMODE=cli"
    goto setmode
)
if "%~1"=="--test" (
    set "NEWMODE=test"
    goto setmode
)
if "%~1"=="--check" (
    set "NEWMODE=check"
    goto setmode
)
echo [run] ERROR: argumento desconocido: "%~1". Usa --help.
exit /b 2

:setmode
if not "%MODE%"=="web" (
    echo [run] ERROR: elige un solo modo entre --cli, --test y --check.
    exit /b 2
)
set "MODE=%NEWMODE%"
shift
goto parse

:parsed
if "%LIVE%"=="1" if "%MODE%"=="test" goto livebad
if "%LIVE%"=="1" if "%MODE%"=="check" goto livebad
goto live_ok
:livebad
echo [run] ERROR: --live no se combina con --test ni --check.
exit /b 2
:live_ok

rem 1. Python 3.10+. Se prueba que de verdad ejecute: python puede ser un stub de la Microsoft Store.
set "PY="
call :try_python py -3
if not defined PY call :try_python python
if not defined PY (
    call :fail "no encontre Python 3.10 o superior. Instalalo desde https://www.python.org/downloads/ y vuelve a correr run.bat"
    exit /b 1
)

rem 2. Entorno virtual. Nunca se borra uno existente.
set "VENV_PY=.venv\Scripts\python.exe"
if exist ".venv" if not exist "%VENV_PY%" (
    call :fail ".venv existe pero no es de este sistema o quedo a medias, por ejemplo por un Ctrl+C al crearlo. Falta %VENV_PY%. No lo borro: renombralo o eliminalo tu y vuelve a correr run.bat"
    exit /b 1
)
rem Regla de este archivo: un exit /b dentro de un bloque anidado en otro bloque, o dentro de un
rem bloque con else, devolvia codigo 0 al ejecutar cmd /c run.bat. Los bloques de un solo nivel
rem funcionan bien; lo que necesita dos niveles o else se resuelve con etiquetas.
if exist ".venv" goto venv_ready
echo [run] creando entorno virtual .venv ...
%PY% -m venv .venv
if not errorlevel 1 goto venv_ready
if exist ".venv" rmdir /s /q ".venv"
call :fail "no pude crear el entorno virtual."
exit /b 1
:venv_ready
"%VENV_PY%" -c "pass" >nul 2>nul
if errorlevel 1 (
    call :fail ".venv no ejecuta Python. No lo borro: eliminalo tu y vuelve a correr run.bat"
    exit /b 1
)

rem 3. Dependencias. Siempre se corre pip: si ya estan satisfechas es rapido y no hay estado
rem intermedio que pueda quedar roto.
echo [run] instalando dependencias de requirements.txt ...
"%VENV_PY%" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    call :fail "fallo la instalacion de dependencias. Revisa tu conexion a Internet. Si el error menciona Long Path, clona el repo en una ruta corta como C:\sentinel y vuelve a correr run.bat"
    exit /b 1
)
"%VENV_PY%" -m pip check >nul 2>nul
if errorlevel 1 echo [run] AVISO: pip check reporta dependencias en conflicto. Si algo falla, borra .venv y repite.

rem 4. .env: se crea desde el ejemplo si falta y nunca se imprime su contenido.
if exist ".env" goto env_ready
if not exist ".env.example" (
    call :fail "falta .env.example, no puedo crear .env"
    exit /b 1
)
copy /y ".env.example" ".env" >nul
echo [run] cree .env desde .env.example. Sin llave, modo demo local. Editalo para poner tu RETO_API_KEY.
:env_ready

rem 5. Estado de la configuracion. El codigo de salida es 10 + 1 llave valida + 2 el .env pide live:
rem asi un fallo de Python, codigo 1, no se confunde con un resultado. Solo 10 a 13 son validos:
rem un codigo mayor, por ejemplo por una senal, no se debe leer como llave valida.
"%VENV_PY%" -c "import sys; from dotenv import dotenv_values as d; import src.config as c; m=(d('.env').get('GROK_MODE') or 'mock').lower(); sys.exit(10 + (1 if c.is_configured() else 0) + (2 if m in ('live','real','production') else 0))"
set "RC=%errorlevel%"
set "RCBAD=0"
if %RC% LSS 10 set "RCBAD=1"
if %RC% GTR 13 set "RCBAD=1"
if "%RCBAD%"=="1" (
    call :fail "no pude leer la configuracion de src/config.py. Revisa .env y requirements.txt"
    exit /b 1
)
set /a "KEYOK=(RC-10) & 1"
set /a "ENVLIVE=((RC-10) >> 1) & 1"

rem 6. Modo de ejecucion. mock es el defecto, live solo con --live y llave valida.
rem Se resuelve con etiquetas y no con bloques if anidados: un exit /b dentro de un if doble
rem con else devolvia codigo 0 al ejecutarlo como cmd /c run.bat.
if "%LIVE%"=="1" goto mode_live
set "GROK_MODE=mock"
if "%ENVLIVE%"=="1" echo [run] AVISO: tu .env pide GROK_MODE=live. Este arranque lo ignora y usa mock, costo 0 USD. Usa --live para activarlo.
if "%KEYOK%"=="1" echo [run] llave del reto: configurada. Modo: mock, costo 0 USD.
if not "%KEYOK%"=="1" echo [run] llave del reto: no configurada. Modo: demo local mock, costo 0 USD.
rem Guardia que falla cerrado: con GROK_MODE=mock definido, src/config.py no debe quedar en live.
rem Si alguien agrega override=True a load_dotenv, el .env en live volveria a ganar y gastaria saldo.
"%VENV_PY%" -c "import sys; import src.config as c; sys.exit(1 if c.is_live_mode_enabled() else 0)"
if errorlevel 1 (
    call :fail "la configuracion quedo en live pese a GROK_MODE=mock, o no se pudo leer. No arranco para no gastar saldo. Avisa al equipo: revisa load_dotenv en src/config.py"
    exit /b 1
)
goto mode_done

:mode_live
if not "%KEYOK%"=="1" (
    call :fail "--live necesita una RETO_API_KEY valida con formato pk_ en .env"
    exit /b 1
)
set "GROK_MODE=live"
echo [run] MODO LIVE: las llamadas a Grok son reales y consumen el saldo compartido del equipo.

:mode_done
set "PYTHONUTF8=1"

rem 7. Lanzar el agente.
if "%MODE%"=="check" goto do_check
if "%MODE%"=="test" goto do_test
if "%MODE%"=="cli" goto do_cli

:do_web
echo [run] levantando la interfaz web. Ctrl+C para detener. Abre en tu navegador la Local URL que aparece abajo, normalmente http://localhost:8501
rem headless: sin esto Streamlit pide un correo en la primera ejecucion y se queda esperando.
rem address localhost y sin estadisticas: el arranque por defecto no se expone a la red.
rem La entrada desde nul evita el aviso Terminar el trabajo por lotes S/N al pulsar Ctrl+C.
"%VENV_PY%" -m streamlit run app_streamlit.py --server.headless true --server.address localhost --browser.gatherUsageStats false <nul
exit /b %errorlevel%

:do_cli
"%VENV_PY%" main.py
exit /b %errorlevel%

:do_test
"%VENV_PY%" -m pytest tests/ -q
exit /b %errorlevel%

:do_check
rem sentinel.py atrapa los errores del modelo y devuelve analysis_available=False sin lanzar nada:
rem por eso la prueba exige True y no basta con que process_message no falle.
"%VENV_PY%" -c "import sys; from src.agent.sentinel import SentinelAgent; r = SentinelAgent().process_message('Su cuenta Nequi fue bloqueada. Llame ya al 3001234567 para reactivarla'); d = r['decision']; ok = d.get('analysis_available') is True; print('[run] prueba de humo ' + ('OK' if ok else 'FALLO: el agente respondio en modo degradado') + ', riesgo: ' + str(d.get('risk_level'))); sys.exit(0 if ok else 1)"
if errorlevel 1 (
    call :fail "la prueba de humo del agente fallo"
    exit /b 1
)
echo [run] listo: entorno verificado. Corre run.bat para levantar el agente.
exit /b 0

:usage
echo Uso: run.bat [--cli ^| --test ^| --check] [--live]
echo.
echo   sin flags    Levanta la interfaz web Streamlit en http://localhost:8501
echo   --cli        Demostracion por consola, main.py
echo   --test       Suite de pruebas, pytest con red mockeada y costo 0 USD
echo   --check      Solo prepara y verifica: venv, dependencias, .env y una prueba de humo en mock
echo   --live       Permite llamadas reales a Grok, consume saldo. Exige una RETO_API_KEY con formato pk_.
echo                No se combina con --test ni --check.
echo   -h, --help   Muestra esta ayuda
exit /b 0

:try_python
%* -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0

:fail
echo [run] ERROR: %~1
exit /b 1
