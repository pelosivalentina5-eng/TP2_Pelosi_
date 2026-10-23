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
            


# ---------- 2. Limpiar ----------

def convertir_movimiento(registro):
    """Convierte un diccionario en Movimiento, o lanza ValueError con el motivo."""
    id_movimiento = validar_id(registro["id"])
    fecha = validar_fecha(registro["fecha"])
    producto = Producto(registro["codigo"])  # valida formato y medida

    tipo = registro["tipo"]
    if tipo not in TIPOS_MOVIMIENTO:
        raise ValueError(f"tipo de movimiento desconocido: {tipo!r}")

    try:
        bultos = int(registro["bultos"])
    except (TypeError, ValueError):
        raise ValueError(f"la cantidad de bultos no es un número entero: {registro['bultos']!r}") from None
    if bultos <= 0:
        raise ValueError(f"la cantidad de bultos debe ser mayor que cero: {bultos}")
    if bultos > BULTOS_MAXIMOS:
        raise ValueError(f"cantidad de bultos fuera de rango (más de {BULTOS_MAXIMOS}): {bultos}")

    return Movimiento(id_movimiento, fecha, producto.codigo, tipo, bultos)


def limpiar_datos(registros):
    """Separa los movimientos válidos de los rechazados.

    Devuelve (validos, rechazos). Cada rechazo guarda el número de fila
    original, el motivo y los datos, para poder revisarlo y corregirlo.
    Un id repetido se considera un movimiento cargado dos veces: se
    conserva el primero.
    """
    validos = []
    rechazos = []
    ids_vistos = set()

    for fila, registro in enumerate(registros, start=1):
        try:
            movimiento = convertir_movimiento(registro)
        except ValueError as error:
            rechazos.append({"fila": fila, "motivo": str(error), **registro})
            continue

        if movimiento.id in ids_vistos:
            rechazos.append({"fila": fila, "motivo": "id duplicado", **registro})
            continue

        ids_vistos.add(movimiento.id)
        validos.append(movimiento)

    return validos, rechazos
            