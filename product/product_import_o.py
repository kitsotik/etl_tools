import xmlrpc.client
import csv
from collections import defaultdict

# Establecer el límite del tamaño de campo CSV
csv.field_size_limit(1000000)

# Permitir caracteres unicode
xmlrpc.client.Transport.use_unicode = True

# Detalles de conexión a Odoo
url = 'http://odoo.local:8069'
db = 'test1'
username = 'admin'
password = 'bgt56yhn*971'

class AllowNoneTransport(xmlrpc.client.Transport):
    def __init__(self, use_datetime=0):
        super().__init__(use_datetime=use_datetime)
        self._allow_none = True

class OdooAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url), transport=AllowNoneTransport())
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url), transport=AllowNoneTransport())
        self.cache = defaultdict(dict)  # Cache para almacenar los resultados de búsqueda

    def import_products_from_csv(self, filename):
        try:
            print("Iniciando la importación...")
            
            # Cachear todas las categorías, impuestos y monedas
            self._cache_all_categories()
            self._cache_all_taxes()
            self._cache_all_currencies()
            
            products_to_create = []

            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    category_id = self.cache['category'].get(row['category'])
                    pos_category_id = self.cache['pos_category'].get(row['pos_category'])
                    public_category_ids = self._get_ids_from_cache('public_category', row['public_category'])
                    taxes_ids = self._get_ids_from_cache('tax', row['taxes'], 'sale')
                    supplier_taxes_ids = self._get_ids_from_cache('tax', row['supplier_taxes'], 'purchase')
                    currency_id = self.cache['currency'].get(row['replenishment_base_cost_currency'])

                    product_data = {
                        'default_code': row['default_code'],
                        'name': row['name'],
                        'categ_id': category_id or False,
                        'type': row['type'],
                        'list_price_type': row['list_price_type'],
                        'sale_margin': row['sale_margin'],
                        'replenishment_base_cost': row['replenishment_base_cost'],
                        'replenishment_base_cost_currency_id': currency_id or False,
                        'available_in_pos': row['available_in_pos'],
                        'pos_categ_id': pos_category_id or False,
                        'public_categ_ids': [(6, 0, public_category_ids)] if public_category_ids else False,
                        'taxes_id': [(6, 0, taxes_ids)] if taxes_ids else False,
                        'supplier_taxes_id': [(6, 0, supplier_taxes_ids)] if supplier_taxes_ids else False
                    }

                    if row['image_1920'] and row['image_1920'].lower() != 'false':
                        product_data['image_1920'] = row['image_1920']

                    products_to_create.append(product_data)
                    print(f"Producto preparado: {row['name']}")

            if products_to_create:
                product_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                                     'product.product', 'create', [products_to_create])
                for product_id, product in zip(product_ids, products_to_create):
                    print(f"Producto '{product['name']}' creado con ID {product_id}")

            print("Importación completada correctamente.")
        except Exception as e:
            print("Error durante la importación:", e)

    def _cache_all_categories(self):
        print("Caché de categorías de productos...")
        categories = self.models.execute_kw(self.db, self.uid, self.password,
                                            'product.category', 'search_read', [[], ['name']])
        for category in categories:
            self.cache['category'][category['name']] = category['id']

        pos_categories = self.models.execute_kw(self.db, self.uid, self.password,
                                                'pos.category', 'search_read', [[], ['name']])
        for category in pos_categories:
            self.cache['pos_category'][category['name']] = category['id']

        public_categories = self.models.execute_kw(self.db, self.uid, self.password,
                                                   'product.public.category', 'search_read', [[], ['name']])
        for category in public_categories:
            self.cache['public_category'][category['name']] = category['id']

        print("Caché de categorías completada.")

    def _cache_all_taxes(self):
        print("Caché de impuestos...")
        taxes = self.models.execute_kw(self.db, self.uid, self.password,
                                       'account.tax', 'search_read', [[], ['name', 'type_tax_use']])
        for tax in taxes:
            self.cache['tax'][(tax['name'], tax['type_tax_use'])] = tax['id']
        print("Caché de impuestos completada.")

    def _cache_all_currencies(self):
        print("Caché de monedas...")
        currencies = self.models.execute_kw(self.db, self.uid, self.password,
                                            'res.currency', 'search_read', [[], ['name']])
        for currency in currencies:
            self.cache['currency'][currency['name']] = currency['id']
        print("Caché de monedas completada.")

    def _get_ids_from_cache(self, cache_name, names, tax_type=None):
        ids = []
        if names:
            for name in names.split(','):
                key = (name.strip(), tax_type) if tax_type else name.strip()
                id_ = self.cache[cache_name].get(key)
                if id_:
                    ids.append(id_)
        return ids

# Crear una instancia de la API de Odoo e importar los productos desde el archivo CSV
odoo = OdooAPI(url, db, username, password)
odoo.import_products_from_csv('productos_exportados.csv')
