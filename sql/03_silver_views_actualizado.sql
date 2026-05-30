/* ============================================================
   ARCHIVO: 03_silver_views.sql
   PROYECTO: Modelo Predictivo de Semáforo por Asesor
   CAPA: Silver
   OBJETIVO:
   Crear vistas limpias, normalizadas y trazables a partir de Bronze.

   IMPORTANTE:
   Este archivo está actualizado para la nueva estructura Bronze:
   - Se incorporan asesor, area, sede, fecha_ingreso y estado_trabajador
     en las tablas mensuales.
   - Se normaliza anio, mes y periodo.
   - La tabla horas_conexion_mes usa horas_conexion_acumulado.
   ============================================================ */


create schema if not exists silver;


/* ============================================================
   Limpieza preventiva de vistas Silver anteriores.
   Se usa CASCADE porque Gold se reconstruirá después.
   ============================================================ */

drop view if exists silver.tmo cascade;
drop view if exists silver.horas_conexion_mes cascade;
drop view if exists silver.crm cascade;
drop view if exists silver.nps cascade;
drop view if exists silver.calidad cascade;
drop view if exists silver.aprobacion_inmediata cascade;
drop view if exists silver.asesor cascade;


/* ============================================================
   1. VISTA: silver.asesor

   Limpia y normaliza la tabla maestra de asesores.
   ============================================================ */

create view silver.asesor as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  archivo_origen,
  fecha_carga
from bronze.asesor
where silver.limpiar_dni(dni) is not null;


/* ============================================================
   2. VISTA: silver.aprobacion_inmediata

   Normaliza aprobación inmediata mensual por asesor.
   ============================================================ */

create view silver.aprobacion_inmediata as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  silver.texto_limpio(indicador) as indicador,
  silver.texto_limpio(unidad_medida) as unidad_medida,
  silver.to_numeric_safe(peso_tablero_pct) as peso_tablero_pct,
  silver.to_numeric_safe(aprobacion_inmediata_pct) as aprobacion_inmediata_pct,
  silver.texto_limpio(nivel_cumplimiento) as nivel_cumplimiento,
  silver.texto_limpio(resultado_bono) as resultado_bono,
  silver.to_numeric_safe(aporte_al_tablero_pct) as aporte_al_tablero_pct,
  archivo_origen,
  fecha_carga
from bronze.aprobacion_inmediata
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   3. VISTA: silver.calidad

   Normaliza calidad mensual por asesor.
   ============================================================ */

create view silver.calidad as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  silver.to_numeric_safe(nota_examen) as nota_examen,
  silver.to_numeric_safe(calidad_pct) as calidad_pct,
  silver.texto_limpio(nivel_indicador) as nivel_indicador,
  archivo_origen,
  fecha_carga
from bronze.calidad
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   4. VISTA: silver.nps

   Normaliza NPS mensual por asesor.
   ============================================================ */

create view silver.nps as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  silver.to_numeric_safe(nps_pct) as nps_pct,
  silver.texto_limpio(nivel_indicador) as nivel_indicador,
  archivo_origen,
  fecha_carga
from bronze.nps
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   5. VISTA: silver.crm

   Normaliza tipificación CRM mensual por asesor.
   ============================================================ */

create view silver.crm as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  silver.to_numeric_safe(atendidas) as atendidas,
  silver.to_numeric_safe(reg_crm) as reg_crm,
  silver.to_numeric_safe(tip_pct) as tip_pct,
  archivo_origen,
  fecha_carga
from bronze.crm
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   6. VISTA: silver.horas_conexion_mes

   Normaliza horas de conexión mensual.
   La nueva estructura ya trae el acumulado mensual en:
   horas_conexion_acumulado.
   ============================================================ */

create view silver.horas_conexion_mes as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  silver.to_numeric_safe(horas_conexion_acumulado) as horas_conexion_acumulado,
  silver.to_numeric_safe(cumplimiento_pct) as cumplimiento_pct,
  silver.texto_limpio(nivel_indicador) as nivel_indicador,
  archivo_origen,
  fecha_carga
from bronze.horas_conexion_mes
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   7. VISTA: silver.tmo

   Normaliza TMO mensual por asesor.
   Conserva el valor original para trazabilidad.
   ============================================================ */

create view silver.tmo as
select
  silver.limpiar_dni(dni) as dni,
  silver.texto_limpio(asesor) as asesor,
  silver.texto_limpio(area) as area,
  silver.texto_limpio(sede) as sede,
  silver.normalizar_fecha(fecha_ingreso) as fecha_ingreso,
  silver.texto_limpio(estado_trabajador) as estado_trabajador,
  lower(silver.texto_limpio(turno)) as turno,
  silver.normalizar_anio(anio) as anio,
  silver.normalizar_mes(mes) as mes,
  silver.normalizar_periodo(anio, mes) as periodo,
  tmo_minutos as tmo_original_bronze,
  silver.normalizar_tmo_minutos(tmo_minutos) as tmo_minutos,
  silver.texto_limpio(nivel_indicador) as nivel_indicador,
  archivo_origen,
  fecha_carga
from bronze.tmo
where silver.limpiar_dni(dni) is not null
  and silver.normalizar_periodo(anio, mes) is not null;


/* ============================================================
   8. VALIDACIONES RÁPIDAS

   Ejecutar manualmente si deseas comprobar la carga Silver.
   ============================================================ */

/*
-- Conteo por vista Silver
select 'silver.asesor' as tabla, count(*) from silver.asesor
union all
select 'silver.aprobacion_inmediata', count(*) from silver.aprobacion_inmediata
union all
select 'silver.calidad', count(*) from silver.calidad
union all
select 'silver.nps', count(*) from silver.nps
union all
select 'silver.crm', count(*) from silver.crm
union all
select 'silver.horas_conexion_mes', count(*) from silver.horas_conexion_mes
union all
select 'silver.tmo', count(*) from silver.tmo;


-- Revisar periodos normalizados por vista
select 'calidad' as tabla, periodo, count(*) from silver.calidad group by periodo
union all
select 'nps', periodo, count(*) from silver.nps group by periodo
union all
select 'crm', periodo, count(*) from silver.crm group by periodo
union all
select 'horas', periodo, count(*) from silver.horas_conexion_mes group by periodo
union all
select 'tmo', periodo, count(*) from silver.tmo group by periodo
order by tabla, periodo;


-- Revisar corrección de TMO
select
  tmo_original_bronze,
  tmo_minutos,
  count(*) as cantidad
from silver.tmo
group by tmo_original_bronze, tmo_minutos
order by tmo_minutos;


-- Revisar horas conexión mensuales
select
  periodo,
  count(*) as registros,
  min(horas_conexion_acumulado) as min_horas,
  max(horas_conexion_acumulado) as max_horas,
  avg(horas_conexion_acumulado) as promedio_horas
from silver.horas_conexion_mes
group by periodo
order by periodo;


-- Revisar posibles valores críticos nulos
select * from silver.tmo where tmo_minutos is null;
select * from silver.calidad where calidad_pct is null;
select * from silver.nps where nps_pct is null;
select * from silver.crm where tip_pct is null;
select * from silver.horas_conexion_mes where cumplimiento_pct is null;
*/
