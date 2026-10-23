"""Validaciones de formato con expresiones regulares.

Una expresión regular solo comprueba la FORMA de un texto. Por eso, cuando
hace falta, se complementa con otra comprobación: por ejemplo, '2026-09-31'
tiene forma de fecha, pero esa fecha no existe en el calendario.
"""

import re
from datetime import datetime

# Código de producto: medida + línea, por ejemplo 45X60-P o 90X120-S
#   (\d{2})    ancho: 2 dígitos
#   X          una X mayúscula
#   (\d{2,3})  largo: 2 o 3 dígitos
#   -([PS])    guion y la línea: P (Premium) o S (Segunda línea)
PATRON_CODIGO = re.compile(r"^(\d{2})X(\d{2,3})-([PS])$")

# Identificador de movimiento: MOV- y 5 dígitos, por ejemplo MOV-00042
PATRON_ID = re.compile(r"^MOV-\d{5}$")

# Fecha en formato AAAA-MM-DD
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validar_codigo(texto):
    """Devuelve (medida, linea) a partir del código, o lanza ValueError.

    Ejemplo: '45X60-P' -> ('45X60', 'P')
    """
    coincidencia = PATRON_CODIGO.match(str(texto))
    if not coincidencia:
        raise ValueError(f"código de producto con formato inválido: {texto!r}")
    ancho, largo, linea = coincidencia.groups()
    return f"{ancho}X{largo}", linea


def validar_id(texto):
    if not PATRON_ID.match(str(texto)):
        raise ValueError(f"id de movimiento con formato inválido: {texto!r}")
    return texto


def validar_fecha(texto):
    """Convierte 'AAAA-MM-DD' en un objeto date, o lanza ValueError."""
    if not PATRON_FECHA.match(str(texto)):
        raise ValueError(f"fecha con formato inválido (se espera AAAA-MM-DD): {texto!r}")
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"fecha inexistente en el calendario: {texto!r}") from None
    