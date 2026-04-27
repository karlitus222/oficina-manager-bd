import os
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from waitress import serve


ROOT = Path(__file__).resolve().parent.parent
DDL_DB = ROOT / "ddl" / "00_create_database.sql"
DDL_SCHEMA = ROOT / "ddl" / "01_create_schema.sql"
DML_SEED = ROOT / "dml" / "01_seed_data.sql"


def connect(dbname: str):
    return psycopg2.connect(
        host=os.getenv("PGHOST", "db"),
        port=os.getenv("PGPORT", "5432"),
        dbname=dbname,
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        cursor_factory=RealDictCursor,
    )


def wait_for_postgres(max_attempts: int = 30):
    last_error = None
    for _ in range(max_attempts):
        try:
            conn = connect("postgres")
            conn.close()
            return
        except Exception as error:  # pragma: no cover
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"PostgreSQL nao respondeu a tempo: {last_error}")


def database_exists() -> bool:
    conn = connect("postgres")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'oficina_db'")
            return cursor.fetchone() is not None
    finally:
        conn.close()


def create_database():
    sql = DDL_DB.read_text(encoding="utf-8")
    conn = connect("postgres")
    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql)
    finally:
        conn.close()


def schema_ready() -> bool:
    conn = connect("oficina_db")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'usuarios'
                """
            )
            return cursor.fetchone() is not None
    finally:
        conn.close()


def run_sql_file(path: Path):
    sql = path.read_text(encoding="utf-8")
    conn = connect("oficina_db")
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
    finally:
        conn.close()


def initialize_database():
    wait_for_postgres()
    if not database_exists():
        create_database()
    if not schema_ready():
        run_sql_file(DDL_SCHEMA)
        run_sql_file(DML_SEED)


def main():
    initialize_database()
    os.environ["DATABASE_URL"] = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@db:5432/oficina_db"
    )
    from src.app import app

    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))


if __name__ == "__main__":
    main()
