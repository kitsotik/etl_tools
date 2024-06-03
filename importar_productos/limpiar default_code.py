import xmlrpc.client

# Datos de conexión a Odoo
url = 'http://localhost:8069'
db = 'o16db'
username = 'admin'
password = 'bgt56yhn*971'

# Conectar a Odoo
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

if uid:
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # Buscar todos los productos
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[]])

    # Actualizar el campo 'default_code' (Referencia interna) a vacío
    models.execute_kw(db, uid, password, 'product.product', 'write', [product_ids, {'default_code': ''}])

    print("El campo 'Referencia interna' se ha dejado en blanco para todos los productos.")
else:
    print("Error de autenticación. Verifica tus credenciales.")
