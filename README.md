# Control de stock de una fábrica de bolsas

**Trabajo Práctico 2 – Programación Orientada a Datos (UCA, 2026)**
**Autora:** Valentina Pelosi

## Problema

Una fábrica de bolsas produce 5 medidas (45x60, 60x90, 80x110, 85x110 y 90x120), cada una en dos líneas de calidad: Premium y Segunda línea. La producción y los despachos se anotan en planillas, en bultos. Para saber cuánto hay de cada producto y cuántos pallets se pueden armar hay que sumar y restar a mano, lo que genera errores de carga, movimientos duplicados y despachos de mercadería que no había.

## Usuario

La persona encargada del depósito o de la logística, que necesita conocer el stock de cada producto en bultos y en pallets para planificar la producción y los despachos.

## Solución propuesta

Una aplicación de consola que importa los movimientos de producción y despacho (CSV o JSON), rechaza los registros con errores y calcula el stock de cada producto a una fecha elegida, expresado en bultos y en pallets.

### Funcionalidades

- Stock de los 10 productos (o de uno solo con `--codigo`) a una fecha de corte.
- Conversión del stock a pallets completos más bultos sueltos.
- Lista de productos por debajo del stock mínimo, con los bultos que faltan.
- Resumen de bultos producidos y despachados en un período, comparando Premium y Segunda línea.
- Detección de despachos que dejarían el stock en negativo.
- Archivo con todos los movimientos rechazados y el motivo de cada uno.

### Fuera del alcance de esta versión

Materias primas, costos y precios, varios depósitos, clientes y pedidos.

## Productos

Cada producto se identifica con un código: medida + línea. `P` es Premium y `S` es Segunda línea.

| Medida | Bultos por pallet | Códigos | Stock mínimo Premium | Stock mínimo Segunda |
|---|---|---|---|---|
| 45x60 | 100 | `45X60-P`, `45X60-S` | 200 bultos | 100 bultos |
| 60x90 | 70 | `60X90-P`, `60X90-S` | 140 bultos | 70 bultos |
| 80x110 | 50 | `80X110-P`, `80X110-S` | 100 bultos | 50 bultos |
| 85x110 | 50 | `85X110-P`, `85X110-S` | 100 bultos | 50 bultos |
| 90x120 | 50 | `90X120-P`, `90X120-S` | 100 bultos | 50 bultos |

Los bultos por pallet son iguales en las dos líneas. El stock mínimo es de 2 pallets para Premium y 1 pallet para Segunda línea, porque Premium es la línea que más se produce y se despacha.

## Datos

El detalle está en [`data/README.md`](data/README.md). En resumen:

- **Fuente:** datos **simulados** con `src/generar_datos.py`, con semilla fija (siempre se generan los mismos).
- **Unidad de análisis:** cada fila es un movimiento de depósito: una producción o un despacho de un producto en un día.
- **Variables:** `id`, `fecha`, `codigo`, `tipo` (`PRODUCCION` o `DESPACHO`) y `bultos`.
- **Tamaño:** 403 movimientos de septiembre y octubre de 2026, en `data/movimientos.csv` y `data/movimientos.json` (mismo contenido en los dos formatos).

## Instalación

Requiere Python 3.10 o superior. Solo usa la biblioteca estándar (`csv`, `json`, `re`, `datetime`, `random`, `argparse`, `unittest`), así que no hay que instalar nada más.

```bash
git clone https://github.com/pelosivalentina5-eng/TP2_Pelosi_.git
cd TP2_Pelosi_
```

## Uso

Todos los comandos se ejecutan desde la carpeta del proyecto.

```bash
# Regenerar los datos simulados (opcional: ya están en data/)
python src/generar_datos.py

# Stock actual de todos los productos
python src/main.py data/movimientos.json

# Stock al 30 de septiembre, leyendo el CSV, con el resumen de septiembre
python src/main.py data/movimientos.csv --fecha-corte 2026-09-30 --desde 2026-09-01 --hasta 2026-09-30

# Un solo producto
python src/main.py data/movimientos.json --codigo 45X60-P
```

| Opción | Descripción | Por defecto |
|---|---|---|
| `entrada` | archivo `.csv` o `.json` de movimientos | (obligatorio) |
| `--fecha-corte` | calcula el stock con los movimientos hasta esa fecha (`AAAA-MM-DD`) | todos |
| `--desde`, `--hasta` | período del resumen por línea, extremos incluidos | todo |
| `--codigo` | muestra solo ese producto | todos |
| `--salida` | carpeta para los archivos de salida | `outputs` |

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las 23 pruebas de `tests/test_app.py` cubren:

1. **Casos normales:** stock calculado a mano, conversión a pallets, fecha de corte, reposición, resumen por línea, normalización de mayúsculas y espacios.
2. **Entradas inválidas y casos límite:** códigos y fechas mal escritos, medida que no se fabrica, tipos desconocidos, bultos negativos, cero, no numéricos o fuera de rango, ids duplicados, despacho mayor al stock, despacho de exactamente todo el stock, movimientos desordenados en el archivo, parámetros inválidos, archivos inexistentes o mal formados.
3. **Propiedades del resultado:** CSV y JSON dan el mismo stock; ningún registro se pierde (válidos + rechazados = leídos); stock = producción − despachos y nunca negativo; pallets × bultos por pallet + sueltos = stock; mismas entradas dan el mismo resultado.

## Organización del código

```
TP2_Pelosi_/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py            # opciones de consola y coordinación del flujo
│   ├── fuentes.py         # FuenteDatos, FuenteCSV y FuenteJSON
│   ├── validacion.py      # expresiones regulares y validación de fechas
│   ├── modelo.py          # clases Producto, Movimiento y ConsultaStock
│   ├── pipeline.py        # normalizar, validar, limpiar, calcular y guardar
│   └── generar_datos.py   # genera los datos simulados
├── tests/
│   └── test_app.py
└── data/
    ├── README.md
    ├── movimientos.csv
    └── movimientos.json
```

Flujo que coordina `main.py`:

```
datos = fuente.cargar(ruta)                          # fuentes.py
datos = normalizar_campos(datos)                     # pipeline.py
validar_esquema(datos)
movimientos, rechazos = limpiar_datos(datos)
productos, rechazos_stock = calcular_stock(movimientos, consulta)
verificar_resultado(productos)
guardar_csv(...)                                     # stock, reposición, resumen y rechazos
```

### Decisiones de diseño

- **`FuenteDatos`** es la clase base de la lectura. Su método `cargar(ruta)` comprueba que el archivo exista, que tenga la extensión correcta y que no esté vacío, y le deja la lectura concreta a cada subclase: **`FuenteCSV`** y **`FuenteJSON`**. Las dos devuelven una lista de diccionarios con los mismos campos, así el resto del programa no depende del formato.
- **`Producto`** representa un producto de la fábrica y su stock. Sabe registrar un movimiento sin quedar en negativo, convertir su stock a pallets y decir si necesita reposición. Al crearse valida que el código y la medida existan.
- **`Movimiento`** representa una producción o un despacho ya validado.
- **`ConsultaStock`** representa lo que pide la persona (fecha de corte, período, producto) y valida esos parámetros antes de procesar los datos.
- **Expresiones regulares** (`src/validacion.py`):
  - `^(\d{2})X(\d{2,3})-([PS])$` valida el código de producto y separa la medida y la línea. Como la regex acepta medidas que la fábrica no hace (por ejemplo `50X70-P`), después se comprueba que la medida exista en el catálogo.
  - `^MOV-\d{5}$` valida el identificador del movimiento.
  - `^\d{4}-\d{2}-\d{2}$` valida la forma de la fecha. Como `2026-09-31` cumple el patrón pero no existe, después se convierte con `datetime.strptime`, que comprueba el calendario.

## Ejemplo de resultado

```
$ python src/main.py data/movimientos.json

Movimientos leídos: 403  |  rechazados: 10
Stock al último movimiento

Código     Línea           Bultos  Pallets  Sueltos  Mínimo  Reponer
45X60-P    Premium            338        3       38     200  NO
45X60-S    Segunda línea       63        0       63     100  SI
60X90-P    Premium            204        2       64     140  NO
60X90-S    Segunda línea        8        0        8      70  SI
80X110-P   Premium            280        5       30     100  NO
80X110-S   Segunda línea       39        0       39      50  SI
85X110-P   Premium            162        3       12     100  NO
85X110-S   Segunda línea       64        1       14      50  NO
90X120-P   Premium            121        2       21     100  NO
90X120-S   Segunda línea       74        1       24      50  NO

Para producir (debajo del mínimo):
  60X90-S    faltan 62 bultos
  45X60-S    faltan 37 bultos
  80X110-S   faltan 11 bultos

Resumen del período por línea:
  Premium        producido:  3300  despachado:  3095
  Segunda línea  producido:  1597  despachado:  1349

Archivos guardados en la carpeta outputs
```

En `outputs/` quedan `stock.csv`, `reposicion.csv`, `resumen_lineas.csv` y `rechazados.csv`.

**Cómo se lee:** de 45X60-P hay 338 bultos, que son 3 pallets completos y 38 bultos sueltos; supera el mínimo de 200, así que no hace falta producir. En cambio, de 60X90-S quedan solo 8 bultos y faltan 62 para llegar a 1 pallet: es lo primero que conviene producir. Las tres medidas a reponer son de Segunda línea.

## Decisiones de limpieza

Cada movimiento rechazado se guarda en `outputs/rechazados.csv` con su número de fila y el motivo. No se descarta nada en silencio.

| Regla | Ejemplo | Por qué |
|---|---|---|
| El id debe ser `MOV-` y 5 dígitos | `M-1` | Sin id válido no se pueden detectar duplicados. |
| La fecha debe tener formato `AAAA-MM-DD` | `15/10/2026` | Hace falta para ordenar los movimientos y aplicar la fecha de corte. |
| La fecha debe existir | `2026-09-31` | Septiembre tiene 30 días. |
| El código debe cumplir el patrón | `45-60-P` | No se puede saber a qué producto corresponde. |
| La medida debe fabricarse | `50X70-P` | La fábrica solo hace 5 medidas. |
| El tipo debe ser `PRODUCCION` o `DESPACHO` | `VENTA` | No se sabe si suma o resta. |
| Los bultos deben ser un entero mayor que cero | `-4`, `0`, `diez` | Un movimiento siempre mueve al menos un bulto. |
| Los bultos no pueden superar 1000 | `5000` | Son más de 10 pallets en un solo movimiento: es un error de carga. |
| El id no puede repetirse | `MOV-00021` dos veces | Es un movimiento cargado dos veces; se conserva el primero. |
| Un despacho no puede superar el stock | despachar 900 si hay 112 | No se puede despachar lo que no hay. |

Además, antes de validar se normalizan los datos: se quitan espacios y el código y el tipo se pasan a mayúscula (`45x60-p` se toma como `45X60-P`). En el CSV todos los valores llegan como texto (`"37"`) y en el JSON como número (`37`); la conversión a entero los iguala.

Los movimientos se aplican en orden de fecha (y de id dentro del mismo día), no en el orden en que aparecen en el archivo. Así un despacho cargado antes que la producción del día anterior no se rechaza por error.

## Interpretación y limitaciones

- **Los datos son simulados.** Sirven para mostrar que la aplicación funciona; los números no describen una fábrica real. Con un archivo real con las mismas columnas, el programa funciona igual.
- El stock inicial de todos los productos es 0 al empezar el archivo. Para usarlo con una fábrica que ya tiene mercadería, habría que cargar primero un movimiento de producción con el stock inicial.
- Los mínimos (2 pallets Premium, 1 pallet Segunda) son una regla elegida para el TP, no un dato de la fábrica.
- Si un despacho se rechaza por falta de stock, el resto se sigue calculando sin él. En la realidad habría que revisar si fue un error de carga o si faltó registrar una producción.
- Los duplicados se detectan por id. Si el mismo movimiento se cargó dos veces con ids distintos, el programa no puede darse cuenta.
- El tope de 1000 bultos por movimiento es un criterio propio; si la fábrica hiciera movimientos más grandes, habría que cambiar `BULTOS_MAXIMOS` en `src/pipeline.py`.


Para el desarrollo usé un asistente de IA como guía.