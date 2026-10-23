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




class TestEntradasInvalidas(unittest.TestCase):
    """2. Entradas inválidas y casos límite."""

    def test_regex_del_codigo(self):
        self.assertEqual(validar_codigo("90X120-S"), ("90X120", "S"))
        for texto in ["45-60-P", "45X60", "45X60-X", "45X60-PP", "4X60-P", ""]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    validar_codigo(texto)

    def test_medida_con_formato_valido_pero_inexistente(self):
        with self.assertRaisesRegex(ValueError, "no se fabrica"):
            Producto("50X70-P")

    def test_fecha_inexistente(self):
        with self.assertRaisesRegex(ValueError, "inexistente"):
            validar_fecha("2026-09-31")
        with self.assertRaisesRegex(ValueError, "formato"):
            validar_fecha("15/10/2026")

    def test_registros_invalidos_se_rechazan_con_motivo(self):
        datos = [
            mov(1, "2026-09-31", "45X60-P", "PRODUCCION", 10),
            mov(2, "2026-09-01", "45-60-P", "PRODUCCION", 10),
            mov(3, "2026-09-01", "45X60-P", "VENTA", 10),
            mov(4, "2026-09-01", "45X60-P", "PRODUCCION", -1),
            mov(5, "2026-09-01", "45X60-P", "PRODUCCION", 0),
            mov(6, "2026-09-01", "45X60-P", "PRODUCCION", "diez"),
            mov(7, "2026-09-01", "45X60-P", "PRODUCCION", 5000),
            {"id": "M-1", "fecha": "2026-09-01", "codigo": "45X60-P", "tipo": "PRODUCCION", "bultos": 1},
        ]
        productos, rechazos = procesar(datos)
        self.assertEqual(len(rechazos), 8)
        self.assertTrue(all(r["motivo"] for r in rechazos))
        self.assertEqual(productos["45X60-P"].stock, 0)

    def test_id_duplicado_se_cuenta_una_vez(self):
        datos = [mov(1, "2026-09-01", "45X60-P", "PRODUCCION", 10)] * 2
        productos, rechazos = procesar(datos)
        self.assertEqual(productos["45X60-P"].stock, 10)
        self.assertEqual(rechazos[0]["motivo"], "id duplicado")

    def test_despacho_mayor_al_stock_se_rechaza(self):
        datos = [
            mov(1, "2026-09-01", "85X110-S", "PRODUCCION", 10),
            mov(2, "2026-09-02", "85X110-S", "DESPACHO", 11),
        ]
        productos, rechazos = procesar(datos)
        self.assertEqual(productos["85X110-S"].stock, 10)
        self.assertIn("stock insuficiente", rechazos[0]["motivo"])

    def test_despachar_exactamente_todo_el_stock(self):
        datos = [
            mov(1, "2026-09-01", "85X110-S", "PRODUCCION", 10),
            mov(2, "2026-09-02", "85X110-S", "DESPACHO", 10),
        ]
        productos, rechazos = procesar(datos)
        self.assertEqual(productos["85X110-S"].stock, 0)
        self.assertEqual(rechazos, [])

    def test_el_orden_del_archivo_no_importa(self):
        # El despacho aparece primero en el archivo, pero es de una fecha posterior
        datos = [
            mov(2, "2026-09-05", "45X60-S", "DESPACHO", 5),
            mov(1, "2026-09-01", "45X60-S", "PRODUCCION", 20),
        ]
        productos, rechazos = procesar(datos)
        self.assertEqual(productos["45X60-S"].stock, 15)
        self.assertEqual(rechazos, [])

    def test_registrar_directo_lanza_error(self):
        producto = Producto("45X60-P")
        with self.assertRaises(StockInsuficiente):
            producto.registrar(Movimiento("MOV-00001", date(2026, 9, 1), "45X60-P", "DESPACHO", 1))

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            ConsultaStock(desde="2026-10-01", hasta="2026-09-01")
        with self.assertRaises(ValueError):
            ConsultaStock(fecha_corte="30-09-2026")
        with self.assertRaises(ValueError):
            ConsultaStock(codigo="50X70-P")

    def test_falta_un_campo(self):
        with self.assertRaisesRegex(ValueError, "bultos"):
            validar_esquema([{"id": "MOV-00001", "fecha": "2026-09-01", "codigo": "45X60-P", "tipo": "DESPACHO"}])

    def test_archivos_con_problemas(self):
        with self.assertRaises(ErrorLectura):
            FuenteJSON().cargar("no_existe.json")
        with self.assertRaises(ErrorLectura):
            fuente_para("movimientos.xlsx")
        with tempfile.TemporaryDirectory() as carpeta:
            roto = Path(carpeta) / "roto.json"
            roto.write_text('[{"id": ', encoding="utf-8")
            with self.assertRaises(ErrorLectura):
                FuenteJSON().cargar(roto)
            objeto = Path(carpeta) / "objeto.json"
            objeto.write_text(json.dumps({"id": "MOV-00001"}), encoding="utf-8")
            with self.assertRaises(ErrorLectura):
                FuenteJSON().cargar(objeto)


if __name__ == "__main__":
    unittest.main()
    