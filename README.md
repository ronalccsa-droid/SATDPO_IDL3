<div align="center">

# SATDPO — Sistema de Alerta Temprana de Desempeño del Personal Operativo

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-Cloud-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Architecture](https://img.shields.io/badge/Arquitectura-Medallion-F59E0B?style=for-the-badge)](#arquitectura)
[![Status](https://img.shields.io/badge/Estado-Activo-22C55E?style=for-the-badge)](#)

> **Proyecto PP2B · Big Data Aplicada · Instituto Continental**

Pipeline de datos orientado al análisis del desempeño del personal operativo. Organiza, transforma y consolida información para detectar de manera temprana problemas de rendimiento, clima laboral, adherencia, calidad, capacitación e incidencias.

</div>

---

## Arquitectura Medallion

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                             │
│  CSV Asesores · CSV Reclutamiento · CSV Desempeño · CSV Turnos      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BRONZE  ·  Carga Raw                                               │
│  Datos sin transformar, trazabilidad completa, timestamps de carga  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────────────┐
│  META  ·  Control       │   │  SILVER  ·  Transformación          │
│  Auditoría de cargas    │   │  Limpieza, joins, estandarización   │
│  Logs de ejecución      │   │  Indicadores calculados             │
└─────────────────────────┘   └──────────────┬──────────────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────────────┐
                             │  GOLD  ·  Modelo Dimensional           │
                             │  Star Schema · Tablas analíticas       │
                             │  fact_reclutamiento                    │
                             │  fact_desempeno_mensual                │
                             └───────────────────────────────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología | Rol |
|------|-----------|-----|
| Lenguaje | Python 3.10+ | Orquestación y transformaciones |
| Base de datos | PostgreSQL 15 | Almacenamiento estructurado |
| Cloud | Supabase | Hosting y acceso remoto |
| Procesamiento | Pandas | Manipulación de DataFrames |
| Exploración | Jupyter Notebook | Análisis iterativo |
| Conectividad | psycopg2 | Driver PostgreSQL |
| Control | SQL + SPs | Stored Procedures por capa |
| Versiones | GitHub | Control de código fuente |

---

## Modelo Dimensional (Gold)

```
                    ┌──────────────────┐
                    │   dim_tiempo     │
                    │  ─────────────  │
                    │  id_tiempo (PK) │
                    │  anio           │
                    │  mes            │
                    │  trimestre      │
                    └────────┬─────────┘
                             │
┌──────────────────┐         │         ┌──────────────────────────┐
│   dim_asesor     │         │         │   fact_reclutamiento     │
│  ─────────────  │◄────────┼────────►│  ──────────────────────  │
│  id_asesor (PK) │         │         │  id_reclutamiento (PK)   │
│  nombre         │         │         │  id_asesor (FK)          │
│  cargo          │         │         │  id_tiempo (FK)          │
│  area           │         │         │  postulantes             │
│  sede           │         │         │  contratados             │
└──────────────────┘         │         │  tasa_conversion         │
                             │         └──────────────────────────┘
                             │
                    ┌────────┴───────────────────────┐
                    │   fact_desempeno_mensual        │
                    │  ─────────────────────────────  │
                    │  id_desempeno (PK)              │
                    │  id_asesor (FK)                 │
                    │  id_tiempo (FK)                 │
                    │  score_calidad                  │
                    │  adherencia_horaria             │
                    │  incidencias                    │
                    │  capacitaciones_completadas     │
                    └─────────────────────────────────┘
```

---

## Entidades del Sistema

| # | Entidad | Descripción |
|---|---------|-------------|
| 1 | `asesor` | Personal operativo evaluado |
| 2 | `reclutamiento` | Proceso de incorporación de personal |
| 3 | `desempeno_mensual` | Métricas de rendimiento por periodo |
| 4 | `turno` | Asignación horaria y adherencia |
| 5 | `capacitacion` | Formación completada por asesor |
| 6 | `incidencia` | Eventos críticos registrados |
| 7 | `clima_laboral` | Indicadores de bienestar |
| 8 | `auditoria_carga` | Trazabilidad del pipeline |

---

## Estructura del Proyecto

```
SATDPO_IDL3/
├── data/
│   ├── raw/                    # Archivos CSV fuente
│   └── processed/              # Datos transformados
├── notebooks/
│   ├── 01_bronze_load.ipynb    # Carga a capa Bronze
│   ├── 02_silver_transform.ipynb # Transformaciones Silver
│   └── 03_gold_model.ipynb     # Modelo dimensional Gold
├── sql/
│   ├── bronze/                 # DDL y SPs Bronze
│   ├── silver/                 # DDL y SPs Silver
│   ├── gold/                   # DDL y SPs Gold
│   └── meta/                   # Tablas de control
├── src/
│   ├── pipeline.py             # Orquestador principal
│   ├── loaders.py              # Carga desde CSV
│   ├── transformers.py         # Lógica de transformación
│   └── validators.py           # Validación de datos
├── requirements.txt
└── README.md
```

---

## Ejecución del Pipeline

```bash
# 1. Clonar el repositorio
git clone https://github.com/ronalccsa-droid/SATDPO_IDL3.git
cd SATDPO_IDL3

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
export DB_HOST=your_supabase_host
export DB_PORT=5432
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASS=your_password

# 4. Ejecutar carga Bronze
python src/pipeline.py --layer bronze

# 5. Ejecutar transformaciones Silver
python src/pipeline.py --layer silver

# 6. Construir modelo Gold
python src/pipeline.py --layer gold

# 7. Validar integridad
python src/validators.py --full-check

# 8. Revisar logs de auditoría en schema meta
psql -c "SELECT * FROM meta.auditoria_carga ORDER BY fecha_carga DESC LIMIT 10;"
```

---

## Flujo de Datos

```
CSV Sources
    │
    ▼
[Bronze] ──► Datos raw con timestamps y trazabilidad
    │
    ├──► [Meta] ──► Registro de ejecución y auditoría
    │
    ▼
[Silver] ──► Limpieza · Joins · Indicadores calculados
    │
    ▼
[Gold] ──► Star Schema listo para análisis y reportes
```

---

## Capas del Pipeline

### Bronze — Carga Raw
- Ingesta directa desde archivos CSV sin modificaciones
- Agrega campos de control: `fecha_carga`, `archivo_origen`, `id_carga`
- Preserva datos originales para trazabilidad y reprocesamiento

### Meta — Control de Ejecución
- Registra cada ejecución del pipeline
- Almacena métricas: filas procesadas, errores, duración
- Permite reejecutar cargas fallidas de forma selectiva

### Silver — Transformación
- Limpieza de nulos, duplicados y valores fuera de rango
- Estandarización de tipos y formatos
- Cálculo de indicadores intermedios
- Joins entre entidades operativas

### Gold — Modelo Analítico
- Esquema estrella optimizado para consultas analíticas
- Tablas de hechos: `fact_reclutamiento`, `fact_desempeno_mensual`
- Dimensiones: `dim_asesor`, `dim_tiempo`
- Base para dashboards y alertas tempranas

---

<div align="center">

**Instituto Continental · 2026**

</div>
