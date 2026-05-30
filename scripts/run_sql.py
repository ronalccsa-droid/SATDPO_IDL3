from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SECRETS_DIR = ROOT_DIR / ".secrets"
SQL_DIR = ROOT_DIR / "sql"

sys.path.append(str(SECRETS_DIR))
from db_config import get_connection


SQL_FILES = [
    ## "01_bronze_tables_actualizado.sql",
    ## "02_silver_functions_actualizado.sql",
    ## "03_silver_views_actualizado.sql",
    "04_gold_model_actualizado.sql",
    ## "05_quality_checks.sql",
]


def ejecutar_sql_file(conn, file_path):
    print(f"\nEjecutando: {file_path.name}")

    sql = file_path.read_text(encoding="utf-8")

    if not sql.strip():
        print(f"Archivo vacío, se omite: {file_path.name}")
        return

    with conn.cursor() as cur:
        cur.execute(sql)

    print(f"OK: {file_path.name}")


def main():
    conn = get_connection()

    try:
        with conn:
            for sql_file in SQL_FILES:
                file_path = SQL_DIR / sql_file

                if not file_path.exists():
                    print(f"No existe el archivo: {file_path}")
                    continue

                ejecutar_sql_file(conn, file_path)

        print("\nProceso SQL completado correctamente.")

    except Exception as e:
        print("\nError ejecutando SQL:")
        print(e)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()