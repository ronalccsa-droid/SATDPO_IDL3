-- ============================================================
-- 01_bronze_tables.sql
-- Crea nuevamente las tablas BRONZE para el Proyecto Productivo 2B
-- Estructura actualizada según los nuevos encabezados de tus archivos.
--
-- IMPORTANTE:
-- Este script elimina y vuelve a crear las tablas bronze.
-- Ejecutarlo antes de importar la data con scripts/importar_drive_bronze.py all
-- ============================================================

create schema if not exists bronze;

-- ------------------------------------------------------------
-- Limpieza de tablas anteriores
-- Se usa CASCADE porque pueden existir vistas Silver/Gold dependientes.
-- Luego debes volver a ejecutar los scripts 02, 03 y 04.
-- ------------------------------------------------------------
drop table if exists bronze.tmo cascade;
drop table if exists bronze.crm cascade;
drop table if exists bronze.nps cascade;
drop table if exists bronze.calidad cascade;
drop table if exists bronze.aprobacion_inmediata cascade;
drop table if exists bronze.horas_conexion_mes cascade;
drop table if exists bronze.asesor cascade;

-- ------------------------------------------------------------
-- Tabla maestra de asesores
-- Archivo origen: Tabla_asesores
-- Encabezados: asesor, DNI, area, sede, fecha_ingreso, estado_trabajador
-- ------------------------------------------------------------
create table bronze.asesor (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- Horas de conexión mensual
-- Archivo origen: data_sintetica_horas_conexion_mensual
-- Encabezados actuales:
-- asesor, DNI, area, sede, fecha_ingreso, estado_trabajador,
-- anio, mes, horas_conexion_acumulado, cumplimiento_percent, nivel_indicador
-- ------------------------------------------------------------
create table bronze.horas_conexion_mes (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  anio text,
  mes text,
  horas_conexion_acumulado text,
  cumplimiento_pct text,
  nivel_indicador text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- Aprobación inmediata
-- Archivo origen: data_sintetica_aprobacion_inmediata
-- ------------------------------------------------------------
create table bronze.aprobacion_inmediata (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  indicador text,
  unidad_medida text,
  peso_tablero_pct text,
  aprobacion_inmediata_pct text,
  nivel_cumplimiento text,
  resultado_bono text,
  aporte_al_tablero_pct text,
  anio text,
  mes text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- Calidad
-- Archivo origen: data_sintetica_Calidad
-- ------------------------------------------------------------
create table bronze.calidad (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  anio text,
  mes text,
  nota_examen text,
  calidad_pct text,
  nivel_indicador text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- NPS
-- Archivo origen: data_sintetica_NPS
-- ------------------------------------------------------------
create table bronze.nps (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  anio text,
  mes text,
  nps_pct text,
  nivel_indicador text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- Tipificación CRM
-- Archivo origen: data_sintetica_tipificacionCRM
-- ------------------------------------------------------------
create table bronze.crm (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  anio text,
  mes text,
  atendidas text,
  reg_crm text,
  tip_pct text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- TMO
-- Archivo origen: data_sintetica_TMO
-- ------------------------------------------------------------
create table bronze.tmo (
  asesor text,
  dni text,
  area text,
  sede text,
  fecha_ingreso text,
  estado_trabajador text,
  turno text,
  anio text,
  mes text,
  tmo_minutos text,
  nivel_indicador text,
  archivo_origen text,
  fecha_carga timestamptz default now()
);

-- ------------------------------------------------------------
-- Índices básicos para acelerar cruces posteriores en Silver/Gold
-- ------------------------------------------------------------
create index if not exists idx_bronze_asesor_dni
  on bronze.asesor (dni);

create index if not exists idx_bronze_horas_dni_anio_mes
  on bronze.horas_conexion_mes (dni, anio, mes);

create index if not exists idx_bronze_aprobacion_dni_anio_mes
  on bronze.aprobacion_inmediata (dni, anio, mes);

create index if not exists idx_bronze_calidad_dni_anio_mes
  on bronze.calidad (dni, anio, mes);

create index if not exists idx_bronze_nps_dni_anio_mes
  on bronze.nps (dni, anio, mes);

create index if not exists idx_bronze_crm_dni_anio_mes
  on bronze.crm (dni, anio, mes);

create index if not exists idx_bronze_tmo_dni_anio_mes
  on bronze.tmo (dni, anio, mes);

-- ------------------------------------------------------------
-- Comprobación de estructura creada
-- Si todavía no importaste data, los conteos saldrán en cero.
-- ------------------------------------------------------------
select 'asesor' as tabla, count(*) as filas from bronze.asesor
union all
select 'horas_conexion_mes', count(*) from bronze.horas_conexion_mes
union all
select 'aprobacion_inmediata', count(*) from bronze.aprobacion_inmediata
union all
select 'calidad', count(*) from bronze.calidad
union all
select 'nps', count(*) from bronze.nps
union all
select 'crm', count(*) from bronze.crm
union all
select 'tmo', count(*) from bronze.tmo;
