#!/bin/bash
set -euo pipefail

if [ -z "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  exit 0
fi

IFS=',' read -ra DATABASES <<< "${POSTGRES_MULTIPLE_DATABASES}"

for database in "${DATABASES[@]}"; do
  database="$(echo "${database}" | xargs)"

  if [ -n "${database}" ]; then
    psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "postgres" <<-EOSQL
      CREATE DATABASE ${database};
EOSQL
  fi
done
