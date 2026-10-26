"""Escritura de los archivos CSV de AutoPark."""

import csv
from pathlib import Path


COLUMNAS_LIQUIDACION = [
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
]
COLUMNAS_RECHAZADOS = [
    "id",
    "patente",
    "tipo_vehiculo",
    "entrada",
    "salida",
    "motivo",
    "registro_original",
]


def escribir_csv(ruta, filas, columnas):
    """Crea o reemplaza un CSV con encabezado y codificación compatible con Excel."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)


def agregar_liquidacion_manual(ruta, liquidacion):
    """Agrega una operación manual sin borrar las anteriores."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    archivo_existente = ruta.exists() and ruta.stat().st_size > 0
    # utf-8-sig agrega una marca BOM al abrir. Solo se usa al crear el archivo.
    codificacion = "utf-8" if archivo_existente else "utf-8-sig"

    with ruta.open("a", encoding=codificacion, newline="") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=COLUMNAS_LIQUIDACION, extrasaction="ignore"
        )
        if not archivo_existente:
            escritor.writeheader()
        escritor.writerow(liquidacion)


def guardar_resultados_lote(directorio_salida, liquidaciones, rechazados):
    """Guarda liquidaciones, rechazos y el ranking del desafío 8.3."""
    directorio_salida = Path(directorio_salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)
    escribir_csv(
        directorio_salida / "liquidacion.csv",
        liquidaciones,
        COLUMNAS_LIQUIDACION,
    )
    escribir_csv(
        directorio_salida / "rechazados.csv",
        rechazados,
        COLUMNAS_RECHAZADOS,
    )

    ranking = sorted(
        liquidaciones,
        key=lambda fila: (
            int(fila["total_cobrado"]),
            int(fila["duracion_minutos"]),
        ),
        reverse=True,
    )
    escribir_csv(
        directorio_salida / "liquidacion_ranking.csv",
        ranking,
        COLUMNAS_LIQUIDACION,
    )
    return ranking