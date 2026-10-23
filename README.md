# Control de stock de una fábrica de bolsas

**Trabajo Práctico 2 – Programación Orientada a Datos (UCA, 2026)**
**Autora:** Valentina Pelosi

## Problema

Una fábrica de bolsas produce 5 medidas (45x60, 60x90, 80x110, 85x110 y 90x120), cada una en dos líneas de calidad: Premium y Segunda línea. La producción y los despachos se anotan en planillas, en bultos. Para saber cuánto hay de cada producto y cuántos pallets se pueden armar hay que sumar y restar a mano, lo que genera errores de carga, movimientos duplicados y despachos de mercadería que no había.

## Usuario

La persona encargada del depósito o de la logística, que necesita conocer el stock de cada producto en bultos y en pallets para planificar la producción y los despachos.

## Solución propuesta

Una aplicación de consola que importa los movimientos de producción y despacho (CSV o JSON), rechaza los registros con errores y calcula el stock de cada producto a una fecha elegida, expresado en bultos y en pallets.

## Alcance de la primera versión

- Stock por producto a una fecha de corte, en bultos y en pallets completos más bultos sueltos.
- Lista de productos por debajo del stock mínimo.
- Resumen de producción y despachos por período, comparando Premium y Segunda línea.
- Detección de despachos que dejarían el stock en negativo.

Fuera del alcance: materias primas, costos y precios, varios depósitos, clientes y pedidos.