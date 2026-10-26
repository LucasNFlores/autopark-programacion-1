"""Presentación paginada de las liquidaciones del lote en consola."""

import csv
import os
import sys
from pathlib import Path

from terminal import limpiar_consola


ENCABEZADOS = [
    "ID",
    "Patente",
    "Vehículo",
    "Duración",
    "Horario",
    "Lavado",
    "Total ($)",
]


def _preparar_fila(liquidacion):
    dias = int(liquidacion.get("dias_completos") or 0)
    if dias == 1:
        duracion = "1 día"
    elif dias > 1:
        duracion = f"{dias} días"
    else:
        duracion = f"{liquidacion.get('duracion_minutos', '0')} min"

    entrada = liquidacion.get("entrada", "")
    salida = liquidacion.get("salida", "")
    horario = f"{entrada}-{salida}" if entrada and salida else "—"

    lavado_texto = str(liquidacion.get("solicito_lavado", "")).strip().lower()
    lavado = "Sí" if lavado_texto in ("true", "1", "si", "sí") else "No"

    return [
        str(liquidacion.get("id", "")),
        str(liquidacion.get("patente", "")),
        str(liquidacion.get("tipo_vehiculo", "")),
        duracion,
        horario,
        lavado,
        "$" + str(liquidacion.get("total_cobrado", "0")),
    ]


def _mostrar_tabla(liquidaciones, imprimir):
    filas = [_preparar_fila(liquidacion) for liquidacion in liquidaciones]
    anchos = []
    for indice, encabezado in enumerate(ENCABEZADOS):
        ancho = max(
            [len(encabezado)] + [len(fila[indice]) for fila in filas]
        )
        anchos.append(ancho)

    def imprimir_borde():
        imprimir("+" + "+".join("-" * (ancho + 2) for ancho in anchos) + "+")

    def imprimir_fila(fila):
        celdas = [
            " " + valor.ljust(anchos[indice]) + " "
            for indice, valor in enumerate(fila)
        ]
        imprimir("|" + "|".join(celdas) + "|")

    imprimir_borde()
    imprimir_fila(ENCABEZADOS)
    imprimir_borde()
    for fila in filas:
        imprimir_fila(fila)
    imprimir_borde()


def _leer_tecla_windows():
    import msvcrt

    while True:
        tecla = msvcrt.getwch()
        if tecla in ("\r", "\n"):
            return "enter"
        if tecla in ("\x00", "\xe0"):
            tecla = msvcrt.getwch()
            if tecla == "K":
                return "izquierda"
            if tecla == "M":
                return "derecha"


def _leer_tecla_unix():
    import select
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    configuracion_anterior = termios.tcgetattr(descriptor)

    try:
        tty.setraw(descriptor)
        while True:
            tecla = os.read(descriptor, 1).decode("utf-8", errors="ignore")
            if tecla in ("\r", "\n"):
                return "enter"

            if tecla == "\x1b" and select.select([descriptor], [], [], 0.2)[0]:
                segundo_caracter = os.read(descriptor, 1).decode(
                    "utf-8", errors="ignore"
                )
                if (
                    segundo_caracter == "["
                    and select.select([descriptor], [], [], 0.2)[0]
                ):
                    tercer_caracter = os.read(descriptor, 1).decode(
                        "utf-8", errors="ignore"
                    )
                    if tercer_caracter == "D":
                        return "izquierda"
                    if tercer_caracter == "C":
                        return "derecha"
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, configuracion_anterior)


def _leer_accion():
    if sys.stdin.isatty():
        if os.name == "nt":
            return _leer_tecla_windows()
        return _leer_tecla_unix()

    respuesta = input(
        "Consola sin lectura de flechas: escriba I (izquierda), "
        "D (derecha) o presione ENTER para volver: "
    ).strip().lower()
    if respuesta in ("i", "izquierda", "left"):
        return "izquierda"
    if respuesta in ("d", "derecha", "right"):
        return "derecha"
    return "enter"


def mostrar_liquidaciones_paginadas(ruta_csv, input_func=input, imprimir=print):
    """Muestra liquidacion.csv en páginas de 5 o 10 filas."""
    limpiar_consola()
    imprimir("Consulta de liquidaciones del último lote")

    ruta_csv = Path(ruta_csv)
    if not ruta_csv.exists():
        imprimir("Todavía no existe liquidacion.csv. Procese un lote primero.")
        input_func("Presione ENTER para volver al menú...")
        return

    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as archivo:
        registros = list(csv.DictReader(archivo))

    if not registros:
        imprimir("No hay liquidaciones válidas para mostrar.")
        input_func("Presione ENTER para volver al menú...")
        return

    while True:
        respuesta = input_func("Registros por página (5 o 10): ").strip()
        if respuesta in ("5", "10"):
            tamano_pagina = int(respuesta)
            break
        imprimir("Ingrese 5 o 10.")

    cantidad_paginas = (len(registros) + tamano_pagina - 1) // tamano_pagina
    pagina_actual = 0
    limpiar_consola()

    while True:
        inicio = pagina_actual * tamano_pagina
        fin = min(inicio + tamano_pagina, len(registros))
        imprimir(
            f"Página {pagina_actual + 1} de {cantidad_paginas} "
            f"(registros {inicio + 1}-{fin} de {len(registros)})"
        )
        _mostrar_tabla(registros[inicio:fin], imprimir)
        imprimir(
            "\u2190 Página anterior | \u2192 Página siguiente | "
            "ENTER: volver al menú"
        )

        accion = _leer_accion()
        if accion == "enter":
            return
        if accion == "izquierda":
            if pagina_actual > 0:
                pagina_actual -= 1
            limpiar_consola()
        elif accion == "derecha":
            if pagina_actual < cantidad_paginas - 1:
                pagina_actual += 1
            limpiar_consola()