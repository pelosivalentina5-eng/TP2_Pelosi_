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

# ---------- 3. Calcular ----------

def crear_productos():
    """Crea los 10 productos de la fábrica (5 medidas x 2 líneas) con stock 0."""
    return {
        f"{medida}-{linea}": Producto(f"{medida}-{linea}")
        for medida in BULTOS_POR_PALLET
        for linea in NOMBRES_LINEA
    }


def calcular_stock(movimientos, consulta):
    """Aplica los movimientos en orden cronológico hasta la fecha de corte.

    Devuelve (productos, rechazos). Un despacho que dejaría el stock en
    negativo no se aplica y queda rechazado.
    """
    productos = crear_productos()
    rechazos = []
    ordenados = sorted(movimientos, key=lambda m: (m.fecha, m.id))

    for movimiento in ordenados:
        if not consulta.incluye_en_stock(movimiento):
            continue
        try:
            productos[movimiento.codigo].registrar(movimiento)
        except StockInsuficiente as error:
            rechazos.append({
                "fila": "",
                "motivo": str(error),
                "id": movimiento.id,
                "fecha": str(movimiento.fecha),
                "codigo": movimiento.codigo,
                "tipo": movimiento.tipo,
                "bultos": movimiento.bultos,
            })
    return productos, rechazos


def verificar_resultado(productos):
    """Comprueba que los resultados sean coherentes; si no, hay un error de cálculo."""
    for p in productos.values():
        if p.stock < 0:
            raise AssertionError(f"{p.codigo} quedó con stock negativo")
        if p.stock != p.producido - p.despachado:
            raise AssertionError(f"{p.codigo}: stock distinto de producido - despachado")
        completos, sueltos = p.pallets()
        if completos * p.bultos_por_pallet + sueltos != p.stock:
            raise AssertionError(f"{p.codigo}: la conversión a pallets no conserva los bultos")
                    

                    


def reporte_stock(productos, codigo=None):
    """Tabla de stock por producto, en bultos y en pallets."""
    filas = []
    for producto in productos.values():
        if codigo and producto.codigo != codigo:
            continue
        completos, sueltos = producto.pallets()
        filas.append({
            "codigo": producto.codigo,
            "medida": producto.medida,
            "linea": producto.nombre_linea(),
            "stock_bultos": producto.stock,
            "pallets_completos": completos,
            "bultos_sueltos": sueltos,
            "stock_minimo": producto.stock_minimo,
            "reponer": "SI" if producto.necesita_reposicion() else "NO",
        })
    return filas


def reporte_reposicion(productos):
    """Productos por debajo del mínimo, del que más falta al que menos."""
    filas = [
        {
            "codigo": p.codigo,
            "stock_bultos": p.stock,
            "stock_minimo": p.stock_minimo,
            "faltan_bultos": p.faltante(),
        }
        for p in productos.values()
        if p.necesita_reposicion()
    ]
    return sorted(filas, key=lambda f: (-f["faltan_bultos"], f["codigo"]))


def resumen_periodo(movimientos, consulta):
    """Bultos producidos y despachados por línea dentro del período pedido."""
    resumen = {
        nombre: {"linea": nombre, "producido": 0, "despachado": 0, "movimientos": 0}
        for nombre in NOMBRES_LINEA.values()
    }
    for movimiento in movimientos:
        if not consulta.incluye_en_periodo(movimiento):
            continue
        if consulta.fecha_corte and movimiento.fecha > consulta.fecha_corte:
            continue
        linea = NOMBRES_LINEA[movimiento.codigo[-1]]
        clave = "producido" if movimiento.tipo == "PRODUCCION" else "despachado"
        resumen[linea][clave] += movimiento.bultos
        resumen[linea]["movimientos"] += 1
    return list(resumen.values())


# ---------- 4. Guardar ----------

def guardar_csv(filas, ruta, campos):
    """Guarda una lista de diccionarios como CSV. Crea la carpeta si no existe."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)
        