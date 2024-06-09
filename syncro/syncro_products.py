import xmlrpc.client
import csv

# Establecer el límite del tamaño de campo CSV
csv.field_size_limit(1000000)

# Permitir caracteres unicode
xmlrpc.client.Transport.use_unicode = True

# Detalles de conexión a las instancias de Odoo
url1 = 'http://odoo.local:8069'
db1 = 'test1'
username1 = 'admin'
password1 = 'bgt56yhn*971'

url2 = 'http://192.168.192.131:8069'
db2 = 'test1'
username2 = 'admin'
password2 = 'bgt56yhn*971'

class OdooAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    def get_products(self):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      'product.product', 'search_read',
                                      [[]],
                                      {'fields': ['default_code', 'name', 'categ_id',
                                                  'type', 'list_price_type',
                                                  'sale_margin', 'replenishment_base_cost',
                                                  'replenishment_base_cost_currency_id',
                                                  'available_in_pos', 'pos_categ_id',
                                                  'public_categ_ids', 'taxes_id',
                                                  'supplier_taxes_id', 'image_1920']})

    def get_category_id(self, category_name):
        category_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                              'product.category', 'search', [[('name', '=', category_name)]])
        return category_ids[0] if category_ids else False

    def create_category(self, category_name):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      'product.category', 'create', [{'name': category_name}])

    def sync_category(self, category_name):
        category_id = self.get_category_id(category_name)
        if not category_id:
            category_id = self.create_category(category_name)
        return category_id

    def create_product(self, product_data):
        # Eliminar el campo 'default_code' antes de crear el producto
        product_data.pop('default_code', None)
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      'product.product', 'create', [product_data])

    def update_product(self, product_id, product_data):
        # Eliminar el campo 'default_code' antes de actualizar el producto
        product_data.pop('default_code', None)
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      'product.product', 'write', [[product_id], product_data])

    def search_product_by_default_code(self, default_code):
        product_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                             'product.product', 'search', [[('default_code', '=', default_code)]])
        return product_ids[0] if product_ids else False

def sync_products(source_odoo, target_odoo):
    source_products = source_odoo.get_products()

    for product in source_products:
        # Obtener el nombre de la categoría y sincronizarla en la instancia de destino
        category_name = source_odoo.models.execute_kw(source_odoo.db, source_odoo.uid, source_odoo.password,
                                                      'product.category', 'read',
                                                      [product['categ_id'][0]], {'fields': ['name']})[0]['name']
        category_id = target_odoo.sync_category(category_name)

        # Preparar los datos del producto para la instancia de destino
        product_data = {
            'default_code': product['default_code'],
            'name': product['name'],
            'categ_id': category_id,
            'type': product['type'],
            'list_price_type': product['list_price_type'],
            'sale_margin': product['sale_margin'],
            'replenishment_base_cost': product['replenishment_base_cost'],
            'replenishment_base_cost_currency_id': product['replenishment_base_cost_currency_id'][0],
            'available_in_pos': product['available_in_pos'],
            'pos_categ_id': product['pos_categ_id'][0] if product['pos_categ_id'] else False,
            'public_categ_ids': [(6, 0, product['public_categ_ids'])],
            'taxes_id': [(6, 0, product['taxes_id'])],
            'supplier_taxes_id': [(6, 0, product['supplier_taxes_id'])]
        }

        if product['image_1920'] and product['image_1920'].lower() != 'false':
            product_data['image_1920'] = product['image_1920']

        # Buscar el producto en la instancia de destino por default_code
        target_product_id = target_odoo.search_product_by_default_code(product['default_code'])
        if target_product_id:
            # Actualizar el producto si ya existe
            try:
                target_odoo.update_product(target_product_id, product_data)
                print(f"Producto '{product['name']}' actualizado en la instancia de destino con ID {target_product_id}")
            except Exception as e:
                print(f"Error actualizando el producto '{product['name']}' en la instancia de destino: {e}")
        else:
            # Crear el producto si no existe
            try:
                target_product_id = target_odoo.create_product(product_data)
                print(f"Producto '{product['name']}' creado en la instancia de destino con ID {target_product_id}")
            except Exception as e:
                print(f"Error creando el producto '{product['name']}' en la instancia de destino: {e}")

# Crear instancias de la API de Odoo para las dos instancias
odoo1 = OdooAPI(url1, db1, username1, password1)
odoo2 = OdooAPI(url2, db2, username2, password2)

# Sincronizar productos de odoo1 a odoo2
sync_products(odoo1, odoo2)
