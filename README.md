# 📊 PP2B - SATDPO

## Sistema de Alerta Temprana de Desempeño del Personal Operativo

Proyecto desarrollado para el curso **Big Data Aplicada** del **Instituto Continental**.

El proyecto tiene como finalidad implementar un **pipeline de datos** orientado al análisis del desempeño del personal operativo, permitiendo organizar, transformar y consolidar información relevante para detectar de manera temprana posibles problemas de rendimiento, clima laboral, adherencia, calidad, capacitación e incidencias.

La solución fue construida sobre una **arquitectura Medallion**, utilizando las capas **Bronze, Silver y Gold**, además de un esquema **Meta** para el control técnico de cargas y ejecución del pipeline.

---

# 🎯 Objetivo del proyecto

Desarrollar una solución de datos que permita:

- Integrar múltiples fuentes de información operativa.
- Construir un pipeline de procesamiento en varias capas.
- Estandarizar y transformar datos para análisis.
- Consolidar indicadores de desempeño del personal.
- Generar una base analítica para sistemas de alerta temprana.

---

# 🏗 Arquitectura del proyecto

El flujo de datos implementado sigue la siguiente lógica:

```text
Archivos fuente / datasets
          │
          ▼
     Python / Notebook
          │
          ▼
   PostgreSQL en Supabase
          │
          ▼
     Bronze Layer
          │
          ▼
      Meta Layer
          │
          ▼
     Silver Layer
          │
          ▼
      Gold Layer
          │
          ▼
Modelo analítico final
```

## Capas implementadas

### 🥉 Bronze
Contiene la información inicial cargada desde los archivos fuente hacia la base de datos.  
En esta etapa se almacenan las tablas base del proyecto.

### ⚙️ Meta
Contiene metadatos técnicos para el control del pipeline, especialmente la configuración de cargas.

### 🥈 Silver
Contiene datos validados, estandarizados y preparados para el análisis.  
Aquí se ejecutan procesos de transformación y carga desde Bronze.

### 🥇 Gold
Contiene el modelo analítico final, estructurado mediante tablas de **dimensiones** y **hechos**, listo para consultas e indicadores.

---

# 🧩 Estructura de datos del proyecto

El proyecto trabaja con 8 entidades principales relacionadas con el desempeño del personal operativo:

- `asesor`
- `reclutamiento`
- `rendimiento_mensual`
- `capacitacion`
- `calidad`
- `incidencias`
- `adherencia`
- `clima`

Estas entidades se cargan inicialmente en Bronze, luego son procesadas en Silver y finalmente consolidadas en Gold.

---

# 🥉 Esquema Bronze

La capa Bronze almacena las tablas base del proyecto:

- `bronze.asesor`
- `bronze.reclutamiento`
- `bronze.rendimiento_mensual`
- `bronze.capacitacion`
- `bronze.calidad`
- `bronze.incidencias`
- `bronze.adherencia`
- `bronze.clima`

Aunque conceptualmente Bronze suele representar datos crudos, en este proyecto se trabajó con una versión inicial ya estructurada en PostgreSQL, lo que permitió facilitar la carga y la transición hacia las siguientes capas.

---

# ⚙️ Esquema Meta

Para el control técnico del pipeline se implementó el esquema `meta`, que contiene la tabla:

- `meta.pipeline_config`

Esta tabla registra:

- el nombre de la tabla controlada
- el tipo de carga (`H`, `F`, `I`)
- la fecha de la última carga registrada

Esto permite centralizar la lógica técnica del pipeline y dejar trazabilidad sobre las tablas procesadas.

Ejemplo de configuración:

```sql
INSERT INTO meta.pipeline_config VALUES
('asesor', 'H', NOW()),
('reclutamiento', 'H', NOW()),
('rendimiento_mensual', 'H', NOW()),
('capacitacion', 'H', NOW()),
('calidad', 'H', NOW()),
('incidencias', 'H', NOW()),
('adherencia', 'H', NOW()),
('clima', 'H', NOW());
```

---

# 🥈 Esquema Silver

La capa Silver se implementó para contener los datos ya preparados para análisis intermedio.

Tablas creadas:

- `silver.asesor`
- `silver.reclutamiento`
- `silver.rendimiento_mensual`
- `silver.capacitacion`
- `silver.calidad`
- `silver.incidencias`
- `silver.adherencia`
- `silver.clima`

## Función de Silver
- Validar estructura de datos
- Estandarizar tipos de datos
- Preparar la información para la capa analítica
- Automatizar el movimiento desde Bronze mediante funciones SQL

## Procedimientos almacenados principales
- `silver.sp_load_asesor()`
- `silver.sp_load_reclutamiento()`
- `silver.sp_load_rendimiento_mensual()`
- `silver.sp_load_capacitacion()`
- `silver.sp_load_calidad()`
- `silver.sp_load_incidencias()`
- `silver.sp_load_adherencia()`
- `silver.sp_load_clima()`

Estas funciones permiten cargar información desde Bronze hacia Silver de forma estructurada y repetible.

---

# 🥇 Esquema Gold

La capa Gold contiene el modelo analítico final del proyecto.

## Dimensiones
- `gold.dim_asesor`
- `gold.dim_tiempo`

## Hechos
- `gold.fact_reclutamiento`
- `gold.fact_desempeno_mensual`

## Función del modelo Gold
- Consolidar información operativa del asesor
- Organizar datos para análisis dimensional
- Facilitar consultas analíticas y generación de indicadores
- Integrar métricas de rendimiento, calidad, adherencia, clima, capacitación e incidencias

---

# ⭐ Modelo dimensional

El modelo analítico final sigue una lógica de esquema en estrella simplificado.

```text
                dim_asesor
                    │
                    │
      ┌─────────────┴─────────────┐
      │                           │
fact_reclutamiento     fact_desempeno_mensual
                                    │
                                    │
                               dim_tiempo
```

## Descripción

### `dim_asesor`
Contiene atributos descriptivos del asesor:
- identificación
- modalidad de trabajo
- edad
- estado civil
- carga familiar
- distancia a oficina
- experiencia previa
- nivel educativo
- estado actual

### `dim_tiempo`
Contiene los períodos de análisis basados en `mes_gestion`.

> Nota: en este proyecto, `mes_gestion` representa un período secuencial de gestión y no necesariamente un mes calendario real.

### `fact_reclutamiento`
Concentra indicadores del proceso de ingreso del asesor:
- puntaje CV
- score de entrevista
- test de estrés
- test de empatía
- perfil de riesgo de ingreso

### `fact_desempeno_mensual`
Integra métricas mensuales como:
- TMO promedio
- FCR
- NPS
- microausentismos
- horas no listo
- horas de capacitación
- nota de auditoría
- errores críticos
- adherencia
- tardanzas
- pausas
- desconexiones
- motivación
- satisfacción con jefe
- total de incidencias
- gravedad promedio

---

# ⚙️ Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| Python | Procesamiento y conexión con base de datos |
| Pandas | Lectura y manipulación de datasets |
| Jupyter Notebook | Ejecución de carga inicial |
| PostgreSQL | Motor de base de datos |
| Supabase | Base de datos en la nube |
| SQL | Creación de esquemas, tablas y funciones |
| GitHub | Control de versiones |
| psycopg2 | Conexión entre Python y PostgreSQL |

---

# 📂 Estructura del repositorio

```text
PP2B_SATDPO/
│
├── .secrets/
│   ├── db_config.py
│   └── secrets.toml
│
├── assets/
│   └── docs/
│
├── data/
│   ├── 1_asesor.csv
│   ├── 2_reclutamiento.csv
│   ├── 3_rendimiento_mensual.csv
│   ├── 4_capacitacion.csv
│   ├── 5_calidad.csv
│   ├── 6_incidencias.csv
│   ├── 7_adherencia.csv
│   └── 8_clima.csv
│
├── notebooks/
│   └── conexion_supabase.ipynb
│
├── sql/
│   ├── bronze.sql
│   ├── meta.sql
│   ├── silver.sql
│   ├── gold.sql
│   └── procedures.sql
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 📥 Fuentes de datos

El sistema utiliza datasets relacionados con el desempeño del personal operativo.

| Archivo | Descripción |
|--------|-------------|
| `1_asesor.csv` | Información general del personal |
| `2_reclutamiento.csv` | Datos del proceso de contratación |
| `3_rendimiento_mensual.csv` | Indicadores mensuales de desempeño |
| `4_capacitacion.csv` | Registro de intervenciones y capacitaciones |
| `5_calidad.csv` | Evaluaciones de calidad del desempeño |
| `6_incidencias.csv` | Registro de incidencias operativas |
| `7_adherencia.csv` | Cumplimiento de horarios y pausas |
| `8_clima.csv` | Indicadores de clima laboral |

---

# 🚀 Cómo ejecutar el proyecto

## 1. Clonar el repositorio

```bash
git clone https://github.com/steph-d989/PP2B_SATDPO.git
cd PP2B_SATDPO
```

## 2. Crear entorno virtual

```bash
python -m venv venv_bda_idl2
```

### Activar entorno en Windows

```bash
venv_bda_idl2\Scripts\activate
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4. Configurar credenciales
Crear o completar los archivos de configuración en `.secrets/` con los datos de conexión a Supabase/PostgreSQL.

Ejemplo esperado:
- host
- puerto
- usuario
- contraseña
- nombre de base de datos

## 5. Ejecutar la carga inicial a Bronze
Abrir y ejecutar el notebook:

```text
notebooks/carga_bronze.ipynb
```

Este notebook realiza:
- lectura de archivos CSV
- preparación inicial
- carga de datos hacia Bronze

## 6. Crear esquemas y tablas en PostgreSQL
Ejecutar los scripts SQL correspondientes para:
- Bronze
- Meta
- Silver
- Gold

## 7. Ejecutar procedimientos de carga del pipeline

### Bronze → Silver
Ejecutar las funciones de carga del esquema Silver.

Ejemplo:

```sql
SELECT silver.sp_load_asesor();
SELECT silver.sp_load_reclutamiento();
```

### Silver → Gold
Ejecutar las funciones de carga del esquema Gold.

Ejemplo:

```sql
SELECT gold.sp_load_dim_asesor();
SELECT gold.sp_load_dim_tiempo();
SELECT gold.sp_load_fact_reclutamiento();
SELECT gold.sp_load_fact_desempeno_mensual();
```

## 8. Validar resultados
Realizar consultas de conteo y revisión de datos en cada capa.

Ejemplo:

```sql
SELECT COUNT(*) FROM silver.asesor;
SELECT COUNT(*) FROM gold.fact_desempeno_mensual;
```

---

# 🔄 Flujo del pipeline

El pipeline del proyecto sigue la siguiente secuencia:

1. Carga de archivos fuente
2. Inserción inicial en Bronze
3. Registro técnico de tablas en Meta
4. Transformación y carga hacia Silver
5. Consolidación analítica en Gold
6. Consulta del modelo final

---

# 📌 Principales aprendizajes del proyecto

- Uso de arquitectura Medallion en un entorno académico
- Implementación de esquemas y tablas en PostgreSQL
- Integración entre Python, SQL y Supabase
- Automatización de cargas mediante funciones SQL
- Modelado dimensional para análisis de desempeño
- Organización de un pipeline de datos escalable y entendible

---

# 📈 Posibles mejoras futuras

- Implementar cargas incrementales reales usando `meta.pipeline_config`
- Incorporar reglas de negocio más explícitas
- Añadir dashboards en Power BI, Tableau o Streamlit
- Crear alertas automáticas a partir de los indicadores de Gold
- Agregar monitoreo y auditoría de ejecuciones del pipeline
- Documentar las dependencias entre tablas y el orden de carga

---

# 🎓 Contexto académico

Proyecto desarrollado para el curso:

**Big Data Aplicada**

Institución:

**Instituto Continental**

---

# 👥 Autoras

- **DAMIANI KAEMENA, STEPHANI**
- **CARDENAS ACARO, CLAUDIA MILAGROS**

Docente:
- **SERGIO ORIZANO SALVADOR**

---

# 🔗 Repositorio

GitHub del proyecto:

```text
https://github.com/steph-d989/PP2B_SATDPO.git
```
