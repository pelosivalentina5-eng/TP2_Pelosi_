"""Lectura de datos: una interfaz común para archivos CSV y JSON.

FuenteDatos define el "contrato": toda fuente tiene un método cargar(ruta)
que devuelve una lista de diccionarios con los mismos campos. Así el resto
del programa no necesita saber de qué tipo de archivo vienen los datos.
"""

import csv
import json
from pathlib import Path


class ErrorLectura(Exception):
    """Error al leer un archivo: no existe, está vacío o tiene mal formato."""


class FuenteDatos:
    """Clase base. Las clases hijas solo tienen que implementar _leer()."""

    extension = ""

    def cargar(self, ruta):
        ruta = Path(ruta)
        if not ruta.exists():
            raise ErrorLectura(f"No se encontró el archivo: {ruta}")
        if ruta.suffix.lower() != self.extension:
            raise ErrorLectura(f"Se esperaba un archivo {self.extension}, pero llegó {ruta.name}")
        registros = self._leer(ruta)
        if len(registros) == 0:
            raise ErrorLectura(f"El archivo {ruta.name} no tiene registros")
        return registros

    def _leer(self, ruta):
        raise NotImplementedError("Cada fuente tiene que implementar _leer()")


class FuenteCSV(FuenteDatos):
    """Lee un CSV con encabezado. Todos los valores llegan como texto."""

    extension = ".csv"

    def _leer(self, ruta):
        with open(ruta, encoding="utf-8", newline="") as archivo:
            return [dict(fila) for fila in csv.DictReader(archivo)]


class FuenteJSON(FuenteDatos):
    """Lee un JSON que contiene una lista de objetos."""

    extension = ".json"

    def _leer(self, ruta):
        try:
            with open(ruta, encoding="utf-8") as archivo:
                contenido = json.load(archivo)
        except json.JSONDecodeError as error:
            raise ErrorLectura(f"{ruta.name} no es un JSON válido: {error.msg}") from error
        if not isinstance(contenido, list):
            raise ErrorLectura(f"{ruta.name} debe contener una lista de movimientos")
        return contenido


def fuente_para(ruta):
    """Elige FuenteCSV o FuenteJSON según la extensión del archivo."""
    extension = Path(ruta).suffix.lower()
    if extension == ".csv":
        return FuenteCSV()
    if extension == ".json":
        return FuenteJSON()
    raise ErrorLectura(f"Formato no soportado: '{extension}'. Usá un archivo .csv o .json")
