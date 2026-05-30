/* ============================================================
   ARCHIVO: 02_silver_functions_actualizado.sql
   PROYECTO: Modelo Predictivo de Semáforo por Asesor
   CAPA: Silver
   OBJETIVO:
   Crear funciones reutilizables para limpieza, normalización,
   cálculo de cumplimiento y clasificación de semáforo.

   AJUSTE:
   Versión adaptada para las tablas Bronze actualizadas con campos:
   asesor, dni, area, sede, fecha_ingreso, estado_trabajador,
   anio, mes y nuevos indicadores.
   ============================================================ */

create schema if not exists silver;


/* ============================================================
   1. FUNCIÓN: silver.texto_limpio(valor text)
   OBJETIVO:
   Limpia textos para Silver sin alterar el valor de negocio.
   Convierte cadenas vacías o textos nulos comunes en NULL real.
   ============================================================ */

create or replace function silver.texto_limpio(valor text)
returns text
language plpgsql
immutable
as $$
declare
  v text;
begin
  v := trim(coalesce(valor, ''));

  if v = '' then
    return null;
  end if;

  if lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  return v;
end;
$$;


/* ============================================================
   2. FUNCIÓN: silver.limpiar_dni(valor text)
   OBJETIVO:
   Limpia el DNI y lo conserva como texto.

   Casos esperados:
   '12345678'     -> '12345678'
   ' 12345678 '   -> '12345678'
   '12345678.0'   -> '12345678'
   '12345678,0'   -> '12345678'
   ============================================================ */

create or replace function silver.limpiar_dni(valor text)
returns text
language plpgsql
immutable
as $$
declare
  v text;
begin
  v := trim(coalesce(valor, ''));

  if v = '' then
    return null;
  end if;

  if lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  -- Caso típico cuando Excel convierte DNI a decimal: 12345678.0
  if v ~ '^\d+[\.,]0+$' then
    v := regexp_replace(v, '[\.,]0+$', '');
  end if;

  -- Dejar solo números
  v := regexp_replace(v, '[^0-9]', '', 'g');

  if v = '' then
    return null;
  end if;

  return v;
end;
$$;


/* ============================================================
   3. FUNCIÓN: silver.to_numeric_safe(valor text)
   OBJETIVO:
   Convierte texto a número de forma segura.

   Casos esperados:
   '95%'       -> 95
   '95,5%'     -> 95.5
   '95.5'      -> 95.5
   ' 100 '     -> 100
   ''          -> null
   ============================================================ */

create or replace function silver.to_numeric_safe(valor text)
returns numeric
language plpgsql
immutable
as $$
declare
  v text;
begin
  v := trim(coalesce(valor, ''));

  if v = '' then
    return null;
  end if;

  if lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  -- Quitar símbolo de porcentaje
  v := replace(v, '%', '');

  -- Convertir coma decimal a punto decimal
  v := replace(v, ',', '.');

  -- Eliminar caracteres no numéricos, excepto punto y signo negativo
  v := regexp_replace(v, '[^0-9\.\-]', '', 'g');

  if v = '' or v = '-' or v = '.' or v = '-.' then
    return null;
  end if;

  return v::numeric;

exception
  when others then
    return null;
end;
$$;


/* ============================================================
   4. FUNCIÓN: silver.normalizar_anio(valor text)
   OBJETIVO:
   Normaliza el año como entero.
   Si viene vacío, usa 2026 porque el proyecto trabaja con data sintética 2026.
   ============================================================ */

create or replace function silver.normalizar_anio(valor text)
returns integer
language plpgsql
immutable
as $$
declare
  v text;
begin
  v := trim(coalesce(valor, ''));

  if v = '' or lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return 2026;
  end if;

  v := regexp_replace(v, '[^0-9]', '', 'g');

  if v = '' then
    return 2026;
  end if;

  if length(v) >= 4 then
    return substring(v from 1 for 4)::integer;
  end if;

  return v::integer;

exception
  when others then
    return 2026;
end;
$$;


/* ============================================================
   5. FUNCIÓN: silver.normalizar_mes(valor text)
   OBJETIVO:
   Convierte diferentes formatos de mes a formato MM.

   Casos esperados:
   'Enero'      -> '01'
   'Febrero'    -> '02'
   '1'          -> '01'
   '01'         -> '01'
   '2026-01-01' -> '01'
   '2026-01'    -> '01'
   ============================================================ */

create or replace function silver.normalizar_mes(valor text)
returns text
language plpgsql
immutable
as $$
declare
  v text;
  n integer;
begin
  v := lower(trim(coalesce(valor, '')));

  if v = '' or v in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  -- Meses en texto español / abreviado / inglés
  if v in ('enero', 'ene', 'jan', 'january') then
    return '01';
  elsif v in ('febrero', 'feb', 'february') then
    return '02';
  elsif v in ('marzo', 'mar', 'march') then
    return '03';
  elsif v in ('abril', 'abr', 'apr', 'april') then
    return '04';
  elsif v in ('mayo', 'may') then
    return '05';
  elsif v in ('junio', 'jun', 'june') then
    return '06';
  elsif v in ('julio', 'jul', 'july') then
    return '07';
  elsif v in ('agosto', 'ago', 'aug', 'august') then
    return '08';
  elsif v in ('septiembre', 'setiembre', 'sep', 'september') then
    return '09';
  elsif v in ('octubre', 'oct', 'october') then
    return '10';
  elsif v in ('noviembre', 'nov', 'november') then
    return '11';
  elsif v in ('diciembre', 'dic', 'dec', 'december') then
    return '12';
  end if;

  -- Fecha con hora: 2026-01-01 00:00:00
  if v ~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$' then
    return to_char(v::timestamp, 'MM');
  end if;

  -- Fecha simple: 2026-01-01
  if v ~ '^\d{4}-\d{2}-\d{2}$' then
    return to_char(v::date, 'MM');
  end if;

  -- Formato YYYY-MM
  if v ~ '^\d{4}-\d{2}$' then
    return substring(v from 6 for 2);
  end if;

  -- Número de mes: 1, 01, 1.0
  if v ~ '^\d{1,2}([\.,]0+)?$' then
    n := split_part(replace(v, ',', '.'), '.', 1)::integer;

    if n between 1 and 12 then
      return lpad(n::text, 2, '0');
    end if;
  end if;

  return null;

exception
  when others then
    return null;
end;
$$;


/* ============================================================
   6. FUNCIÓN: silver.normalizar_periodo(anio text, mes text)
   OBJETIVO:
   Construye el periodo estándar YYYY-MM usando las columnas nuevas anio y mes.
   Si anio viene vacío, usa 2026 por defecto para la data sintética.
   ============================================================ */

create or replace function silver.normalizar_periodo(anio text, mes text)
returns text
language plpgsql
immutable
as $$
declare
  a integer;
  m text;
begin
  a := silver.normalizar_anio(anio);
  m := silver.normalizar_mes(mes);

  if m is null then
    return null;
  end if;

  return a::text || '-' || m;
end;
$$;


/* ============================================================
   7. FUNCIÓN: silver.normalizar_fecha(valor text)
   OBJETIVO:
   Convierte fechas de texto a date de forma segura.
   Aplica para fecha_ingreso y otros campos de fecha.
   ============================================================ */

create or replace function silver.normalizar_fecha(valor text)
returns date
language plpgsql
immutable
as $$
declare
  v text;
begin
  v := trim(coalesce(valor, ''));

  if v = '' or lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  if v ~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$' then
    return v::timestamp::date;
  end if;

  if v ~ '^\d{4}-\d{2}-\d{2}$' then
    return v::date;
  end if;

  if v ~ '^\d{2}/\d{2}/\d{4}$' then
    return to_date(v, 'DD/MM/YYYY');
  end if;

  return null;

exception
  when others then
    return null;
end;
$$;


/* ============================================================
   8. FUNCIÓN: silver.normalizar_tmo_minutos(valor text)
   OBJETIVO:
   Convierte el TMO a minutos decimales.

   Casos esperados:
   '5:30'                   -> 5.50
   '5,30'                   -> 5.30
   '5.30'                   -> 5.30
   '2026-04-05 00:00:00'    -> 5.04
   '2026-07-05 00:00:00'    -> 5.07

   Nota importante:
   Cuando Excel/Google Sheets interpreta el TMO como fecha,
   se transforma con la regla:
   día + mes / 100
   ============================================================ */

create or replace function silver.normalizar_tmo_minutos(valor text)
returns numeric
language plpgsql
immutable
as $$
declare
  v text;
  partes text[];
begin
  v := trim(coalesce(valor, ''));

  if v = '' or lower(v) in ('nan', 'none', 'null', 'na', 'n/a', 'sin dato') then
    return null;
  end if;

  -- Caso 1: fecha con hora, ejemplo: 2026-01-05 00:00:00
  -- Regla correcta para este dataset: día + mes/100
  -- Ejemplo: 2026-01-05 = 5.01
  if v ~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$' then
    return round(
      extract(day from v::timestamp)::numeric
      + extract(month from v::timestamp)::numeric / 100,
      2
    );
  end if;

  -- Caso 2: fecha simple, ejemplo: 2026-01-05
  if v ~ '^\d{4}-\d{2}-\d{2}$' then
    return round(
      extract(day from v::date)::numeric
      + extract(month from v::date)::numeric / 100,
      2
    );
  end if;

  -- Caso 3: minutos y segundos, ejemplo: 5:30
  -- 5:30 = 5.50 minutos decimales
  if v ~ '^\d{1,2}:\d{2}$' then
    partes := string_to_array(v, ':');

    return round(
      partes[1]::numeric + partes[2]::numeric / 60,
      2
    );
  end if;

  -- Caso 4: número normal como texto, ejemplo: 5.0, 5.13 o 5,13
  v := replace(v, ',', '.');
  v := regexp_replace(v, '[^0-9\.\-]', '', 'g');

  if v = '' or v = '-' or v = '.' or v = '-.' then
    return null;
  end if;

  return round(v::numeric, 2);

exception
  when others then
    return null;
end;
$$;


/* ============================================================
   9. FUNCIÓN: silver.calcular_nc_mayor_mejor(...)
   OBJETIVO:
   Calcula nivel de cumplimiento para indicadores donde
   un valor mayor es mejor.

   Aplica para:
   - Aprobación inmediata
   - Horas conexión
   - NPS
   - Calidad
   - Tipificación CRM
   ============================================================ */

create or replace function silver.calcular_nc_mayor_mejor(
  valor numeric,
  meta_0 numeric,
  meta_100 numeric,
  meta_150 numeric
)
returns numeric
language plpgsql
immutable
as $$
begin
  if valor is null then
    return null;
  end if;

  if meta_0 is null or meta_100 is null or meta_150 is null then
    return null;
  end if;

  if valor <= meta_0 then
    return 0;
  end if;

  if valor > meta_0 and valor <= meta_100 then
    return round(
      ((valor - meta_0) / nullif(meta_100 - meta_0, 0)) * 100,
      2
    );
  end if;

  if valor > meta_100 and valor < meta_150 then
    return round(
      100 + ((valor - meta_100) / nullif(meta_150 - meta_100, 0)) * 50,
      2
    );
  end if;

  if valor >= meta_150 then
    return 150;
  end if;

  return null;
end;
$$;


/* ============================================================
   10. FUNCIÓN: silver.calcular_nc_menor_mejor(...)
   OBJETIVO:
   Calcula nivel de cumplimiento para indicadores donde
   un valor menor es mejor.

   Aplica para:
   - TMO
   ============================================================ */

create or replace function silver.calcular_nc_menor_mejor(
  valor numeric,
  meta_150 numeric,
  meta_100 numeric,
  meta_0 numeric
)
returns numeric
language plpgsql
immutable
as $$
begin
  if valor is null then
    return null;
  end if;

  if meta_150 is null or meta_100 is null or meta_0 is null then
    return null;
  end if;

  if valor <= meta_150 then
    return 150;
  end if;

  if valor > meta_150 and valor <= meta_100 then
    return round(
      100 + ((meta_100 - valor) / nullif(meta_100 - meta_150, 0)) * 50,
      2
    );
  end if;

  if valor > meta_100 and valor < meta_0 then
    return round(
      ((meta_0 - valor) / nullif(meta_0 - meta_100, 0)) * 100,
      2
    );
  end if;

  if valor >= meta_0 then
    return 0;
  end if;

  return null;
end;
$$;


/* ============================================================
   11. FUNCIÓN: silver.clasificar_semaforo(score numeric)
   OBJETIVO:
   Clasifica el score ponderado final en Verde, Ámbar o Rojo.

   score >= 100 -> Verde
   score >= 70  -> Ámbar
   score < 70   -> Rojo
   ============================================================ */

create or replace function silver.clasificar_semaforo(score numeric)
returns text
language plpgsql
immutable
as $$
begin
  if score is null then
    return null;
  end if;

  if score >= 100 then
    return 'Verde';
  elsif score >= 70 then
    return 'Ámbar';
  else
    return 'Rojo';
  end if;
end;
$$;


/* ============================================================
   12. FUNCIÓN: silver.nivel_alerta_nc(nc numeric)
   OBJETIVO:
   Clasifica el nivel de alerta de cada indicador normalizado.
   ============================================================ */

create or replace function silver.nivel_alerta_nc(nc numeric)
returns text
language plpgsql
immutable
as $$
begin
  if nc is null then
    return 'Sin dato';
  end if;

  if nc >= 100 then
    return 'Adecuado';
  elsif nc >= 70 then
    return 'Por mejorar';
  else
    return 'Crítico';
  end if;
end;
$$;


/* ============================================================
   13. PRUEBAS RÁPIDAS DE VALIDACIÓN
   Estas consultas se dejan comentadas.
   Puedes copiarlas y ejecutarlas aparte si deseas revisar.
   Si usas scripts/run_sql.py, déjalas comentadas.
   ============================================================ */

/*
select silver.texto_limpio(' NaN ') as texto_limpio;

select silver.limpiar_dni('12345678.0') as dni_limpio;

select silver.to_numeric_safe('95,5%') as porcentaje;

select silver.normalizar_anio('2026') as anio_normalizado;

select silver.normalizar_mes('Enero') as mes_normalizado;

select silver.normalizar_periodo('2026', 'Enero') as periodo_normalizado;

select silver.normalizar_fecha('01/03/2026') as fecha_normalizada;

select silver.normalizar_tmo_minutos('2026-04-05 00:00:00') as tmo_fecha_1;

select silver.normalizar_tmo_minutos('5:30') as tmo_min_seg;

select silver.calcular_nc_mayor_mejor(90, 70, 90, 95) as nc_calidad;

select silver.calcular_nc_menor_mejor(5.50, 4.9, 5.0, 6.0) as nc_tmo;

select silver.clasificar_semaforo(85) as semaforo;

select silver.nivel_alerta_nc(65) as nivel_alerta;
*/
