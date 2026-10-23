"""Genera movimientos de stock simulados de la fábrica de bolsas.

Crea dos archivos con el mismo contenido: data/movimientos.csv y
data/movimientos.json. Usa una semilla fija, así cada vez que se ejecuta
produce exactamente los mismos datos.

También agrega a propósito algunos registros con errores, para probar
que el programa los detecta.

Uso (desde la carpeta del proyecto):
    python src/generar_datos.py
"""

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEMILLA = 2026
INICIO = date(2026, 9, 1)
DIAS = 61  # septiembre y octubre de 2026

MEDIDAS = ["45X60", "60X90", "80X110", "85X110", "90X120"]
LINEAS = ["P", "S"]  # P = Premium, S = Segunda línea


def generar_movimientos(rng):
    """Simula producción y despachos día por día, sin dejar stock negativo."""
    stock = {f"{m}-{l}": 0 for m in MEDIDAS for l in LINEAS}
    movimientos = []

    for d in range(DIAS):
        dia = INICIO + timedelta(days=d)
        if dia.weekday() == 6:  # los domingos la fábrica no trabaja
            continue
        for codigo in stock:
            # Producción: la línea Premium produce más que la Segunda
            maximo = 40 if codigo.endswith("-P") else 20
            if rng.random() < 0.5:
                bultos = rng.randint(5, maximo)
                stock[codigo] += bultos
                movimientos.append([dia, codigo, "PRODUCCION", bultos])
            # Despacho: nunca más de lo que hay en el depósito
            if stock[codigo] > 1 and rng.random() < 0.3:
                bultos = rng.randint(1, stock[codigo] // 2)
                stock[codigo] -= bultos
                movimientos.append([dia, codigo, "DESPACHO", bultos])

    registros = []
    for numero, (dia, codigo, tipo, bultos) in enumerate(movimientos, start=1):
        registros.append({
            "id": f"MOV-{numero:05d}",
            "fecha": dia.isoformat(),
            "codigo": codigo,
            "tipo": tipo,
            "bultos": bultos,
        })
    return registros


def agregar_errores(registros):
    """Agrega registros con problemas conocidos al final del archivo."""
    errores = [
        {"id": "MOV-90001", "fecha": "2026-09-31", "codigo": "45X60-P", "tipo": "PRODUCCION", "bultos": 10},
        {"id": "MOV-90002", "fecha": "15/10/2026", "codigo": "60X90-S", "tipo": "PRODUCCION", "bultos": 10},
        {"id": "MOV-90003", "fecha": "2026-10-05", "codigo": "45-60-P", "tipo": "DESPACHO", "bultos": 5},
        {"id": "MOV-90004", "fecha": "2026-10-06", "codigo": "50X70-P", "tipo": "PRODUCCION", "bultos": 8},
        {"id": "MOV-90005", "fecha": "2026-10-07", "codigo": "80X110-P", "tipo": "VENTA", "bultos": 3},
        {"id": "MOV-90006", "fecha": "2026-10-08", "codigo": "85X110-S", "tipo": "DESPACHO", "bultos": -4},
        {"id": "MOV-90007", "fecha": "2026-10-09", "codigo": "90X120-S", "tipo": "PRODUCCION", "bultos": "diez"},
        {"id": "MOV-90008", "fecha": "2026-10-30", "codigo": "90X120-P", "tipo": "DESPACHO", "bultos": 900},
        {"id": "MOV-90009", "fecha": "2026-10-30", "codigo": "60X90-P", "tipo": "PRODUCCION", "bultos": 5000},
    ]
    duplicado = dict(registros[20])  # un movimiento cargado dos veces
    return registros + errores + [duplicado]


def guardar(registros, carpeta):
    carpeta.mkdir(exist_ok=True)
    with open(carpeta / "movimientos.json", "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=2)
    with open(carpeta / "movimientos.csv", "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=["id", "fecha", "codigo", "tipo", "bultos"])
        escritor.writeheader()
        escritor.writerows(registros)


def main():
    rng = random.Random(SEMILLA)
    registros = agregar_errores(generar_movimientos(rng))
    carpeta = Path(__file__).resolve().parent.parent / "data"
    guardar(registros, carpeta)
    print(f"Se generaron {len(registros)} movimientos en la carpeta {carpeta}")


if __name__ == "__main__":
    main()