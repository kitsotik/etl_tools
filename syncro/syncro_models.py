import xmlrpc.client

# Datos de conexión para la instancia de Odoo de origen
url_origen = 'http://odoo.local:8069'
db_origen = 'test1'
username_origen = 'admin'
password_origen = 'bgt56yhn*971'

# Datos de conexión para la instancia de Odoo de destino
url_destino = 'http://192.168.192.132:8069'
db_destino = 'test1'
username_destino = 'admin'
password_destino = 'bgt56yhn*971'

def connect_to_odoo(url, db, username, password):
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return uid, models

def get_non_relational_fields(models, uid, db, password, model):
    fields = models.execute_kw(db, uid, password, 'ir.model.fields', 'search_read', [[('model', '=', model)]], {'fields': ['name', 'ttype']})
    non_relational_fields = [field['name'] for field in fields if field['ttype'] not in ('many2one', 'one2many', 'many2many', 'reference')]
    return non_relational_fields

def get_product_ids(models, uid, db, password):
    return models.execute_kw(db, uid, password, 'product.product', 'search', [[]])

def get_product(models, uid, db, password, product_id, fields):
    product = models.execute_kw(db, uid, password, 'product.product', 'read', [[product_id], fields])
    if product:
        product = product[0]
        # Eliminar campo 'id' y 'internal_code' del producto para evitar problemas de unicidad
        product.pop('id', None)
        product.pop('internal_code', None)
    return product

def create_or_update_product(models, uid, db, password, product):
    existing_product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[('name', '=', product['name'])]])
    
    product_data = {key: value for key, value in product.items() if key not in ('id', 'internal_code')}  # Eliminar campos 'id' e 'internal_code'
    
    if existing_product_ids:
        models.execute_kw(db, uid, password, 'product.product', 'write', [existing_product_ids, product_data])
        print(f"Producto '{product['name']}' actualizado correctamente.")
    else:
        models.execute_kw(db, uid, password, 'product.product', 'create', [product_data])
        print(f"Producto '{product['name']}' creado correctamente.")

def sync_products():
    uid_origen, models_origen = connect_to_odoo(url_origen, db_origen, username_origen, password_origen)
    uid_destino, models_destino = connect_to_odoo(url_destino, db_destino, username_destino, password_destino)

    # Obtener todos los campos no relacionales del modelo product.product
    fields = get_non_relational_fields(models_origen, uid_origen, db_origen, password_origen, 'product.product')

    # Obtener todos los IDs de los productos de la base de datos de origen
    product_ids = get_product_ids(models_origen, uid_origen, db_origen, password_origen)

    for product_id in product_ids:
        try:
            # Obtener datos del producto
            product = get_product(models_origen, uid_origen, db_origen, password_origen, product_id, fields)
            if product:
                create_or_update_product(models_destino, uid_destino, db_destino, password_destino, product)
            else:
                print(f"Producto con ID '{product_id}' no encontrado en la base de datos de origen.")
        except Exception as e:
            print(f"Error al sincronizar el producto con ID '{product_id}': {e}")

if __name__ == "__main__":
    sync_products()
