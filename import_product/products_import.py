import xmlrpc.client
import csv
csv.field_size_limit(1000000)

#por tema acentos y eñes
xmlrpc.client.Transport.use_unicode = True 

url = 'http://odoo.local:8069'
db = 'o16db'
username = 'admin'
password = 'bgt56yhn*971'

list_price_type_translate = {
    'By Margin': ('by_margin'),
    'Fixed value': ('manual'),
    # Agregar otras categorías según sea necesario
}
type_product_translate = {
    'Almacenable': ('product'),
    'Servicio': ('service'),
    'consu': ('consu'),
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

    def create_product(self, default_code,product_name, category_id, type_product, list_price_type,sale_margin,replenishment_base_cost,replenishment_base_cost_currency_id,available_in_pos,pos_categ_id,public_categ_ids,taxes_id,supplier_taxes_id,image_1920):
        values = {
            'default_code': default_code,
            'name': product_name,
            'categ_id': category_id,
            'type': type_product,
            'list_price_type' : list_price_type,
            'sale_margin' : sale_margin,
            'replenishment_base_cost' : replenishment_base_cost,
            'replenishment_base_cost_currency_id' : replenishment_base_cost_currency_id,
            'available_in_pos': available_in_pos,
            'pos_categ_id' : pos_categ_id,
            'public_categ_ids': [public_categ_ids], 
            'taxes_id': [taxes_id],
            'supplier_taxes_id': [supplier_taxes_id],
            'image_1920': image_1920,
        }
        product_id = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'create', [values])
        return product_id

odoo = OdooAPI(url, db, username, password)
contador=1
with open('exported_products.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
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

        #Busca el id de la categoria basadoo en el nombre que trae del archivo
        category_id = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'product.category', 'search', [[('complete_name','=',category_name)]])[0]
        #Busca el id de la moneda del producto
        replenishment_base_cost_currency_id = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'res.currency', 'search', [[('name','=',replenishment_base_cost_currency)]])[0]
        #Busca el id de la categoria del pos basadoo en el nombre que trae del archivo
        pos_categ_id = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'pos.category', 'search', [[('name','=',pos_categ_name)]])[0]
        #Busca el id de la categoria del website basado en el nombre que trae del archivo
        #if len(public_categ_name) != 0:
        public_categ_ids = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'product.public.category', 'search', [[('name','=',public_categ_name)]])[0]
        taxes_id = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'account.tax', 'search', [[('name','=',taxes_name)]])[0]
        supplier_taxes_id = odoo.models.execute_kw(db, odoo.uid, odoo.password, 'account.tax', 'search', [[('name','=',supplier_taxes_name)]])[0]

        #crea el producto
        odoo.create_product(default_code, product_name, category_id, type_product,list_price_type, sale_margin,replenishment_base_cost, replenishment_base_cost_currency_id,available_in_pos,pos_categ_id,public_categ_ids,taxes_id,supplier_taxes_id,image_1920)
        print(f"El producto {product_name} se ha creado con éxito.")