#!/bin/sh
# Dump the FilmGraph database to a timestamped gzip, keeping the most recent few.
#
# Credentials come from backend/.env, so there is one place on the box that knows the password.
#
#   ./backup-db.sh              dump to ~/filmgraph-backups
#   ./backup-db.sh /mnt/other   dump somewhere else
#
# This writes to the same disk as the database. That protects against a bad migration or a
# mistaken DELETE, which is what actually happens, but not against losing the volume. Copy
# anything you care about off the box, or take an EBS snapshot as well.
set -e

ENV_FILE="$(dirname "$0")/../backend/.env"
DEST="${1:-$HOME/filmgraph-backups}"
KEEP=7

[ -f "$ENV_FILE" ] || { echo "no .env at $ENV_FILE" >&2; exit 1; }

eval "$(python3 - "$ENV_FILE" <<'PY'
import sys, urllib.parse
url = None
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if line.startswith("DATABASE_URL="):
        url = line.split("=", 1)[1].strip().strip('"').strip("'")
if not url:
    sys.exit("DATABASE_URL not found in .env")
p = urllib.parse.urlsplit(url)
print(f"DB_USER={urllib.parse.unquote(p.username or '')}")
print(f"DB_PASS={urllib.parse.unquote(p.password or '')}")
print(f"DB_HOST={p.hostname or 'localhost'}")
print(f"DB_PORT={p.port or 3306}")
print(f"DB_NAME={(p.path or '/').lstrip('/')}")
PY
)"

mkdir -p "$DEST"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$DEST/${DB_NAME}-${STAMP}.sql.gz"

MYSQL_PWD="$DB_PASS" mysqldump \
    --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
    --single-transaction \
    --default-character-set=utf8mb4 \
    "$DB_NAME" | gzip > "$OUT"

echo "wrote $OUT ($(du -h "$OUT" | cut -f1))"

ls -1t "$DEST"/"${DB_NAME}"-*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do
    rm -f "$old"
    echo "pruned $old"
done
