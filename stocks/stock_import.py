import csv
import xmlrpc.client
import datetime

# Datos de conexión a Odoo
url = 'http://odoo.local:8069'
db = 'test1'
username = 'admin'
password = 'bgt56yhn*971'

# ID de ubicaciones en Odoo
location_virtual_id = 14  # Virtual Locations/Inventory adjustment
location_default_id = 8   # WH/Stock

# Archivo CSV
csv_file_path = 'stock.csv'

def connect_to_odoo(url, db, username, password):
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    return uid, models

def create_picking(models, db, uid, password, location_virtual_id, location_default_id):
    picking_values = {
        'picking_type_id': 1,  # ID del tipo de picking
        'location_id': location_virtual_id,
        'location_dest_id': location_default_id,
        'move_type': 'direct',
    }
    return models.execute_kw(db, uid, password, 'stock.picking', 'create', [picking_values])

def process_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product_name = row['Nombre']
            quantity = row['Cantidad a mano']
            uom_name = row['Unidad de medida']
            # Convertir "Unidades" a "Units"
            if uom_name.lower() == 'unidades':
                uom_name = 'Units'
            yield product_name, quantity, uom_name

def get_product_id(models, db, uid, password, product_name):
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['name', '=', product_name]]])
    return product_ids[0] if product_ids else None

def get_uom_id(models, db, uid, password, uom_name):
    uom_ids = models.execute_kw(db, uid, password, 'uom.uom', 'search', [[['name', '=', uom_name]]])
    return uom_ids[0] if uom_ids else None

def create_stock_move(models, db, uid, password, product_id, quantity, uom_id, location_virtual_id, location_default_id, picking_id):
    move_values = {
        'name': 'Movimiento de stock XMLRPC',
        'product_id': product_id,
        'product_uom_qty': quantity,
        'product_uom': uom_id,
        'location_id': location_virtual_id,
        'location_dest_id': location_default_id,
        'picking_id': picking_id,
    }
    return models.execute_kw(db, uid, password, 'stock.move', 'create', [move_values])

def main():
    uid, models = connect_to_odoo(url, db, username, password)
    if not uid:
        print("Error en la autenticación con Odoo")
        return
    
    picking_id = create_picking(models, db, uid, password, location_virtual_id, location_default_id)
    
    for product_name, quantity, uom_name in process_csv(csv_file_path):
        product_id = get_product_id(models, db, uid, password, product_name)
        if not product_id:
            print(f'No se encontró el producto {product_name}')
            continue
        
        product = models.execute_kw(db, uid, password, 'product.product', 'read', [product_id, ['type']])[0]
        if product['type'] != 'product':  # Solo procesar productos almacenable
            print(f'El producto "{product_name}" no es almacenable')
            continue
        
        uom_id = get_uom_id(models, db, uid, password, uom_name)
        if not uom_id:
            print(f'No se encontró el UoM {uom_name}')
            continue
        
        try:
            create_stock_move(models, db, uid, password, product_id, float(quantity), uom_id, location_virtual_id, location_default_id, picking_id)
            print(f'Se ha creado el movimiento de stock para el producto "{product_name}"')
        except Exception as e:
            print(f'Error al crear el movimiento de stock para el producto "{product_name}": {e}')

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

if __name__ == '__main__':
    main()
