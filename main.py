"""Punto de entrada del sistema de consola AutoPark."""

from datetime import date, datetime
from pathlib import Path

from liquidaciones import calcular_liquidacion
from procesamiento import (
    cargar_tarifas,
    leer_liquidaciones_manuales,
    procesar_movimientos,
)
from reportes import agregar_liquidacion_manual, guardar_resultados_lote
from visualizacion import mostrar_liquidaciones_paginadas
from terminal import limpiar_consola, esperar_enter
from validaciones import (
    normalizar_patente,
    normalizar_tipo_vehiculo,
    validar_horario,
)


DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
RUTA_TARIFAS = DIRECTORIO_PROYECTO / "datos_entrada" / "tarifas.json"
RUTA_MOVIMIENTOS = DIRECTORIO_PROYECTO / "datos_entrada" / "movimientos.json"
DIRECTORIO_SALIDA = DIRECTORIO_PROYECTO / "datos_salida"


def solicitar_patente(tipo_vehiculo=None):
    while True:
        try:
            return normalizar_patente(input("Ingrese la patente: "), tipo_vehiculo)
        except ValueError as error:
            print(f"Patente inválida: {error}")


def solicitar_tipo_vehiculo():
    while True:
        try:
            return normalizar_tipo_vehiculo(
                input("Tipo de vehículo (auto/moto/camioneta): ")
            )
        except ValueError as error:
            print(f"Tipo inválido: {error}")


def solicitar_dias_completos():
    while True:
        texto = input("¿Cuántos días completos pasaron?: ").strip()
        try:
            dias = int(texto)
            if dias < 0:
                print("Ingrese un entero no negativo.")
                continue
            return dias
        except ValueError:
            print("Ingrese una cantidad entera de días.")


def solicitar_horario(etiqueta):
    while True:
        horario = input(f"Hora de {etiqueta} (HH:MM): ")
        try:
            return horario, validar_horario(horario)
        except ValueError as error:
            print(error)


def solicitar_lavado():
    while True:
        respuesta = input("¿Solicitó lavado? (S/N): ").strip().lower()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        print("Responda S o N.")


def mostrar_liquidacion(liquidacion):
    if liquidacion["dias_completos"] > 0:
        print(
            "Duración: "
            f"{liquidacion['dias_completos']} día(s) completo(s) "
            f"({liquidacion['duracion_minutos']} minutos de referencia)"
        )
    else:
        print(
            f"Duración: {liquidacion['duracion_minutos']} minutos "
            f"({liquidacion['entrada']} a {liquidacion['salida']})"
        )
    print("Estacionamiento base: $" + str(liquidacion["estacionamiento_base"]))
    print(
        "Bonificación de estacionamiento: -$"
        + str(liquidacion["bonificacion_estacionamiento"])
    )
    print("Estacionamiento cobrado: $" + str(liquidacion["estacionamiento_cobrado"]))
    print("Lavado: $" + str(liquidacion["costo_lavado"]))
    print("TOTAL: $" + str(liquidacion["total_cobrado"]))


def registrar_cobro_manual():
    try:
        tarifas = cargar_tarifas(RUTA_TARIFAS)
        patente = solicitar_patente()
        tipo_vehiculo = solicitar_tipo_vehiculo()
        while True:
            try:
                patente = normalizar_patente(patente, tipo_vehiculo)
                break
            except ValueError as error:
                print(f"Patente no compatible con el tipo de vehículo: {error}")
                patente = solicitar_patente(tipo_vehiculo)
        dias_completos = solicitar_dias_completos()

        entrada = ""
        salida = ""
        minutos_estadia = None
        if dias_completos == 0:
            entrada, minutos_entrada = solicitar_horario("entrada")
            while True:
                salida, minutos_salida = solicitar_horario("salida")
                if minutos_salida >= minutos_entrada:
                    break
                print("La salida no puede ser anterior a la entrada.")
            minutos_estadia = minutos_salida - minutos_entrada

        solicito_lavado = solicitar_lavado()
        liquidacion = calcular_liquidacion(
            tipo_vehiculo=tipo_vehiculo,
            tarifas=tarifas,
            minutos_estadia=minutos_estadia,
            dias_completos=dias_completos,
            entrada=entrada,
            salida=salida,
            solicito_lavado=solicito_lavado,
        )
        liquidacion.update(
            {
                "fecha_operacion": date.today().isoformat(),
                "id": datetime.now().strftime("MAN-%Y%m%d-%H%M%S%f"),
                "patente": patente,
                "tipo_vehiculo": tipo_vehiculo,
            }
        )

        print("\nDetalle de la liquidación")
        mostrar_liquidacion(liquidacion)
        agregar_liquidacion_manual(
            DIRECTORIO_SALIDA / "liquidacion-manual.csv", liquidacion
        )
        print("Comprobante agregado a liquidacion-manual.csv.")
    except (OSError, ValueError) as error:
        print(f"No se pudo registrar el cobro: {error}")


def solicitar_origen_lote():
    while True:
        limpiar_consola()
        print("Origen de los movimientos para procesar")
        print("1. Solo datos iniciales (movimientos.json)")
        print("2. Solo ingresos manuales")
        print("3. Ambos")
        print("4. Volver al menu principal")
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            return "iniciales"
        if opcion == "2":
            return "manuales"
        if opcion == "3":
            return "ambos"
        if opcion == "4":
            return None
        print("Opcion invalida.")
        esperar_enter("Presione ENTER para continuar...")


def procesar_lote():
    origen = solicitar_origen_lote()
    if origen is None:
        return

    try:
        liquidaciones = []
        rechazados = []
        cantidad_recibida = 0

        if origen in ("iniciales", "ambos"):
            validas_iniciales, rechazados_iniciales, recibidos_iniciales = (
                procesar_movimientos(RUTA_TARIFAS, RUTA_MOVIMIENTOS)
            )
            liquidaciones.extend(validas_iniciales)
            rechazados.extend(rechazados_iniciales)
            cantidad_recibida += recibidos_iniciales

        if origen in ("manuales", "ambos"):
            validas_manuales, rechazados_manuales, recibidos_manuales = (
                leer_liquidaciones_manuales(
                    DIRECTORIO_SALIDA / "liquidacion-manual.csv"
                )
            )
            liquidaciones.extend(validas_manuales)
            rechazados.extend(rechazados_manuales)
            cantidad_recibida += recibidos_manuales
            if recibidos_manuales == 0:
                print("No hay ingresos manuales guardados para incluir.")

        guardar_resultados_lote(DIRECTORIO_SALIDA, liquidaciones, rechazados)

        total_recaudado = sum(
            liquidacion["total_cobrado"] for liquidacion in liquidaciones
        )
        nombres_origen = {
            "iniciales": "datos iniciales",
            "manuales": "ingresos manuales",
            "ambos": "datos iniciales e ingresos manuales",
        }
        print("\nLote procesado.")
        print(f"Origen: {nombres_origen[origen]}")
        print(f"Registros recibidos: {cantidad_recibida}")
        print(f"Liquidaciones validas: {len(liquidaciones)}")
        print(f"Movimientos rechazados: {len(rechazados)}")
        print("Total recaudado: $" + str(total_recaudado))
        print(
            "Archivos generados en datos_salida/: liquidacion.csv, rechazados.csv "
            "y liquidacion_ranking.csv."
        )
    except (OSError, ValueError) as error:
        print(f"No se pudo procesar el lote: {error}")

def mostrar_menu():
    print("==================================================")
    print("   SISTEMA DE GESTIÓN DE ESTACIONAMIENTO AUTOPARK")
    print("==================================================")
    print("1. Registrar cobro manual")
    print("2. Procesar lote de movimientos")
    print("3. Ver liquidaciones del último lote")
    print("4. Salir")


def main():
    while True:
        limpiar_consola()
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            limpiar_consola()
            registrar_cobro_manual()
            esperar_enter("\nPresione ENTER para volver al menú principal...")
        elif opcion == "2":
            limpiar_consola()
            procesar_lote()
            esperar_enter("\nPresione ENTER para volver al menú principal...")
        elif opcion == "3":
            mostrar_liquidaciones_paginadas(
                DIRECTORIO_SALIDA / "liquidacion.csv"
            )
        elif opcion == "4":
            print("Hasta luego.")
            break
        else:
            print("Opción inválida. Seleccione 1, 2, 3 o 4.")
            esperar_enter("Presione ENTER para continuar...")

if __name__ == "__main__":
    main()