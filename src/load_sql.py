"""Builds data/sales.db from a MySQL-style .sql script.
Run from the project folder:
  python src/load_sql.py                      -> finds the one .sql file inside the data folder
  python src/load_sql.py data/brightmart_db.sql   -> use a specific file"""
import glob
import os
import re
import sqlite3
import sys

DATA_DIR_NAME = "data"   # change this if your data folder has a different name

# Project folder = the folder above src/, wherever you run the command from
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, DATA_DIR_NAME)
DB_PATH = os.path.join(DATA_DIR, "sales.db")
os.makedirs(DATA_DIR, exist_ok=True)

if len(sys.argv) > 1:
    SQL_FILE = sys.argv[1]
else:
    found = glob.glob(os.path.join(DATA_DIR, "**", "*.sql"), recursive=True)
    if len(found) != 1:
        print("Found %d .sql files in %s." % (len(found), DATA_DIR))
        print("Run:  python src/load_sql.py path/to/your_file.sql")
        for f in found:
            print("  ", f)
        sys.exit(1)
    SQL_FILE = found[0]
print("Using script:", SQL_FILE)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)      # start fresh each run

with open(SQL_FILE, encoding="utf-8") as f:
    sql = f.read()

# 1. Remove statements SQLite doesn't have
sql = re.sub(r"(?im)^\s*(CREATE\s+DATABASE|DROP\s+DATABASE|USE|LOCK\s+TABLES|UNLOCK\s+TABLES|DELIMITER)\b[^;\n]*;?", "", sql)
sql = re.sub(r"(?im)^\s*SET\s+(@|FOREIGN_KEY_CHECKS|SQL_MODE|NAMES|TIME_ZONE|UNIQUE_CHECKS|SQL_)[^;]*;", "", sql)

# 2. Remove table options like ") ENGINE=InnoDB DEFAULT CHARSET=utf8;"
sql = re.sub(r"(?is)\)\s*(ENGINE|AUTO_INCREMENT|DEFAULT\s+CHARSET|CHARSET|COLLATE)\s*=[^;]*;", ");", sql)

# 3. Remove other MySQL-only column bits
sql = re.sub(r"(?i)\bAUTO_INCREMENT\b", "", sql)
sql = re.sub(r"(?i)\bUNSIGNED\b", "", sql)
sql = re.sub(r"(?i)\bCOMMENT\s+'[^']*'", "", sql)
sql = re.sub(r"(?i)\bENUM\s*\([^)]*\)", "TEXT", sql)

# 4. Run one statement at a time so any error is easy to find
conn = sqlite3.connect(DB_PATH)
buffer, ok, count = "", True, 0
for line in sql.splitlines(keepends=True):
    buffer += line
    if sqlite3.complete_statement(buffer):
        stmt, buffer = buffer.strip(), ""
        if not stmt:
            continue
        try:
            conn.execute(stmt)
            count += 1
        except sqlite3.Error as e:
            ok = False
            print("FAILED:", e)
            print("----- statement -----")
            print(stmt[:600])
            break

conn.commit()
if ok:
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"sales.db created ({count} statements run)")
    for t in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {n} rows")
else:
    print("Stopped because of the error above.")
conn.close()