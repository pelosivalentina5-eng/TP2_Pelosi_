"""Punto de entrada: calcula el stock de la fábrica de bolsas y genera los reportes.

Ejemplos (desde la carpeta del proyecto):
    python src/main.py data/movimientos.json
    python src/main.py data/movimientos.csv --fecha-corte 2026-09-30
    python src/main.py data/movimientos.json --codigo 45X60-P
"""

import argparse
import sys
from pathlib import Path

from fuentes import ErrorLectura, fuente_para
from modelo import ConsultaStock
from pipeline import (
    calcular_stock,
    guardar_csv,
    limpiar_datos,
    normalizar_campos,
    reporte_reposicion,
    reporte_stock,
    resumen_periodo,
    validar_esquema,
    verificar_resultado,
)


def leer_argumentos():
    parser = argparse.ArgumentParser(description="Control de stock de una fábrica de bolsas.")
    parser.add_argument("entrada", help="archivo de movimientos (.csv o .json)")
    parser.add_argument("--fecha-corte", help="calcular el stock a esta fecha, AAAA-MM-DD (por defecto, todo)")
    parser.add_argument("--desde", help="inicio del período del resumen, AAAA-MM-DD")
    parser.add_argument("--hasta", help="fin del período del resumen, AAAA-MM-DD")
    parser.add_argument("--codigo", help="mostrar solo un producto, por ejemplo 45X60-P")
    parser.add_argument("--salida", default="outputs", help="carpeta para los archivos de salida")
    return parser.parse_args()


def mostrar(stock, reposicion, resumen, leidos, rechazados, consulta):
    corte = consulta.fecha_corte or "último movimiento"
    print(f"\nMovimientos leídos: {leidos}  |  rechazados: {rechazados}")
    print(f"Stock al {corte}\n")
    print(f"{'Código':<10} {'Línea':<14} {'Bultos':>7} {'Pallets':>8} {'Sueltos':>8} {'Mínimo':>7}  Reponer")
    for f in stock:
        print(f"{f['codigo']:<10} {f['linea']:<14} {f['stock_bultos']:>7} "
              f"{f['pallets_completos']:>8} {f['bultos_sueltos']:>8} {f['stock_minimo']:>7}  {f['reponer']}")

    if not consulta.codigo:
        print("\nPara producir (debajo del mínimo):")
        if not reposicion:
            print("  Ningún producto está debajo del mínimo.")
        for f in reposicion:
            print(f"  {f['codigo']:<10} faltan {f['faltan_bultos']} bultos")

    print("\nResumen del período por línea:")
    for f in resumen:
        print(f"  {f['linea']:<14} producido: {f['producido']:>5}  despachado: {f['despachado']:>5}")


def main():
    args = leer_argumentos()
    try:
        consulta = ConsultaStock(args.fecha_corte, args.desde, args.hasta, args.codigo)
        datos = fuente_para(args.entrada).cargar(args.entrada)
        datos = normalizar_campos(datos)
        validar_esquema(datos)
        movimientos, rechazos = limpiar_datos(datos)
        productos, rechazos_stock = calcular_stock(movimientos, consulta)
        verificar_resultado(productos)
    except (ErrorLectura, ValueError) as error:
        print(f"Error: {error}")
        return 1

    rechazos += rechazos_stock
    stock = reporte_stock(productos, consulta.codigo)
    reposicion = reporte_reposicion(productos)
    resumen = resumen_periodo(movimientos, consulta)

    carpeta = Path(args.salida)
    guardar_csv(stock, carpeta / "stock.csv", list(stock[0].keys()))
    guardar_csv(reposicion, carpeta / "reposicion.csv",
                ["codigo", "stock_bultos", "stock_minimo", "faltan_bultos"])
    guardar_csv(resumen, carpeta / "resumen_lineas.csv",
                ["linea", "producido", "despachado", "movimientos"])
    guardar_csv(rechazos, carpeta / "rechazados.csv",
                ["fila", "motivo", "id", "fecha", "codigo", "tipo", "bultos"])

    mostrar(stock, reposicion, resumen, len(datos), len(rechazos), consulta)
    print(f"\nArchivos guardados en la carpeta {carpeta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    