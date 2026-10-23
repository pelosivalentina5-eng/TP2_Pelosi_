"""Pruebas del programa. Se ejecutan desde la carpeta del proyecto con:

    python -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from fuentes import ErrorLectura, FuenteCSV, FuenteJSON, fuente_para  # noqa: E402
from modelo import ConsultaStock, Movimiento, Producto, StockInsuficiente  # noqa: E402
from pipeline import (  # noqa: E402
    calcular_stock,
    limpiar_datos,
    normalizar_campos,
    reporte_reposicion,
    reporte_stock,
    resumen_periodo,
    validar_esquema,
    verificar_resultado,
)
from validacion import validar_codigo, validar_fecha  # noqa: E402


def mov(numero, fecha, codigo, tipo, bultos):
    """Arma un registro como los que vienen del archivo."""
    return {"id": f"MOV-{numero:05d}", "fecha": fecha, "codigo": codigo,
            "tipo": tipo, "bultos": bultos}


def procesar(registros, **parametros):
    consulta = ConsultaStock(**parametros)
    validos, rechazos = limpiar_datos(normalizar_campos(registros))
    productos, rechazos_stock = calcular_stock(validos, consulta)
    return productos, rechazos + rechazos_stock


class TestCasosNormales(unittest.TestCase):
    """1. Casos normales: datos conocidos dan resultados que se calculan a mano."""

    def test_stock_con_movimientos_conocidos(self):
        datos = [
            mov(1, "2026-09-01", "45X60-P", "PRODUCCION", 250),
            mov(2, "2026-09-02", "45X60-P", "DESPACHO", 20),
            mov(3, "2026-09-03", "60X90-S", "PRODUCCION", 70),
        ]
        productos, rechazos = procesar(datos)
        self.assertEqual(rechazos, [])
        self.assertEqual(productos["45X60-P"].stock, 230)
        self.assertEqual(productos["60X90-S"].stock, 70)
        self.assertEqual(productos["90X120-P"].stock, 0)

    def test_conversion_a_pallets(self):
        # 230 bultos de 45X60 (100 por pallet) son 2 pallets y 30 sueltos
        productos, _ = procesar([mov(1, "2026-09-01", "45X60-P", "PRODUCCION", 230)])
        self.assertEqual(productos["45X60-P"].pallets(), (2, 30))
        # 70 bultos de 60X90 (70 por pallet) son exactamente 1 pallet
        productos, _ = procesar([mov(1, "2026-09-01", "60X90-S", "PRODUCCION", 70)])
        self.assertEqual(productos["60X90-S"].pallets(), (1, 0))

    def test_fecha_de_corte(self):
        datos = [
            mov(1, "2026-09-01", "80X110-P", "PRODUCCION", 100),
            mov(2, "2026-10-01", "80X110-P", "PRODUCCION", 50),
        ]
        productos, _ = procesar(datos, fecha_corte="2026-09-30")
        self.assertEqual(productos["80X110-P"].stock, 100)

    def test_reposicion(self):
        # Mínimo de 90X120-P: 2 pallets x 50 = 100 bultos
        productos, _ = procesar([mov(1, "2026-09-01", "90X120-P", "PRODUCCION", 60)])
        filas = {f["codigo"]: f for f in reporte_reposicion(productos)}
        self.assertEqual(filas["90X120-P"]["faltan_bultos"], 40)

    def test_resumen_por_linea(self):
        datos = [
            mov(1, "2026-09-01", "45X60-P", "PRODUCCION", 30),
            mov(2, "2026-09-01", "45X60-S", "PRODUCCION", 10),
            mov(3, "2026-09-02", "45X60-S", "DESPACHO", 4),
        ]
        validos, _ = limpiar_datos(datos)
        resumen = {f["linea"]: f for f in resumen_periodo(validos, ConsultaStock())}
        self.assertEqual(resumen["Premium"]["producido"], 30)
        self.assertEqual(resumen["Segunda línea"]["producido"], 10)
        self.assertEqual(resumen["Segunda línea"]["despachado"], 4)

    def test_normaliza_minusculas_y_espacios(self):
        productos, rechazos = procesar([mov(1, " 2026-09-01 ", " 45x60-p", "produccion", "15")])
        self.assertEqual(rechazos, [])
        self.assertEqual(productos["45X60-P"].stock, 15)


if __name__ == "__main__":
    unittest.main()
    