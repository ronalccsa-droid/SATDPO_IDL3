import io
import sys
from pathlib import Path

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


ROOT_DIR = Path(__file__).resolve().parents[1]
SECRETS_DIR = ROOT_DIR / ".secrets"

OAUTH_CLIENT_FILE = SECRETS_DIR / "google_oauth_client.json"
TOKEN_FILE = SECRETS_DIR / "google_token.json"

sys.path.append(str(SECRETS_DIR))
from db_config import get_connection


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


# ============================================================
# CARGA BRONZE ESTRICTA
# - No inventa columnas.
# - No rellena datos faltantes.
# - No convierte faltantes en texto "NaN".
# - Carga el dato tal como llega del archivo origen, como texto.
# - Si el archivo de Drive no tiene los encabezados esperados, se detiene.
# ============================================================

TABLAS = {
    "asesor": {
        "drive_id": "1ju_zxAXjQHKuY0NQ0DQFnQxqHefX1fr4gekIsQ55Fhc",
        "drive_name": "Tabla_asesores",
        "supabase_table": "bronze.asesor",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
        },
    },
    "horas": {
        "drive_id": "1YED1_sywEWtnJ3Pk-NFWCgOtFt1E5wF1",
        "drive_name": "data_sintetica_horas_conexion_mensual",
        "supabase_table": "bronze.horas_conexion_mes",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "anio": "anio",
            "mes": "mes",
            "horas_conexion_acumulado": "horas_conexion_acumulado",
            "cumplimiento_percent": "cumplimiento_pct",
            "nivel_indicador": "nivel_indicador",
        },
    },
    "aprobacion": {
        "drive_id": "1GNN_J4stzgos0FMMtuodadxnBLVa-Kl08fHA4L4crPs",
        "drive_name": "data_sintetica_aprobacion_inmediata",
        "supabase_table": "bronze.aprobacion_inmediata",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "indicador": "indicador",
            "unidad_medida": "unidad_medida",
            "peso_tablero_%": "peso_tablero_pct",
            "%_aprobacion_inmediata": "aprobacion_inmediata_pct",
            "nivel_cumplimiento": "nivel_cumplimiento",
            "resultado_bono": "resultado_bono",
            "aporte_al_tablero_%": "aporte_al_tablero_pct",
            "anio": "anio",
            "mes": "mes",
        },
    },
    "calidad": {
        "drive_id": "1teUlTRJhiZw2FR1rp88nXp7I6Zj1O0XnQ17-b-VLK2k",
        "drive_name": "data_sintetica_Calidad",
        "supabase_table": "bronze.calidad",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "anio": "anio",
            "mes": "mes",
            "nota_examen": "nota_examen",
            "calidad_%": "calidad_pct",
            "nivel_indicador": "nivel_indicador",
        },
    },
    "nps": {
        "drive_id": "1LjIm0UvWGl315D-h0GS7vGnOW41FxjrZEHl0ETK_Y5o",
        "drive_name": "data_sintetica_NPS",
        "supabase_table": "bronze.nps",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "anio": "anio",
            "mes": "mes",
            "NPS_%": "nps_pct",
            "nivel_indicador": "nivel_indicador",
        },
    },
    "crm": {
        "drive_id": "18brVyfwzkOgD9NxaULHrSqNXH_54U56grnPxde1aHf4",
        "drive_name": "data_sintetica_tipificacionCRM",
        "supabase_table": "bronze.crm",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "anio": "anio",
            "mes": "mes",
            "Atendidas": "atendidas",
            "Reg_CRM": "reg_crm",
            "TIP_%": "tip_pct",
        },
    },
    "tmo": {
        "drive_id": "1y7wtJ9JIit1p_-IPY9vOdgUId2OUtciuB5VU2HYCLvI",
        "drive_name": "data_sintetica_TMO",
        "supabase_table": "bronze.tmo",
        "column_map": {
            "asesor": "asesor",
            "DNI": "dni",
            "area": "area",
            "sede": "sede",
            "fecha_ingreso": "fecha_ingreso",
            "estado_trabajador": "estado_trabajador",
            "turno": "turno",
            "anio": "anio",
            "mes": "mes",
            "TMO_minutos": "tmo_minutos",
            "nivel_indicador": "nivel_indicador",
        },
    },
}


def get_drive_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_FILE,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds)


def obtener_archivo(service, config):
    drive_id = config["drive_id"]
    drive_name = config["drive_name"]

    try:
        archivo = service.files().get(
            fileId=drive_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        ).execute()

        print(f"Archivo encontrado por ID: {archivo['name']} | {archivo['mimeType']}")
        return archivo

    except Exception as e:
        print(f"No se pudo acceder por ID: {drive_id}")
        print(f"Detalle: {e}")
        print(f"Intentando buscar por nombre: {drive_name}")

    response = service.files().list(
        q=f"name = '{drive_name}' and trashed = false",
        fields="files(id, name, mimeType)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora="allDrives",
        pageSize=100,
    ).execute()

    archivos = response.get("files", [])

    print("Coincidencias por nombre:")
    for archivo in archivos:
        print(f"- {archivo['name']} | ID: {archivo['id']} | {archivo['mimeType']}")

    if not archivos:
        raise FileNotFoundError(f"No se encontró el archivo: {drive_name}")

    return archivos[0]


def descargar_archivo(service, archivo):
    buffer = io.BytesIO()

    if archivo["mimeType"] == "application/vnd.google-apps.spreadsheet":
        request = service.files().export_media(
            fileId=archivo["id"],
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        request = service.files().get_media(
            fileId=archivo["id"],
            supportsAllDrives=True,
        )

    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer


def leer_dataframe(buffer, archivo):
    nombre = archivo["name"].lower()
    mime_type = archivo["mimeType"]

    if nombre.endswith(".csv") or mime_type == "text/csv":
        return pd.read_csv(
            buffer,
            dtype=str,
            keep_default_na=False,
        )

    return pd.read_excel(
        buffer,
        dtype=str,
        keep_default_na=False,
    )


def preparar_dataframe(df, config, nombre_archivo):
    column_map = config["column_map"]

    # Se limpian solo los nombres de columnas para evitar errores por espacios accidentales.
    # Los valores se cargan tal como llegan del archivo origen.
    df.columns = df.columns.astype(str).str.strip()

    columnas_origen = list(column_map.keys())
    faltantes_origen = [col for col in columnas_origen if col not in df.columns]

    if faltantes_origen:
        print("\nColumnas encontradas en el archivo origen:")
        print(list(df.columns))
        print("\nColumnas esperadas para esta tabla:")
        print(columnas_origen)
        raise ValueError(
            "El archivo de Drive no coincide con la estructura Bronze esperada. "
            f"Faltan columnas de origen: {faltantes_origen}"
        )

    # Se seleccionan solo las columnas definidas para la tabla Bronze.
    # No se crean columnas faltantes, porque Bronze debe reflejar el origen.
    df = df[columnas_origen].copy()
    df = df.rename(columns=column_map)

    # Capa Bronze: todo se carga como texto, sin transformar el contenido.
    # Con keep_default_na=False, las celdas vacías llegan como "" y no como NaN.
    for col in df.columns:
        df[col] = df[col].astype(str)

    df["archivo_origen"] = str(nombre_archivo)

    return df


def cargar_bronze(df, tabla_destino):
    columnas = list(df.columns)
    placeholders = ", ".join(["%s"] * len(columnas))
    columnas_sql = ", ".join(columnas)

    sql_truncate = f"truncate table {tabla_destino};"

    sql_insert = f"""
        insert into {tabla_destino} ({columnas_sql})
        values ({placeholders})
    """

    rows = df.values.tolist()

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                print(f"Limpiando tabla destino: {tabla_destino}")
                cur.execute(sql_truncate)

                print(f"Insertando {len(rows)} filas en {tabla_destino}")
                cur.executemany(sql_insert, rows)
    finally:
        conn.close()


def importar_tabla(service, nombre_config):
    config = TABLAS[nombre_config]

    print(f"\nImportando: {nombre_config}")

    archivo = obtener_archivo(service, config)
    buffer = descargar_archivo(service, archivo)
    df = leer_dataframe(buffer, archivo)

    df_limpio = preparar_dataframe(df, config, archivo["name"])

    cargar_bronze(df_limpio, config["supabase_table"])

    print(f"OK: {len(df_limpio)} filas cargadas en {config['supabase_table']}")


def main():
    if len(sys.argv) < 2:
        opciones = ", ".join(TABLAS.keys())
        print(f"Uso: python scripts/importar_drive_bronze.py [{opciones}|all]")
        return

    objetivo = sys.argv[1].lower()
    service = get_drive_service()

    if objetivo == "all":
        for nombre_config in TABLAS:
            importar_tabla(service, nombre_config)
    elif objetivo in TABLAS:
        importar_tabla(service, objetivo)
    else:
        opciones = ", ".join(TABLAS.keys())
        raise ValueError(
            f"Tabla no reconocida: {objetivo}. Opciones: {opciones}, all"
        )


if __name__ == "__main__":
    main()
