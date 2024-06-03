# hacel a imprtacion de los stock de los articulos y ademas hace el movimiento de almacen.

import xmlrpc.client
import openpyxl
import datetime

# Datos de conexión a Odoo
url = 'http://localhost:8069'
db = 'o16db'
username = 'admin'
password = 'bgt56yhn*971'

# ID de ubicaciones en Odoo
location_virtual_id = 14 # Virtual Locations/Inventory adjustment
location_default_id = 8 # WH/Stock

# Conexión a Odoo utilizando XML-RPC
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Lectura de datos desde el archivo Excel
workbook = openpyxl.load_workbook('_stock.xlsx')
sheet = workbook['Sheet1']

# Creación del picking
values = {
    'picking_type_id': 1, # ID del tipo de picking
    'location_id': location_virtual_id,
    'location_dest_id': location_default_id,
    'move_type': 'direct',
}
picking_id = models.execute_kw(db, uid, password, 'stock.picking', 'create', [values])

for row in sheet.iter_rows(min_row=2, values_only=True):
    product_name = row[0]
    quantity = row[1]
    uom_name = row[2]

    # Búsqueda del ID del producto en Odoo
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', '=', product_name]]])
    if not product_ids:
        print('No se encontró el producto {}'.format(product_name))
        continue
    product_id = product_ids[0]

    # Obtener información del producto para verificar si es almacenable
    product = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids, ['type']])[0]
    if product['type'] != 'product':  # Solo procesar productos almacenable
        print('El producto "{}" no es almacenable'.format(product_name))
        continue

    # Búsqueda del ID del UoM en Odoo
    uom_ids = models.execute_kw(db, uid, password, 'uom.uom', 'search', [[['name', '=', uom_name]]])
    if not uom_ids:
        print('No se encontró el UoM {}'.format(uom_name))
        continue
    uom_id = uom_ids[0]

    # Creación del movimiento de stock
    more_values = {
        'name': 'Movimiento de stock XMLRPC',
        'product_id': product_id,
        'product_uom_qty': quantity,
        'product_uom': uom_id,
        'location_id': location_virtual_id,
        'location_dest_id': location_default_id,
        'picking_id': picking_id,
    }

    try:        
        # Creación del movimiento de stock
        move_id = models.execute_kw(db, uid, password, 'stock.move', 'create', [more_values])

        print('Se ha creado el movimiento de stock para el producto "{}"'.format(product_name))
    
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
