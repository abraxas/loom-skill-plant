#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-loom-190-skill-plant}"
export LOOM_URL="${LOOM_URL:-http://127.0.0.1:18640}"

PIN_TAG="v1.9.0"
PIN_SHA="a3050669f5b4c83210a44ed4346f17e01641e82f"
SRC_DEST="src-v1.9.0"
LABEL="LOOM-190-SKILL-PLANT"
WITNESS="LOOM-190-SKILL-PLANT-WITNESS"

down() {
  echo "== docker compose down -v =="
  docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans || true
}


copy_pin() {
  local tmp got
  tmp="$(mktemp -d)"
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "${PIN_TAG}" --filter=blob:none --sparse \
    https://github.com/awslabs/loom.git "${tmp}"
  git -C "${tmp}" sparse-checkout set backend
  got="$(git -C "${tmp}" rev-parse HEAD)"
  echo "checkout tag=${PIN_TAG} sha=${got} expect=${PIN_SHA}"
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    GIT_TERMINAL_PROMPT=0 git -C "${tmp}" fetch --depth 1 origin "${PIN_SHA}"
    git -C "${tmp}" checkout -f "${PIN_SHA}"
    got="$(git -C "${tmp}" rev-parse HEAD)"
    echo "checkout-forced sha=${got}"
  fi
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    rm -rf "${tmp}"
    echo "FAIL ${LABEL} unexpected-commit got=${got} expect=${PIN_SHA}" | tee poc-last-run.txt
    exit 1
  fi
  rm -rf "src-v1.9.0"
  mkdir -p "src-v1.9.0/backend"
  cp -a "${tmp}/backend/app" "src-v1.9.0/backend/"
  cp -a "${tmp}/backend/etc" "src-v1.9.0/backend/"
  cp "${tmp}/backend/requirements.txt" "src-v1.9.0/backend/"
  rm -rf "${tmp}"
  find "src-v1.9.0" -type d -name '__pycache__' -exec rm -rf {} + || true
  echo "checkout-ok tag=${PIN_TAG} sha=${got} source=public-tag"
}

echo "== pin ${PIN_TAG} ${PIN_SHA} =="
copy_pin
if [[ ! -f "${SRC_DEST}/backend/app/routers/registry.py" ]]; then
  echo "FAIL ${LABEL} missing-app-tree ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if [[ ! -f "${SRC_DEST}/backend/app/services/registry.py" ]]; then
  echo "FAIL ${LABEL} missing-registry-service ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi

echo "== docker compose down (clean) =="
down

echo "== docker compose up --build =="
up_ok=0
for attempt in 1 2 3 4 5; do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" up --build -d; then
    up_ok=1
    break
  fi
  echo "compose-up-retry attempt=${attempt}"
  sleep 20
  down
done
if [[ "${up_ok}" != 1 ]]; then
  echo "FAIL ${LABEL} compose up failed ${WITNESS}" | tee poc-last-run.txt
  down
  exit 1
fi

echo "== wait /health =="
ready=0
code=""
for i in $(seq 1 90); do
  code="$(curl -sS -o /tmp/loom-190-skill-plant-health.json -w '%{http_code}' --max-time 5 "${LOOM_URL}/health" || true)"
  if [[ "${code}" == "200" ]]; then
    ready=1
    echo "health-ready name=loom attempt=${i} http=${code}"
    break
  fi
  echo "health-wait name=loom attempt=${i} http=${code}"
  sleep 2
done
if [[ "${ready}" != 1 ]]; then
  echo "FAIL ${LABEL} loom not ready http=${code} ${WITNESS}" | tee poc-last-run.txt
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --tail=160 || true
  down
  exit 1
fi

echo "== poc.py =="
set +e
docker compose -p "${COMPOSE_PROJECT_NAME}" exec -T \
  -e LOOM_URL=http://127.0.0.1:8000 \
  loom python /lab/poc.py | tee poc-last-run.txt
rc=${PIPESTATUS[0]}
set -e
if ! grep -qE "FAIL ${LABEL}|SUCCESS ${LABEL}" poc-last-run.txt; then
  echo "FAIL ${LABEL} poc-no-verdict exit=${rc} ${WITNESS}" >> poc-last-run.txt
  rc=1
fi

down
exit "${rc}"
