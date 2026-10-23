# Datos

## Procedencia

| | |
|---|---|
| **Archivos** | `movimientos.csv` y `movimientos.json` (mismo contenido en dos formatos) |
| **Origen** | Datos **simulados**, generados con `python src/generar_datos.py` |
| **Responsable** | Valentina Pelosi |
| **Licencia** | Datos inventados, de libre uso |
| **Fecha de generación** | 23 de octubre de 2026 |
| **Semilla** | 2026: cada ejecución produce exactamente los mismos archivos |

### Por qué datos simulados

No se cuenta con registros reales de una fábrica de bolsas que se puedan publicar. Los datos se generaron con un programa que imita el funcionamiento del depósito:

- la fábrica trabaja de lunes a sábado;
- cada día, cada producto tiene un 50 % de probabilidad de tener producción;
- la línea Premium produce lotes de 5 a 40 bultos y la Segunda línea de 5 a 20;
- los despachos nunca superan la mitad del stock disponible ese día.

## Unidad de análisis y variables

Cada fila es **un movimiento de depósito**: una producción o un despacho de un producto en un día.

| Variable | Tipo | Descripción |
|---|---|---|
| `id` | texto `MOV-00000` | Identificador único del movimiento |
| `fecha` | texto `AAAA-MM-DD` | Día del movimiento |
| `codigo` | texto, por ejemplo `45X60-P` | Medida de la bolsa y línea (`P` Premium, `S` Segunda línea) |
| `tipo` | `PRODUCCION` o `DESPACHO` | Si los bultos entran o salen del depósito |
| `bultos` | entero | Cantidad de bultos del movimiento |

En el JSON el archivo es una lista de objetos y `bultos` es un número. En el CSV todos los valores son texto y el programa los convierte.

## Contenido

- 403 movimientos entre el 1 de septiembre y el 31 de octubre de 2026.
- 393 movimientos correctos.
- 10 movimientos con problemas agregados a propósito para probar la limpieza:

| Id | Problema |
|---|---|
| MOV-90001 | Fecha inexistente (`2026-09-31`) |
| MOV-90002 | Fecha con otro formato (`15/10/2026`) |
| MOV-90003 | Código mal escrito (`45-60-P`) |
| MOV-90004 | Medida que no se fabrica (`50X70-P`) |
| MOV-90005 | Tipo desconocido (`VENTA`) |
| MOV-90006 | Bultos negativos (`-4`) |
| MOV-90007 | Bultos no numéricos (`diez`) |
| MOV-90008 | Despacho de 900 bultos, mayor que el stock disponible |
| MOV-90009 | Producción de 5000 bultos, fuera de rango |
| MOV-00021 | Cargado dos veces (id duplicado) |

## Limitaciones

- Al ser simulados, los datos no describen una fábrica real; sirven para demostrar y probar la aplicación.
- No hay estacionalidad ni pedidos grandes de clientes: la producción y los despachos son parejos todo el período.
- El stock arranca en 0 el 1 de septiembre.