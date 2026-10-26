"""Lectura y procesamiento tolerante de movimientos JSON."""

import csv
import json
from datetime import date
from pathlib import Path

from liquidaciones import calcular_liquidacion, validar_tarifas
from validaciones import validar_movimiento


def leer_json(ruta):
    """Lee un archivo JSON con codificación UTF-8."""
    ruta = Path(ruta)
    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError as error:
        raise ValueError(f"No se encontró el archivo: {ruta}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"El archivo JSON no es válido: {ruta}") from error


def cargar_tarifas(ruta):
    """Carga y valida la configuración tarifaria."""
    return validar_tarifas(leer_json(ruta))


def validar_fecha_operacion(valor):
    if not isinstance(valor, str):
        raise ValueError("'fecha_operacion' debe tener el formato AAAA-MM-DD.")
    try:
        fecha = date.fromisoformat(valor)
    except ValueError as error:
        raise ValueError("'fecha_operacion' debe tener el formato AAAA-MM-DD.") from error
    if fecha.isoformat() != valor:
        raise ValueError("'fecha_operacion' debe tener el formato AAAA-MM-DD.")
    return valor


def valor_para_csv(valor):
    """Convierte valores complejos de un registro inválido a texto legible."""
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    return json.dumps(valor, ensure_ascii=False)


def crear_rechazo(movimiento, motivo):
    if isinstance(movimiento, dict):
        return {
            "id": valor_para_csv(movimiento.get("id", "")),
            "patente": valor_para_csv(movimiento.get("patente", "")),
            "tipo_vehiculo": valor_para_csv(movimiento.get("tipo_vehiculo", "")),
            "entrada": valor_para_csv(movimiento.get("entrada", "")),
            "salida": valor_para_csv(movimiento.get("salida", "")),
            "motivo": motivo,
            "registro_original": json.dumps(movimiento, ensure_ascii=False),
        }
    return {
        "id": "",
        "patente": "",
        "tipo_vehiculo": "",
        "entrada": "",
        "salida": "",
        "motivo": motivo,
        "registro_original": json.dumps(movimiento, ensure_ascii=False),
    }


def procesar_movimientos(ruta_tarifas, ruta_movimientos):
    """Devuelve (válidos, rechazados, cantidad de registros recibidos)."""
    tarifas = cargar_tarifas(ruta_tarifas)
    datos_movimientos = leer_json(ruta_movimientos)

    if not isinstance(datos_movimientos, dict):
        raise ValueError("El archivo de movimientos debe contener un objeto JSON.")
    fecha_operacion = validar_fecha_operacion(
        datos_movimientos.get("fecha_operacion")
    )
    movimientos = datos_movimientos.get("movimientos")
    if not isinstance(movimientos, list):
        raise ValueError("El campo 'movimientos' debe ser una lista.")

    liquidaciones = []
    rechazados = []

    for movimiento in movimientos:
        try:
            datos = validar_movimiento(movimiento)
            minutos_estadia = datos["minutos_salida"] - datos["minutos_entrada"]
            liquidacion = calcular_liquidacion(
                tipo_vehiculo=datos["tipo_vehiculo"],
                tarifas=tarifas,
                minutos_estadia=minutos_estadia,
                entrada=datos["entrada"],
                salida=datos["salida"],
                solicito_lavado=datos["solicito_lavado"],
            )
            liquidacion.update(
                {
                    "fecha_operacion": fecha_operacion,
                    "id": datos["id"],
                    "patente": datos["patente"],
                    "tipo_vehiculo": datos["tipo_vehiculo"],
                }
            )
            liquidaciones.append(liquidacion)
        except (TypeError, ValueError, KeyError) as error:
            rechazados.append(crear_rechazo(movimiento, str(error)))

    return liquidaciones, rechazados, len(movimientos)


def leer_liquidaciones_manuales(ruta_csv):
    """Lee cobros manuales ya liquidados y devuelve validos, rechazados y cantidad."""
    ruta_csv = Path(ruta_csv)
    if not ruta_csv.exists():
        return [], [], 0

    campos_requeridos = {
        "fecha_operacion",
        "id",
        "patente",
        "tipo_vehiculo",
        "dias_completos",
        "duracion_minutos",
        "entrada",
        "salida",
        "solicito_lavado",
        "estacionamiento_base",
        "bonificacion_estacionamiento",
        "estacionamiento_cobrado",
        "costo_lavado",
        "total_cobrado",
    }
    campos_numericos = (
        "dias_completos",
        "duracion_minutos",
        "estacionamiento_base",
        "bonificacion_estacionamiento",
        "estacionamiento_cobrado",
        "costo_lavado",
        "total_cobrado",
    )

    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames is None:
            return [], [], 0

        faltantes = campos_requeridos.difference(lector.fieldnames)
        if faltantes:
            nombres = ", ".join(sorted(faltantes))
            raise ValueError(
                f"El CSV de cobros manuales no tiene las columnas requeridas: {nombres}."
            )

        filas = list(lector)

    liquidaciones = []
    rechazados = []

    for numero_fila, fila in enumerate(filas, start=2):
        try:
            liquidacion = {
                campo: fila.get(campo, "")
                for campo in campos_requeridos
            }

            for campo in campos_numericos:
                liquidacion[campo] = int(liquidacion[campo])

            if not liquidacion["id"] or not liquidacion["patente"]:
                raise ValueError("Falta el ID o la patente.")
            if liquidacion["dias_completos"] < 0:
                raise ValueError("La cantidad de dias no puede ser negativa.")
            if any(liquidacion[campo] < 0 for campo in campos_numericos):
                raise ValueError("Los importes y la duracion deben ser no negativos.")

            liquidacion["fecha_operacion"] = validar_fecha_operacion(
                liquidacion["fecha_operacion"]
            )

            lavado = str(liquidacion["solicito_lavado"]).strip().lower()
            if lavado in ("true", "1", "si", "s\u00ed"):
                liquidacion["solicito_lavado"] = True
            elif lavado in ("false", "0", "no"):
                liquidacion["solicito_lavado"] = False
            else:
                raise ValueError("El valor de lavado no es valido.")

            if liquidacion["total_cobrado"] != (
                liquidacion["estacionamiento_cobrado"] + liquidacion["costo_lavado"]
            ):
                raise ValueError("El total no coincide con el desglose.")

            liquidaciones.append(liquidacion)
        except (TypeError, ValueError, KeyError) as error:
            rechazados.append(
                {
                    "id": fila.get("id", ""),
                    "patente": fila.get("patente", ""),
                    "tipo_vehiculo": fila.get("tipo_vehiculo", ""),
                    "entrada": fila.get("entrada", ""),
                    "salida": fila.get("salida", ""),
                    "motivo": (
                        f"Liquidacion manual invalida en la fila {numero_fila}: {error}"
                    ),
                    "registro_original": json.dumps(fila, ensure_ascii=False),
                }
            )

    return liquidaciones, rechazados, len(filas)
