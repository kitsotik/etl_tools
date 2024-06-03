import xmlrpc.client

# Datos de conexión a Odoo
url = 'http://localhost:8069'
db = 'test2'
username = 'admin'
password = 'bgt56yhn*971'

# Autenticación
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# Crear un objeto de la API de modelos
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Consultar todas las ubicaciones (físicas y virtuales)
location_ids = models.execute_kw(
    db, uid, password,
    'stock.location', 'search', [[]]
)

# Leer la información de todas las ubicaciones
locations = models.execute_kw(
    db, uid, password,
    'stock.location', 'read',
    [location_ids], {'fields': ['id', 'barcode', 'complete_name', 'usage']}
)

# Mostrar los resultados
for location in locations:
    barcode = location.get('barcode', 'N/A')  # Obtener el código de barras o 'N/A' si no existe
    print("ID: {}, Código de Barras: {}, Nombre Completo: {}, Uso: {}".format(location['id'], barcode, location['complete_name'], location['usage']))
