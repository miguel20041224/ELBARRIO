#!/usr/bin/env bash
# Smoke test del flujo de red frontend -> backend.
#
# Comprueba lo mismo que comprueba el navegador: preflight CORS, cabecera
# Access-Control-Allow-Origin en la respuesta real, y que un origen ajeno no la
# recibe. Sirve igual contra localhost que contra el despliegue de Render.
#
#   ./scripts/smoke-network.sh
#   ./scripts/smoke-network.sh https://elbarrio-api.onrender.com https://elbarrio.vercel.app
#
# Solo lee y crea una carrera de prueba; no borra nada.
set -uo pipefail

API="${1:-http://localhost:8000}"
ORIGIN="${2:-http://localhost:4173}"
STRANGER="https://sitio-ajeno.example"

API="${API%/}"
ORIGIN="${ORIGIN%/}"

pass=0
fail=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    printf '  \033[32mOK\033[0m   %s\n' "$name"
    pass=$((pass + 1))
  else
    printf '  \033[31mFALLA\033[0m %s\n       esperado: %s\n       obtenido: %s\n' \
      "$name" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# Devuelve el valor de access-control-allow-origin, o "(sin cabecera)".
allow_origin_header() {
  local value
  value=$(grep -i '^access-control-allow-origin:' <<<"$1" | tr -d '\r' | cut -d' ' -f2-)
  echo "${value:-(sin cabecera)}"
}

echo "API:    $API"
echo "Origin: $ORIGIN"
echo

echo "[1] Salud del backend"
status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$API/health")
check "GET /health responde 200" "200" "$status"

echo "[2] Preflight CORS desde el frontend"
headers=$(curl -s -D - -o /dev/null -X OPTIONS "$API/api/careers" \
  -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" --max-time 30)
check "preflight aprobado" "$ORIGIN" "$(allow_origin_header "$headers")"

echo "[3] Preflight desde un origen ajeno"
headers=$(curl -s -D - -o /dev/null -X OPTIONS "$API/api/careers" \
  -H "Origin: $STRANGER" \
  -H "Access-Control-Request-Method: POST" --max-time 30)
check "origen ajeno rechazado" "(sin cabecera)" "$(allow_origin_header "$headers")"

echo "[4] Crear carrera (POST /api/careers)"
body=$(curl -s -D /tmp/elbarrio-smoke-headers -X POST "$API/api/careers" \
  -H "Origin: $ORIGIN" -H "Content-Type: application/json" --max-time 60 \
  -d '{"mode":"player","draft":{"firstName":"Smoke","lastName":"Test","birthCountry":"AR","startingLeague":"col-primera-a","position":"CAM","shirtNumber":10,"preferredFoot":"left","age":19,"height":175,"weight":70}}')
check "respuesta con cabecera CORS" "$ORIGIN" \
  "$(allow_origin_header "$(cat /tmp/elbarrio-smoke-headers)")"

career_id=$(python3 -c 'import json,sys;print(json.load(sys.stdin).get("id",""))' <<<"$body" 2>/dev/null)
if [[ -z "$career_id" ]]; then
  printf '  \033[31mFALLA\033[0m no se pudo leer el id de la carrera creada\n'
  fail=$((fail + 1))
else
  echo "[5] Releer carrera (GET /api/careers/$career_id)"
  headers=$(curl -s -D - -o /tmp/elbarrio-smoke-body -H "Origin: $ORIGIN" \
    --max-time 30 "$API/api/careers/$career_id")
  check "responde 200" "200" "$(head -1 <<<"$headers" | tr -d '\r' | cut -d' ' -f2)"
  check "respuesta con cabecera CORS" "$ORIGIN" "$(allow_origin_header "$headers")"
  returned_id=$(python3 -c 'import json,sys;print(json.load(sys.stdin).get("id",""))' \
    < /tmp/elbarrio-smoke-body 2>/dev/null)
  check "devuelve la misma carrera" "$career_id" "$returned_id"
fi

echo "[6] Carrera inexistente"
# El frontend distingue este 404 (carrera borrada del servidor) de un fallo de
# red: con 404 limpia el estado local, con fallo de red lo conserva.
status=$(curl -s -o /dev/null -w '%{http_code}' -H "Origin: $ORIGIN" \
  --max-time 30 "$API/api/careers/no-existe-12345")
check "GET de id desconocido responde 404" "404" "$status"

rm -f /tmp/elbarrio-smoke-headers /tmp/elbarrio-smoke-body

echo
if [[ $fail -eq 0 ]]; then
  printf '\033[32m%d comprobaciones OK\033[0m\n' "$pass"
  exit 0
fi
printf '\033[31m%d fallos\033[0m de %d comprobaciones\n' "$fail" "$((pass + fail))"
exit 1
