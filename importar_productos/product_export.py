import csv
import xmlrpc.client

# Configura los detalles de tu instancia de Odoo
url = 'http://192.168.192.131:8069'
db = 'test2'
username = 'admin'
password = 'bgt56yhn*971'

# Conecta al servidor
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Define los campos que quieres descargar
fields = [
    'id', 'name', 'type', 'categ_id', 'list_price', 'sale_margin', 
    'standard_price', 'currency_id', 'available_in_pos', 'pos_categ_id', 
    'public_categ_ids', 'taxes_id', 'supplier_taxes_id', 'image_1920'
]

# Busca los productos
product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[]])
products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': fields})

# Mapea los campos para que coincidan con los nombres del CSV
mapped_fields = {
    'id': 'id',
    'name': 'name',
    'type': 'type',
    'categ_id': 'categ_id',
    'list_price': 'list_price_type',
    'sale_margin': 'sale_margin',
    'standard_price': 'replenishment_base_cost',
    'currency_id': 'replenishment_base_cost_currency_id',
    'available_in_pos': 'available_in_pos',
    'pos_categ_id': 'pos_categ_id',
    'public_categ_ids': 'public_categ_ids',
    'taxes_id': 'taxes_id',
    'supplier_taxes_id': 'supplier_taxes_id',
    'image_1920': 'image_1920'
}

def format_field(field_value):
    if isinstance(field_value, list):
        return ', '.join(str(v) for v in field_value) if field_value else ''
    return field_value

# Procesa los productos para el CSV
csv_data = []
for product in products:
    row = {}
    for field in fields:
        if field in ['pos_categ_id', 'public_categ_ids', 'taxes_id', 'supplier_taxes_id']:
            row[mapped_fields[field]] = format_field(product.get(field))
        else:
            row[mapped_fields[field]] = product.get(field)
    csv_data.append(row)

# Escribe los datos en un archivo CSV
with open('productos.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=mapped_fields.values())
    writer.writeheader()
    for row in csv_data:
        writer.writerow(row)

print("CSV guardado exitosamente.")
