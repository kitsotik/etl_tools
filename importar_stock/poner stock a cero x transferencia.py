import xmlrpc.client
import datetime

# Datos de conexión a Odoo
url = 'http://localhost:8069'
db = 'o16db'
username = 'admin'
password = 'bgt56yhn*971'

# ID de ubicaciones en Odoo
location_virtual_id = 14  # Virtual Locations/Inventory adjustment
location_default_id = 8  # WH/Stock

# Conexión a Odoo utilizando XML-RPC
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Creación del picking
values = {
    'picking_type_id': 1,  # ID del tipo de picking
    'location_id': location_virtual_id,
    'location_dest_id': location_default_id,
    'move_type': 'direct',
}
picking_id = models.execute_kw(db, uid, password, 'stock.picking', 'create', [values])

# Búsqueda de todos los productos almacenables en Odoo
product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['type', '=', 'product']]])
if not product_ids:
    print('No se encontraron productos almacenables.')
    exit()

for product_id in product_ids:
    # Obtener información del producto
    product = models.execute_kw(db, uid, password, 'product.product', 'read', [product_id, ['name', 'uom_id']])[0]
    product_name = product['name']
    uom_id = product['uom_id'][0]

    # Obtener el stock actual del producto en la ubicación predeterminada
    stock_quant = models.execute_kw(db, uid, password, 'stock.quant', 'search_read', 
                                    [[['product_id', '=', product_id], ['location_id', '=', location_default_id]]], 
                                    {'fields': ['quantity']})
    
    if not stock_quant:
        print('No se encontró stock para el producto "{}" en la ubicación predeterminada.'.format(product_name))
        continue
    
    current_stock = stock_quant[0]['quantity']
    
    if current_stock <= 0:
        # Si el stock es cero o menor, no hacer nada
        print('El producto "{}" ya tiene stock cero.'.format(product_name))
        continue
    
    # Creación del movimiento de stock para reducir el stock actual a cero
    more_values = {
        'name': 'Movimiento de stock XMLRPC',
        'product_id': product_id,
        'product_uom_qty': current_stock,  # Cantidad a mover
        'product_uom': uom_id,
        'location_id': location_default_id,
        'location_dest_id': location_virtual_id,
        'picking_id': picking_id,
    }

    try:        
        # Creación del movimiento de stock
        move_id = models.execute_kw(db, uid, password, 'stock.move', 'create', [more_values])

        print('Se ha creado el movimiento de stock para el producto "{}" para ajustar su stock a cero.'.format(product_name))
    
    except Exception as e:
        print('Error al crear el movimiento de stock para el producto "{}": {}'.format(product_name, e))

# Cambiar el estado de la transferencia a "por hacer"
models.execute_kw(db, uid, password, 'stock.picking', 'action_confirm', [picking_id])

# Buscar los movimientos del picking
move_ids = models.execute_kw(db, uid, password, 'stock.move', 'search_read', [[['picking_id', '=', picking_id]], ['product_uom_qty', 'quantity_done']])

# Iterar sobre los movimientos
for move in move_ids:
    qty_demanded = move['product_uom_qty']
    qty_done = move['quantity_done']

    # Verificar si la cantidad hecha es menor que la cantidad demandada
    if qty_done < qty_demanded:
        # Establecer la cantidad hecha como la cantidad demandada
        models.execute_kw(db, uid, password, 'stock.move', 'write', [[move['id']], {'quantity_done': qty_demanded}])

# Validar la transferencia
models.execute_kw(db, uid, password, 'stock.picking', 'button_validate', [[picking_id]])

print('El stock de todos los productos almacenables se ha ajustado a cero.')
