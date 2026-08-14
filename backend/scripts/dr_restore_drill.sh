#!/usr/bin/env bash
# Disaster Recovery (DR) Database Restore Drill Script for GymClubNex
set -euo pipefail

HOST="${PGHOST:-localhost}"
PORT="${PGPORT:-5433}"
USER="${PGUSER:-postgres}"
DB_NAME="${PGDATABASE:-fitness_os}"
RESTORE_DB_NAME="fitness_os_dr_drill_$(date +%s)"
DUMP_FILE="/tmp/fitness_os_dr_backup_$(date +%s).sql"

# Check if fitness-os-postgres container is running
USE_DOCKER_EXEC=0
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "fitness-os-postgres"; then
  USE_DOCKER_EXEC=1
fi

echo "=== GymClubNex DR Restore Drill Starting ==="
echo "Host: ${HOST}:${PORT} (Docker exec: ${USE_DOCKER_EXEC})"
echo "Source Database: ${DB_NAME}"
echo "Target Restore Database: ${RESTORE_DB_NAME}"

# Step 1: Dump Source Database
echo "--> Creating full schema & data dump..."
if [ "${USE_DOCKER_EXEC}" = "1" ]; then
  docker exec -e PGPASSWORD=postgres fitness-os-postgres pg_dump -U "${USER}" -d "${DB_NAME}" -F p > "${DUMP_FILE}"
else
  PGPASSWORD="${PGPASSWORD:-postgres}" pg_dump -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${DB_NAME}" -F p -f "${DUMP_FILE}"
fi

if [ ! -f "${DUMP_FILE}" ] || [ ! -s "${DUMP_FILE}" ]; then
  echo "FAIL: Dump file was not created or is empty!"
  exit 1
fi
echo "Dump file size: $(du -h "${DUMP_FILE}" | cut -f1)"

# Step 2: Create Target DR Test Database
echo "--> Creating target test database ${RESTORE_DB_NAME}..."
if [ "${USE_DOCKER_EXEC}" = "1" ]; then
  docker exec -e PGPASSWORD=postgres fitness-os-postgres psql -U "${USER}" -d postgres -c "CREATE DATABASE ${RESTORE_DB_NAME};"
  echo "--> Restoring dump into ${RESTORE_DB_NAME}..."
  docker exec -i -e PGPASSWORD=postgres fitness-os-postgres psql -U "${USER}" -d "${RESTORE_DB_NAME}" < "${DUMP_FILE}" > /dev/null
  echo "--> Verifying database table counts..."
  MEMBER_COUNT=$(docker exec -e PGPASSWORD=postgres fitness-os-postgres psql -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM members;" | tr -d ' \r\n')
  TENANT_COUNT=$(docker exec -e PGPASSWORD=postgres fitness-os-postgres psql -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM tenants;" | tr -d ' \r\n')
  echo "Verification Results:"
  echo " - Tenants count: ${TENANT_COUNT}"
  echo " - Members count: ${MEMBER_COUNT}"
  echo "--> Cleaning up DR test database and temporary dump file..."
  docker exec -e PGPASSWORD=postgres fitness-os-postgres psql -U "${USER}" -d postgres -c "DROP DATABASE ${RESTORE_DB_NAME};"
else
  PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d postgres -c "CREATE DATABASE ${RESTORE_DB_NAME};"
  echo "--> Restoring dump into ${RESTORE_DB_NAME}..."
  PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -f "${DUMP_FILE}" > /dev/null
  echo "--> Verifying database table counts..."
  MEMBER_COUNT=$(PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM members;" | tr -d ' \r\n')
  TENANT_COUNT=$(PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM tenants;" | tr -d ' \r\n')
  echo "Verification Results:"
  echo " - Tenants count: ${TENANT_COUNT}"
  echo " - Members count: ${MEMBER_COUNT}"
  echo "--> Cleaning up DR test database and temporary dump file..."
  PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d postgres -c "DROP DATABASE ${RESTORE_DB_NAME};"
fi
rm -f "${DUMP_FILE}"

echo "=== DR RESTORE DRILL PASSED SUCCESSFULLY ==="
