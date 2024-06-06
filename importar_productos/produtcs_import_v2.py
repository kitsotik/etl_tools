import xmlrpc.client
import csv
csv.field_size_limit(1000000)

# Por tema acentos y eñes
xmlrpc.client.Transport.use_unicode = True 

url = 'http://odoo.local:8069'
db = 'o16db'
username = 'admin'
password = 'bgt56yhn*971'

list_price_type_translate = {
    'By Margin': 'by_margin',
    'Fixed value': 'manual',
    # Agregar otras categorías según sea necesario
}
type_product_translate = {
    'Almacenable': 'product',
    'Servicio': 'service',
    'consu': 'consu',
}

class OdooAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    def create_products(self, products):
        product_ids = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'create', [products])
        return product_ids

odoo = OdooAPI(url, db, username, password)

# Pre-fetch IDs for categories, currencies, POS categories, etc.
def fetch_id(model, field, value):
    result = odoo.models.execute_kw(db, odoo.uid, odoo.password, model, 'search', [[(field, '=', value)]], {'limit': 1})
    return result[0] if result else None

categories = {}
currencies = {}
pos_categories = {}
public_categories = {}
taxes = {}
supplier_taxes = {}

with open('productos.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    next(reader)  # Skip header row
    products = []
    for row in reader:
        default_code = row[0]
        product_name = row[1]
        type_product = type_product_translate.get(row[2], '')
        category_name = row[3]
        list_price_type = list_price_type_translate.get(row[4], '')
        sale_margin = row[5]
        replenishment_base_cost = row[6]
        replenishment_base_cost_currency = row[7]
        available_in_pos = row[8]
        pos_categ_name = row[9]
        public_categ_name = row[10]
        taxes_name = row[11]
        supplier_taxes_name = row[12]
        image_1920 = row[13]

        if category_name not in categories:
            categories[category_name] = fetch_id('product.category', 'complete_name', category_name)
        if replenishment_base_cost_currency not in currencies:
            currencies[replenishment_base_cost_currency] = fetch_id('res.currency', 'name', replenishment_base_cost_currency)
        if pos_categ_name not in pos_categories:
            pos_categories[pos_categ_name] = fetch_id('pos.category', 'name', pos_categ_name)
        if public_categ_name not in public_categories:
            public_categories[public_categ_name] = fetch_id('product.public.category', 'name', public_categ_name)
        if taxes_name not in taxes:
            taxes[taxes_name] = fetch_id('account.tax', 'name', taxes_name)
        if supplier_taxes_name not in supplier_taxes:
            supplier_taxes[supplier_taxes_name] = fetch_id('account.tax', 'name', supplier_taxes_name)

        products.append({
            'default_code': default_code,
            'name': product_name,
            'categ_id': categories[category_name],
            'type': type_product,
            'list_price_type': list_price_type,
            'sale_margin': sale_margin,
            'replenishment_base_cost': replenishment_base_cost,
            'replenishment_base_cost_currency_id': currencies[replenishment_base_cost_currency],
            'available_in_pos': available_in_pos,
            'pos_categ_id': pos_categories[pos_categ_name],
            'public_categ_ids': [public_categories[public_categ_name]] if public_categ_name in public_categories else [],
            'taxes_id': [taxes[taxes_name]],
            'supplier_taxes_id': [supplier_taxes[supplier_taxes_name]],
            'image_1920': image_1920,
        })

    # Create products in batch
    odoo.create_products(products)
    print(f"Se han creado {len(products)} productos con éxito.")
