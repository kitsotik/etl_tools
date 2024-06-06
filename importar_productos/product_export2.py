import xmlrpc.client
import csv

# Por tema de acentos y eñes
xmlrpc.client.Transport.use_unicode = True 

url = 'http://192.168.192.131:8069'
db = 'test2'
username = 'admin'
password = 'bgt56yhn*971'

class OdooAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    def search_read_products(self):
        fields = [
            'default_code', 'name', 'categ_id', 'type', 'list_price_type',
            'sale_margin', 'replenishment_base_cost', 'replenishment_base_cost_currency_id',
            'available_in_pos', 'pos_categ_id', 'public_categ_ids', 'taxes_id', 
            'supplier_taxes_id', 'image_1920'
        ]
        products = self.models.execute_kw(self.db, self.uid, self.password,
            'product.product', 'search_read', 
            [[], fields])
        return products

    def get_name_by_id(self, model, ids):
        if not ids:
            return []
        result = self.models.execute_kw(self.db, self.uid, self.password,
            model, 'name_get', [ids])
        return [name[1] for name in result] if result else []

odoo = OdooAPI(url, db, username, password)

# Recupera los productos de Odoo
products = odoo.search_read_products()

# Escribe los productos en un archivo CSV
with open('exported_products.csv', mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    # Escribe la cabecera
    writer.writerow([
        'default_code', 'product_name', 'category_name', 'type_product', 
        'list_price_type', 'sale_margin', 'replenishment_base_cost', 
        'replenishment_base_cost_currency', 'available_in_pos', 'pos_categ_name', 
        'public_categ_name', 'taxes_name', 'supplier_taxes_name', 'image_1920'
    ])
    
    for product in products:
        category_name = odoo.get_name_by_id('product.category', [product['categ_id'][0]])[0] if product['categ_id'] else ''
        replenishment_base_cost_currency = odoo.get_name_by_id('res.currency', [product['replenishment_base_cost_currency_id'][0]])[0] if product['replenishment_base_cost_currency_id'] else ''
        pos_categ_name = odoo.get_name_by_id('pos.category', [product['pos_categ_id'][0]])[0] if product['pos_categ_id'] else ''
        public_categ_name = ', '.join(odoo.get_name_by_id('product.public.category', product['public_categ_ids'])) if product['public_categ_ids'] else ''
        taxes_name = ', '.join(odoo.get_name_by_id('account.tax', product['taxes_id'])) if product['taxes_id'] else ''
        supplier_taxes_name = ', '.join(odoo.get_name_by_id('account.tax', product['supplier_taxes_id'])) if product['supplier_taxes_id'] else ''
        
        writer.writerow([
            product['default_code'], product['name'], category_name, product['type'], 
            product['list_price_type'], product['sale_margin'], product['replenishment_base_cost'], 
            replenishment_base_cost_currency, product['available_in_pos'], pos_categ_name, 
            public_categ_name, taxes_name, supplier_taxes_name, product['image_1920']
        ])

print("Los productos han sido exportados con éxito a 'exported_products.csv'.")
