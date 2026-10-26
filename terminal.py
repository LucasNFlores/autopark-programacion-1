"""Utilidades sencillas para controlar la consola."""

import os
import sys


def limpiar_consola():
    """Limpia la pantalla visible y coloca el cursor al inicio."""
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def esperar_enter(mensaje="Presione ENTER para continuar..."):
    """Pausa la pantalla hasta que el usuario confirme."""
    input(mensaje)