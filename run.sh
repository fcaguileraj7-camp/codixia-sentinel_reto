#!/usr/bin/env bash
# SentinelGuard AI - arranque de 1 comando (Linux / macOS / Git Bash).
# Equivalente para Windows: run.bat. Los mensajes van sin acentos a proposito:
# asi se leen igual en cualquier terminal.
#
# Lo que hace, en orden: busca Python 3.10+, crea .venv si falta, instala requirements.txt,
# crea .env desde .env.example si falta, verifica la configuracion (sin mostrar la llave)
# y levanta el agente. Es idempotente: se puede correr las veces que haga falta.
#
# SEGURIDAD DE COSTOS: por defecto fuerza GROK_MODE=mock en el proceso que lanza, aunque
# el .env diga "live" (load_dotenv no pisa una variable que ya existe en el entorno).
# Las llamadas reales a Grok gastan el saldo compartido del equipo y solo se activan
# con --live explicito.
set -euo pipefail

usage() {
  cat <<'EOF'
Uso: ./run.sh [--cli | --test | --check] [--live]

  (sin flags)  Levanta la interfaz web (Streamlit) en http://localhost:8501
  --cli        Demostracion por consola (main.py)
  --test       Suite de pruebas (pytest; red mockeada, costo 0 USD)
  --check      Solo prepara y verifica: venv, dependencias, .env y una prueba de humo en mock
  --live       Permite llamadas reales a Grok (consume saldo). Exige RETO_API_KEY valida.
               No se combina con --test ni --check.
  -h, --help   Muestra esta ayuda
EOF
}

say() { printf '[run] %s\n' "$*"; }
die() { printf '[run] ERROR: %s\n' "$*" >&2; exit 1; }

cd "$(dirname "${BASH_SOURCE[0]}")"

MODE="web"
LIVE=0
for arg in "$@"; do
  case "$arg" in
    --cli|--test|--check)
      [ "$MODE" = "web" ] || { say "ERROR: elige un solo modo entre --cli, --test y --check." >&2; exit 2; }
      MODE="${arg#--}" ;;
    --live) LIVE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) say "ERROR: argumento desconocido: $arg (usa --help)" >&2; exit 2 ;;
  esac
done
if [ "$LIVE" = 1 ] && { [ "$MODE" = "test" ] || [ "$MODE" = "check" ]; }; then
  say "ERROR: --live no se combina con --test ni --check." >&2
  exit 2
fi

# 1. Python 3.10+ (se prueba que de verdad ejecute: en Windows python3 puede ser un stub).
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 \
     && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PY="$cand"
    break
  fi
done
[ -n "$PY" ] || die "no encontre Python 3.10 o superior (probe python3 y python). Instalalo desde https://www.python.org/downloads/ y vuelve a correr ./run.sh"

# 2. Entorno virtual. Nunca se borra uno existente.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) VENV_PY=".venv/Scripts/python.exe" ;;
  *) VENV_PY=".venv/bin/python" ;;
esac
if [ -e .venv ] && [ ! -x "$VENV_PY" ]; then
  die ".venv existe pero no es de este sistema (falta $VENV_PY). No lo borro: renombralo o eliminalo tu y vuelve a correr ./run.sh"
fi
if [ ! -e .venv ]; then
  say "creando entorno virtual .venv ..."
  if ! "$PY" -m venv .venv; then
    rm -rf .venv # solo el que esta corrida acaba de intentar crear
    die "no pude crear el entorno virtual. En Debian/Ubuntu instala: sudo apt install python3-venv"
  fi
fi
"$VENV_PY" -c 'pass' >/dev/null 2>&1 || die ".venv no ejecuta Python. No lo borro: eliminalo tu y vuelve a correr ./run.sh"

# 3. Dependencias. Siempre se corre pip: si ya estan satisfechas es rapido y no hay estado
#    intermedio que pueda quedar roto.
say "instalando dependencias de requirements.txt ..."
"$VENV_PY" -m pip install -q --disable-pip-version-check -r requirements.txt \
  || die "fallo la instalacion de dependencias. Revisa tu conexion a Internet y vuelve a correr ./run.sh"
if ! "$VENV_PY" -m pip check >/dev/null 2>&1; then
  say "AVISO: pip check reporta dependencias en conflicto. Si algo falla, borra .venv y repite."
fi

# 4. .env: se crea desde el ejemplo si falta y nunca se imprime su contenido.
if [ ! -f .env ]; then
  [ -f .env.example ] || die "falta .env.example, no puedo crear .env"
  cp .env.example .env
  say "cree .env desde .env.example. Sin llave, modo demo local. Editalo para poner tu RETO_API_KEY."
fi

# 5. Estado de la configuracion. El codigo de salida es 10 + 1 (llave valida) + 2 (el .env pide live):
#    asi un fallo de Python (codigo 1) no se confunde con un resultado.
rc=0
"$VENV_PY" -c "import sys; from dotenv import dotenv_values as d; import src.config as c; m=(d('.env').get('GROK_MODE') or 'mock').lower(); sys.exit(10 + (1 if c.is_configured() else 0) + (2 if m in ('live','real','production') else 0))" || rc=$?
[ "$rc" -ge 10 ] || die "no pude leer la configuracion (src/config.py). Revisa .env y requirements.txt"
key_ok=$(( (rc - 10) & 1 ))
env_live=$(( ((rc - 10) >> 1) & 1 ))

# 6. Modo de ejecucion. mock es el defecto; live solo con --live y llave valida.
if [ "$LIVE" = 1 ]; then
  [ "$key_ok" = 1 ] || die "--live necesita una RETO_API_KEY valida con formato pk_ en .env"
  export GROK_MODE=live
  say "MODO LIVE: las llamadas a Grok son reales y consumen el saldo compartido del equipo."
else
  export GROK_MODE=mock
  if [ "$env_live" = 1 ]; then
    say "AVISO: tu .env pide GROK_MODE=live. Este arranque lo ignora y usa mock, costo 0 USD. Usa --live para activarlo."
  fi
  if [ "$key_ok" = 1 ]; then
    say "llave del reto: configurada. Modo: mock, costo 0 USD."
  else
    say "llave del reto: no configurada. Modo: demo local mock, costo 0 USD."
  fi
fi
export PYTHONUTF8=1

# 7. Lanzar el agente.
case "$MODE" in
  check)
    "$VENV_PY" -c "from src.agent.sentinel import SentinelAgent; r = SentinelAgent().process_message('Su cuenta Nequi fue bloqueada. Llame ya al 3001234567 para reactivarla'); print('[run] prueba de humo OK, riesgo: ' + str(r['decision'].get('risk_level')))" \
      || die "la prueba de humo del agente fallo"
    say "listo: entorno verificado. Corre ./run.sh para levantar el agente."
    ;;
  test)
    exec "$VENV_PY" -m pytest tests/ -q
    ;;
  cli)
    exec "$VENV_PY" main.py
    ;;
  web)
    say "levantando la interfaz web. Ctrl+C para detener. Abre en tu navegador la Local URL que aparece abajo, normalmente http://localhost:8501"
    # headless: sin esto Streamlit pide un correo en la primera ejecucion y se queda esperando.
    # address localhost y sin estadisticas: el arranque por defecto no se expone a la red.
    exec "$VENV_PY" -m streamlit run app_streamlit.py \
      --server.headless true --server.address localhost --browser.gatherUsageStats false
    ;;
esac
