"""Normalización y validaciones de los datos de AutoPark."""

import re


# Formatos generales: ABC123 (tradicional) o AA123BB (Mercosur).
PATRON_PATENTE_GENERAL = re.compile(
    r"(?:[A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2})"
)
# Moto Mercosur: A123ABC. Moto anterior: 123ABC.
PATRON_PATENTE_MOTO = re.compile(
    r"(?:\d{3}[A-Z]{3}|[A-Z]\d{3}[A-Z]{3})"
)

TIPOS_VEHICULO = {"auto", "moto", "camioneta"}
PATRON_HORARIO = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def normalizar_patente(patente, tipo_vehiculo=None):
    """Normaliza la patente y acepta los formatos correspondientes al vehículo."""
    if not isinstance(patente, str):
        raise ValueError("La patente debe ser un texto.")

    patente_normalizada = "".join(patente.split()).upper()
    categoria = (
        tipo_vehiculo.strip().lower()
        if isinstance(tipo_vehiculo, str)
        else tipo_vehiculo
    )

    if PATRON_PATENTE_GENERAL.fullmatch(patente_normalizada):
        return patente_normalizada

    es_formato_moto = (
        PATRON_PATENTE_MOTO.fullmatch(patente_normalizada)
    )

    if es_formato_moto:
        if categoria is None or categoria == "moto":
            return patente_normalizada
        raise ValueError(
            "El formato ingresado corresponde a una moto; revise el tipo de vehículo."
        )

    if categoria == "moto":
        raise ValueError(
            "Para motos se acepta AAA000, AA000AA, A000AAA (Mercosur) "
            "o 000AAA (formato anterior)."
        )
    raise ValueError(
        "La patente debe tener el formato AAA000 o AA000AA. "
        "Para motos también se acepta A000AAA o 000AAA."
    )


def normalizar_tipo_vehiculo(tipo_vehiculo):
    """Recorta los extremos, convierte a minúsculas y valida la categoría."""
    if not isinstance(tipo_vehiculo, str):
        raise ValueError("El tipo de vehículo debe ser un texto.")

    tipo_normalizado = tipo_vehiculo.strip().lower()
    if tipo_normalizado not in TIPOS_VEHICULO:
        raise ValueError(
            "El tipo de vehículo debe ser auto, moto o camioneta."
        )
    return tipo_normalizado


def validar_horario(horario):
    """Valida HH:MM en formato de 24 horas y devuelve los minutos del día."""
    if not isinstance(horario, str) or not PATRON_HORARIO.fullmatch(horario):
        raise ValueError("El horario debe tener el formato válido HH:MM.")

    horas, minutos = horario.split(":")
    return int(horas) * 60 + int(minutos)


def validar_movimiento(movimiento):
    """Valida un registro del lote y devuelve sus datos normalizados."""
    if not isinstance(movimiento, dict):
        raise ValueError("El registro debe ser un objeto JSON.")

    campos_requeridos = (
        "id",
        "patente",
        "tipo_vehiculo",
        "entrada",
        "salida",
        "solicito_lavado",
    )
    for campo in campos_requeridos:
        if campo not in movimiento:
            raise ValueError(f"Falta el campo requerido '{campo}'.")

    identificador = movimiento["id"]
    if not isinstance(identificador, str) or not identificador.strip():
        raise ValueError("El campo 'id' debe ser un texto no vacío.")

    tipo_vehiculo = normalizar_tipo_vehiculo(movimiento["tipo_vehiculo"])
    patente = normalizar_patente(movimiento["patente"], tipo_vehiculo)
    entrada = movimiento["entrada"]
    salida = movimiento["salida"]
    minutos_entrada = validar_horario(entrada)
    minutos_salida = validar_horario(salida)

    if minutos_salida < minutos_entrada:
        raise ValueError("La salida es anterior a la entrada.")

    solicito_lavado = movimiento["solicito_lavado"]
    if not isinstance(solicito_lavado, bool):
        raise ValueError("El campo 'solicito_lavado' debe ser booleano.")

    return {
        "id": identificador.strip(),
        "patente": patente,
        "tipo_vehiculo": tipo_vehiculo,
        "entrada": entrada,
        "salida": salida,
        "minutos_entrada": minutos_entrada,
        "minutos_salida": minutos_salida,
        "solicito_lavado": solicito_lavado,
    }
