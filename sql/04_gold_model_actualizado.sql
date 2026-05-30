/* ============================================================
   ARCHIVO: 04_gold_model.sql
   PROYECTO: Modelo Predictivo de Semáforo por Asesor
   CAPA: Gold
   OBJETIVO:
   Consolidar indicadores mensuales por asesor, calcular niveles de cumplimiento,
   score ponderado, semáforo actual y variable objetivo para el modelo predictivo.

   Versión optimizada:
   - Evita explosión de filas por duplicados en Silver.
   - Primero agrupa cada tabla por dni + periodo.
   - Luego realiza los joins de Gold.
   ============================================================ */

create schema if not exists gold;

drop view if exists gold.puntos_mejora_asesor cascade;
drop view if exists gold.modelo_predictivo_semaforo cascade;
drop view if exists gold.modelo_semaforo_asesor_mes cascade;

drop table if exists gold.puntos_mejora_asesor cascade;
drop table if exists gold.modelo_predictivo_semaforo cascade;
drop table if exists gold.modelo_semaforo_asesor_mes cascade;

create table gold.modelo_semaforo_asesor_mes as

with asesor as (
  select
    dni,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador
  from silver.asesor
  group by dni
),

aprobacion as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(aprobacion_inmediata_pct) as aprobacion_inmediata_pct
  from silver.aprobacion_inmediata
  group by dni, anio, mes, periodo
),

horas as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(horas_conexion_acumulado) as horas_conexion_acumulado,
    avg(cumplimiento_pct) as cumplimiento_pct
  from silver.horas_conexion_mes
  group by dni, anio, mes, periodo
),

tmo as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(tmo_minutos) as tmo_minutos,
    max(tmo_original_bronze) as tmo_original_bronze
  from silver.tmo
  group by dni, anio, mes, periodo
),

nps as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(nps_pct) as nps_pct
  from silver.nps
  group by dni, anio, mes, periodo
),

calidad as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(calidad_pct) as calidad_pct,
    avg(nota_examen) as nota_examen
  from silver.calidad
  group by dni, anio, mes, periodo
),

crm as (
  select
    dni,
    anio,
    mes,
    periodo,
    max(asesor) as asesor,
    max(area) as area,
    max(sede) as sede,
    max(fecha_ingreso) as fecha_ingreso,
    max(estado_trabajador) as estado_trabajador,
    avg(tip_pct) as tip_pct,
    sum(atendidas) as atendidas,
    sum(reg_crm) as reg_crm
  from silver.crm
  group by dni, anio, mes, periodo
),

llaves as (
  select dni, anio, mes, periodo from aprobacion
  union
  select dni, anio, mes, periodo from horas
  union
  select dni, anio, mes, periodo from tmo
  union
  select dni, anio, mes, periodo from nps
  union
  select dni, anio, mes, periodo from calidad
  union
  select dni, anio, mes, periodo from crm
),

base as (
  select
    k.dni,

    coalesce(a.asesor, c.asesor, ai.asesor, h.asesor, t.asesor, n.asesor, cr.asesor) as asesor,
    coalesce(a.area, c.area, ai.area, h.area, t.area, n.area, cr.area) as area,
    coalesce(a.sede, c.sede, ai.sede, h.sede, t.sede, n.sede, cr.sede) as sede,
    coalesce(a.fecha_ingreso, c.fecha_ingreso, ai.fecha_ingreso, h.fecha_ingreso, t.fecha_ingreso, n.fecha_ingreso, cr.fecha_ingreso) as fecha_ingreso,
    coalesce(a.estado_trabajador, c.estado_trabajador, ai.estado_trabajador, h.estado_trabajador, t.estado_trabajador, n.estado_trabajador, cr.estado_trabajador) as estado_trabajador,

    k.anio,
    k.mes,
    k.periodo,

    ai.aprobacion_inmediata_pct,
    h.horas_conexion_acumulado,
    h.cumplimiento_pct as horas_conexion_pct,
    t.tmo_minutos,
    n.nps_pct,
    c.calidad_pct,
    cr.tip_pct as tipificacion_crm_pct,

    c.nota_examen,
    cr.atendidas,
    cr.reg_crm,
    t.tmo_original_bronze

  from llaves k
  left join asesor a on k.dni = a.dni
  left join aprobacion ai on k.dni = ai.dni and k.periodo = ai.periodo
  left join horas h on k.dni = h.dni and k.periodo = h.periodo
  left join tmo t on k.dni = t.dni and k.periodo = t.periodo
  left join nps n on k.dni = n.dni and k.periodo = n.periodo
  left join calidad c on k.dni = c.dni and k.periodo = c.periodo
  left join crm cr on k.dni = cr.dni and k.periodo = cr.periodo
),

nc as (
  select
    *,
    silver.calcular_nc_mayor_mejor(aprobacion_inmediata_pct, 45, 50, 55) as nc_aprobacion,
    silver.calcular_nc_mayor_mejor(horas_conexion_pct, 90, 95, 100) as nc_horas_conexion,
    silver.calcular_nc_menor_mejor(tmo_minutos, 4.9, 5.0, 6.0) as nc_tmo,
    silver.calcular_nc_mayor_mejor(nps_pct, 60.7, 70.7, 75.7) as nc_nps,
    silver.calcular_nc_mayor_mejor(calidad_pct, 70, 90, 95) as nc_calidad,
    silver.calcular_nc_mayor_mejor(tipificacion_crm_pct, 80, 90, 100) as nc_tipificacion
  from base
),

score as (
  select
    *,
    round(
      coalesce(nc_aprobacion, 0)     * 0.10 +
      coalesce(nc_horas_conexion, 0) * 0.10 +
      coalesce(nc_tmo, 0)            * 0.20 +
      coalesce(nc_nps, 0)            * 0.25 +
      coalesce(nc_calidad, 0)        * 0.25 +
      coalesce(nc_tipificacion, 0)   * 0.10,
      2
    ) as score_final
  from nc
)

select
  dni,
  asesor,
  area,
  sede,
  fecha_ingreso,
  estado_trabajador,
  anio,
  mes,
  periodo,

  aprobacion_inmediata_pct,
  horas_conexion_acumulado,
  horas_conexion_pct,
  tmo_minutos,
  nps_pct,
  calidad_pct,
  tipificacion_crm_pct,

  nota_examen,
  atendidas,
  reg_crm,

  nc_aprobacion,
  nc_horas_conexion,
  nc_tmo,
  nc_nps,
  nc_calidad,
  nc_tipificacion,

  silver.nivel_alerta_nc(nc_aprobacion) as alerta_aprobacion,
  silver.nivel_alerta_nc(nc_horas_conexion) as alerta_horas_conexion,
  silver.nivel_alerta_nc(nc_tmo) as alerta_tmo,
  silver.nivel_alerta_nc(nc_nps) as alerta_nps,
  silver.nivel_alerta_nc(nc_calidad) as alerta_calidad,
  silver.nivel_alerta_nc(nc_tipificacion) as alerta_tipificacion,

  score_final,
  silver.clasificar_semaforo(score_final) as semaforo_actual,

  tmo_original_bronze
from score;

create index if not exists idx_gold_semaforo_dni_periodo
on gold.modelo_semaforo_asesor_mes (dni, periodo);

create index if not exists idx_gold_semaforo_periodo
on gold.modelo_semaforo_asesor_mes (periodo);

analyze gold.modelo_semaforo_asesor_mes;


create table gold.modelo_predictivo_semaforo as
with datos as (
  select
    *,
    lead(semaforo_actual) over (partition by dni order by periodo) as semaforo_mes_siguiente,
    lead(score_final) over (partition by dni order by periodo) as score_mes_siguiente,
    lead(periodo) over (partition by dni order by periodo) as periodo_siguiente
  from gold.modelo_semaforo_asesor_mes
)
select *
from datos
where semaforo_mes_siguiente is not null;

create index if not exists idx_gold_predictivo_dni_periodo
on gold.modelo_predictivo_semaforo (dni, periodo);

create index if not exists idx_gold_predictivo_target
on gold.modelo_predictivo_semaforo (semaforo_mes_siguiente);

analyze gold.modelo_predictivo_semaforo;


create table gold.puntos_mejora_asesor as
with indicadores as (
  select dni, asesor, anio, mes, periodo, 'Aprobación inmediata' as indicador,
         aprobacion_inmediata_pct as valor_original, nc_aprobacion as nivel_cumplimiento,
         alerta_aprobacion as nivel_alerta, 0.10 as peso_indicador,
         'Revisar criterios de aprobación, validación documental y flujo de autorización inmediata.' as recomendacion
  from gold.modelo_semaforo_asesor_mes

  union all
  select dni, asesor, anio, mes, periodo, 'Horas conexión',
         horas_conexion_pct, nc_horas_conexion,
         alerta_horas_conexion, 0.10,
         'Controlar puntualidad, pausas, desconexiones y cumplimiento de jornada operativa.'
  from gold.modelo_semaforo_asesor_mes

  union all
  select dni, asesor, anio, mes, periodo, 'TMO',
         tmo_minutos, nc_tmo,
         alerta_tmo, 0.20,
         'Mejorar guion de atención, reducir tiempos muertos y reforzar eficiencia en el manejo del caso.'
  from gold.modelo_semaforo_asesor_mes

  union all
  select dni, asesor, anio, mes, periodo, 'NPS',
         nps_pct, nc_nps,
         alerta_nps, 0.25,
         'Mejorar empatía, claridad de comunicación, orientación al asegurado y cierre de llamada.'
  from gold.modelo_semaforo_asesor_mes

  union all
  select dni, asesor, anio, mes, periodo, 'Calidad',
         calidad_pct, nc_calidad,
         alerta_calidad, 0.25,
         'Reforzar protocolo de atención, validación de datos y cumplimiento del checklist de calidad.'
  from gold.modelo_semaforo_asesor_mes

  union all
  select dni, asesor, anio, mes, periodo, 'Tipificación CRM',
         tipificacion_crm_pct, nc_tipificacion,
         alerta_tipificacion, 0.10,
         'Capacitar en registro correcto, codificación del caso y cierre adecuado en el sistema CRM.'
  from gold.modelo_semaforo_asesor_mes
),
priorizado as (
  select
    *,
    row_number() over (
      partition by dni, periodo
      order by nivel_cumplimiento asc nulls first, peso_indicador desc
    ) as prioridad_mejora
  from indicadores
)
select *
from priorizado;

create index if not exists idx_gold_puntos_dni_periodo
on gold.puntos_mejora_asesor (dni, periodo);

create index if not exists idx_gold_puntos_prioridad
on gold.puntos_mejora_asesor (prioridad_mejora);

analyze gold.puntos_mejora_asesor;
