"""Clases del dominio: productos, movimientos y la consulta de stock."""

from validacion import validar_codigo, validar_fecha

# Bultos que entran en un pallet según la medida de la bolsa.
# Es igual para Premium y para Segunda línea.
BULTOS_POR_PALLET = {
    "45X60": 100,
    "60X90": 70,
    "80X110": 50,
    "85X110": 50,
    "90X120": 50,
}

NOMBRES_LINEA = {"P": "Premium", "S": "Segunda línea"}

# Stock mínimo, en pallets: por debajo de esto hay que producir.
PALLETS_MINIMOS = {"P": 2, "S": 1}

TIPOS_MOVIMIENTO = ("PRODUCCION", "DESPACHO")


class StockInsuficiente(Exception):
    """Se intentó despachar más bultos de los que hay en el depósito."""


class Producto:
    """Un producto de la fábrica (una medida en una línea) y su stock en bultos."""

    def __init__(self, codigo):
        self.codigo = codigo
        self.medida, self.linea = validar_codigo(codigo)
        if self.medida not in BULTOS_POR_PALLET:
            raise ValueError(f"la medida {self.medida} no se fabrica")
        self.bultos_por_pallet = BULTOS_POR_PALLET[self.medida]
        self.stock_minimo = PALLETS_MINIMOS[self.linea] * self.bultos_por_pallet
        self.stock = 0
        self.producido = 0
        self.despachado = 0

    def nombre_linea(self):
        return NOMBRES_LINEA[self.linea]

    def registrar(self, movimiento):
        """Suma o resta los bultos del movimiento. Nunca deja el stock negativo."""
        if movimiento.tipo == "PRODUCCION":
            self.stock += movimiento.bultos
            self.producido += movimiento.bultos
        else:
            if movimiento.bultos > self.stock:
                raise StockInsuficiente(
                    f"stock insuficiente: se quisieron despachar {movimiento.bultos} "
                    f"bultos y había {self.stock}"
                )
            self.stock -= movimiento.bultos
            self.despachado += movimiento.bultos

    def pallets(self):
        """Devuelve (pallets completos, bultos sueltos). Ej: 230 bultos de 45X60 -> (2, 30)."""
        return divmod(self.stock, self.bultos_por_pallet)

    def necesita_reposicion(self):
        return self.stock < self.stock_minimo

    def faltante(self):
        """Bultos que faltan para llegar al stock mínimo (0 si no falta nada)."""
        return max(0, self.stock_minimo - self.stock)

    def __repr__(self):
        return f"Producto({self.codigo}, stock={self.stock})"
    
    
    

class Movimiento:
    """Un movimiento de depósito ya validado: una producción o un despacho."""

    def __init__(self, id_movimiento, fecha, codigo, tipo, bultos):
        self.id = id_movimiento
        self.fecha = fecha
        self.codigo = codigo
        self.tipo = tipo
        self.bultos = bultos

    def __repr__(self):
        return f"Movimiento({self.id}, {self.fecha}, {self.codigo}, {self.tipo}, {self.bultos})"


class ConsultaStock:
    """Lo que pide quien usa el programa. Valida los parámetros al crearse."""

    def __init__(self, fecha_corte=None, desde=None, hasta=None, codigo=None):
        self.fecha_corte = validar_fecha(fecha_corte) if fecha_corte else None
        self.desde = validar_fecha(desde) if desde else None
        self.hasta = validar_fecha(hasta) if hasta else None
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError(f"'desde' ({self.desde}) es posterior a 'hasta' ({self.hasta})")
        if codigo:
            Producto(codigo)  # lanza ValueError si el código no es válido
        self.codigo = codigo

    def incluye_en_stock(self, movimiento):
        """El stock se calcula con todos los movimientos hasta la fecha de corte."""
        return self.fecha_corte is None or movimiento.fecha <= self.fecha_corte

    def incluye_en_periodo(self, movimiento):
        """El resumen de producción y despachos usa solo el período pedido."""
        if self.desde and movimiento.fecha < self.desde:
            return False
        if self.hasta and movimiento.fecha > self.hasta:
            return False
        return True