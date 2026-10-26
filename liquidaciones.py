"""Cálculos de estacionamiento y lavado para todos los canales de cobro."""

from collections.abc import Mapping


CLAVES_CONFIGURACION = (
    "minutos_bloque_inicial",
    "minutos_limite_primer_tramo",
    "minutos_hora_adicional",
    "minutos_dia_completo",
)
CLAVES_TARIFA = (
    "precio_bloque_30min",
    "precio_hora_adicional",
    "tope_dia",
    "precio_lavado",
)


def validar_tarifas(datos):
    """Comprueba que el JSON de tarifas tenga claves e importes utilizables."""
    if not isinstance(datos, Mapping):
        raise ValueError("El archivo de tarifas debe contener un objeto JSON.")

    configuracion = datos.get("configuracion")
    tarifas = datos.get("tarifas")
    if not isinstance(configuracion, Mapping) or not isinstance(tarifas, Mapping):
        raise ValueError("El archivo debe incluir 'configuracion' y 'tarifas'.")

    for clave in CLAVES_CONFIGURACION:
        valor = configuracion.get(clave)
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValueError(
                f"La configuración '{clave}' debe ser un entero positivo."
            )

    for tipo in ("auto", "moto", "camioneta"):
        tarifa = tarifas.get(tipo)
        if not isinstance(tarifa, Mapping):
            raise ValueError(f"Falta la tarifa para '{tipo}'.")
        for clave in CLAVES_TARIFA:
            valor = tarifa.get(clave)
            if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
                raise ValueError(
                    f"La tarifa '{tipo}.{clave}' debe ser un entero no negativo."
                )

    if configuracion["minutos_limite_primer_tramo"] < configuracion[
        "minutos_bloque_inicial"
    ]:
        raise ValueError(
            "El límite del primer tramo debe ser al menos un bloque inicial."
        )

    return datos


def calcular_liquidacion(
    tipo_vehiculo,
    tarifas,
    minutos_estadia=None,
    dias_completos=0,
    entrada="",
    salida="",
    solicito_lavado=False,
):
    """Calcula una liquidación; se utiliza tanto en caja como en el lote."""
    validar_tarifas(tarifas)
    if tipo_vehiculo not in tarifas["tarifas"]:
        raise ValueError("No hay una tarifa para el tipo de vehículo indicado.")
    if isinstance(dias_completos, bool) or not isinstance(dias_completos, int):
        raise ValueError("Los días completos deben ser un número entero.")
    if dias_completos < 0:
        raise ValueError("Los días completos no pueden ser negativos.")
    if not isinstance(solicito_lavado, bool):
        raise ValueError("La solicitud de lavado debe ser verdadera o falsa.")

    configuracion = tarifas["configuracion"]
    tarifa = tarifas["tarifas"][tipo_vehiculo]
    minutos_dia = configuracion["minutos_dia_completo"]

    if dias_completos > 0:
        duracion_minutos = dias_completos * minutos_dia
        estacionamiento_base = dias_completos * tarifa["tope_dia"]
        estacionamiento_cobrado = estacionamiento_base
        bonificacion = 0
    else:
        if (
            isinstance(minutos_estadia, bool)
            or not isinstance(minutos_estadia, int)
            or minutos_estadia < 0
        ):
            raise ValueError("La duración debe ser un entero de cero o más minutos.")

        duracion_minutos = minutos_estadia
        bloque_inicial = configuracion["minutos_bloque_inicial"]
        limite_primer_tramo = configuracion["minutos_limite_primer_tramo"]
        hora_adicional = configuracion["minutos_hora_adicional"]

        if duracion_minutos == 0:
            estacionamiento_sin_tope = 0
            costo_horas_excedentes = 0
        elif duracion_minutos <= limite_primer_tramo:
            cantidad_bloques = (duracion_minutos + bloque_inicial - 1) // bloque_inicial
            estacionamiento_sin_tope = (
                cantidad_bloques * tarifa["precio_bloque_30min"]
            )
            costo_horas_excedentes = 0
        else:
            cantidad_bloques_iniciales = (
                limite_primer_tramo + bloque_inicial - 1
            ) // bloque_inicial
            minutos_excedentes = duracion_minutos - limite_primer_tramo
            cantidad_horas_excedentes = (
                minutos_excedentes + hora_adicional - 1
            ) // hora_adicional
            costo_inicial = (
                cantidad_bloques_iniciales * tarifa["precio_bloque_30min"]
            )
            costo_horas_excedentes = (
                cantidad_horas_excedentes * tarifa["precio_hora_adicional"]
            )
            estacionamiento_sin_tope = costo_inicial + costo_horas_excedentes

        estacionamiento_base = min(
            estacionamiento_sin_tope, tarifa["tope_dia"]
        )

        if solicito_lavado and duracion_minutos > limite_primer_tramo:
            estacionamiento_cobrado = min(
                costo_horas_excedentes, tarifa["tope_dia"]
            )
        elif solicito_lavado:
            estacionamiento_cobrado = 0
        else:
            estacionamiento_cobrado = estacionamiento_base

        bonificacion = estacionamiento_base - estacionamiento_cobrado

    costo_lavado = tarifa["precio_lavado"] if solicito_lavado else 0
    total_cobrado = estacionamiento_cobrado + costo_lavado

    return {
        "dias_completos": dias_completos,
        "duracion_minutos": duracion_minutos,
        "entrada": entrada,
        "salida": salida,
        "solicito_lavado": solicito_lavado,
        "estacionamiento_base": estacionamiento_base,
        "bonificacion_estacionamiento": bonificacion,
        "estacionamiento_cobrado": estacionamiento_cobrado,
        "costo_lavado": costo_lavado,
        "total_cobrado": total_cobrado,
    }