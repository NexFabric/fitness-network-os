#!/usr/bin/env bash
# Disaster Recovery (DR) Database Restore Drill Script for GymClubNex
set -euo pipefail

HOST="${PGHOST:-localhost}"
PORT="${PGPORT:-5433}"
USER="${PGUSER:-postgres}"
DB_NAME="${PGDATABASE:-fitness_os}"
RESTORE_DB_NAME="fitness_os_dr_drill_$(date +%s)"
DUMP_FILE="/tmp/fitness_os_dr_backup_$(date +%s).sql"

echo "=== GymClubNex DR Restore Drill Starting ==="
echo "Host: ${HOST}:${PORT}"
echo "Source Database: ${DB_NAME}"
echo "Target Restore Database: ${RESTORE_DB_NAME}"

# Step 1: Dump Source Database
echo "--> Creating full schema & data dump..."
PGPASSWORD="${PGPASSWORD:-postgres}" pg_dump -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${DB_NAME}" -F p -f "${DUMP_FILE}"

if [ ! -f "${DUMP_FILE}" ] || [ ! -s "${DUMP_FILE}" ]; then
  echo "FAIL: Dump file was not created or is empty!"
  exit 1
fi
echo "Dump file size: $(du -h "${DUMP_FILE}" | cut -f1)"

# Step 2: Create Target DR Test Database
echo "--> Creating target test database ${RESTORE_DB_NAME}..."
PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d postgres -c "CREATE DATABASE ${RESTORE_DB_NAME};"

# Step 3: Restore Dump to Target DR Test Database
echo "--> Restoring dump into ${RESTORE_DB_NAME}..."
PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -f "${DUMP_FILE}" > /dev/null

# Step 4: Verification of Integrity & Table Row Counts
echo "--> Verifying database table counts..."
MEMBER_COUNT=$(PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM members;" | tr -d ' ')
TENANT_COUNT=$(PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${RESTORE_DB_NAME}" -t -c "SELECT count(*) FROM tenants;" | tr -d ' ')

echo "Verification Results:"
echo " - Tenants count: ${TENANT_COUNT}"
echo " - Members count: ${MEMBER_COUNT}"

# Step 5: Cleanup Temporary DR Database & Backup File
echo "--> Cleaning up DR test database and temporary dump file..."
PGPASSWORD="${PGPASSWORD:-postgres}" psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d postgres -c "DROP DATABASE ${RESTORE_DB_NAME};"
rm -f "${DUMP_FILE}"

echo "=== DR RESTORE DRILL PASSED SUCCESSFULLY ==="
