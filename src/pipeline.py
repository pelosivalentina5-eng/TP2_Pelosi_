"""Flujo de procesamiento: normalizar -> validar -> limpiar -> calcular -> guardar.

Estas funciones reciben los datos ya cargados (listas de diccionarios),
así que no dependen de si vinieron de un CSV o de un JSON.
"""

import csv
from pathlib import Path

from modelo import (
    BULTOS_POR_PALLET,
    NOMBRES_LINEA,
    TIPOS_MOVIMIENTO,
    Movimiento,
    Producto,
    StockInsuficiente,
)
from validacion import validar_fecha, validar_id

CAMPOS_REQUERIDOS = ["id", "fecha", "codigo", "tipo", "bultos"]

# Más de 1000 bultos en un solo movimiento es imposible para esta fábrica
# (son 10 pallets de la medida más chica): se considera un error de carga.
BULTOS_MAXIMOS = 1000


# ---------- 1. Normalizar y validar el esquema ----------

def normalizar_campos(registros):
    """Pasa los nombres de campo a minúscula y quita espacios en los textos.

    También pasa a mayúscula el código y el tipo, para que '45x60-p' y
    'produccion' se reconozcan igual que '45X60-P' y 'PRODUCCION'.
    """
    normalizados = []
    for registro in registros:
        nuevo = {}
        for campo, valor in registro.items():
            campo = str(campo).strip().lower()
            if isinstance(valor, str):
                valor = valor.strip()
                if campo in ("codigo", "tipo"):
                    valor = valor.upper()
            nuevo[campo] = valor
        normalizados.append(nuevo)
    return normalizados


def validar_esquema(registros):
    """Comprueba que todos los registros tengan los campos necesarios."""
    for numero, registro in enumerate(registros, start=1):
        faltantes = [c for c in CAMPOS_REQUERIDOS if c not in registro]
        if faltantes:
            raise ValueError(
                f"El registro {numero} no tiene los campos: {', '.join(faltantes)}. "
                f"Campos esperados: {', '.join(CAMPOS_REQUERIDOS)}"
            )
            