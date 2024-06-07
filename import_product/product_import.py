import xmlrpc.client
import csv

# Establecer el límite del tamaño de campo CSV
csv.field_size_limit(1000000)

# Permitir caracteres unicode
xmlrpc.client.Transport.use_unicode = True

# Detalles de conexión a Odoo
url = 'http://localhost:8069'
db = 'test1'
username = 'admin'
password = 'bgt56yhn*971'

class OdooAPI:
    def __init__(self, url, db, username, password):
        """
        Inicializa la conexión a la API de Odoo.
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    def import_products_from_csv(self, filename):
        """
        Importa los productos desde un archivo CSV a Odoo.
        """
        try:
            # Abrir el archivo CSV para lectura
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Iterar sobre cada fila en el archivo CSV
                for row in reader:
                    # Obtener los IDs de las categorías, impuestos, etc.
                    category_id = self._get_category_id(row['category'])
                    pos_category_id = self._get_pos_category_id(row['pos_category'])
                    public_category_ids = self._get_public_category_ids(row['public_category'])
                    taxes_ids = self._get_taxes_ids(row['taxes'], 'sale')
                    supplier_taxes_ids = self._get_taxes_ids(row['supplier_taxes'], 'purchase')
                    
                    # Obtener el ID de la moneda
                    currency_id = self._get_currency_id(row['replenishment_base_cost_currency'])

                    # Crear el producto en Odoo
                    product_id = self.models.execute_kw(self.db, self.uid, self.password,
                                                        'product.product', 'create', [{
                                                            'default_code': row['default_code'],
                                                            'name': row['name'],
                                                            'categ_id': category_id,
                                                            'type': row['type'],
                                                            'list_price_type': row['list_price_type'],
                                                            'sale_margin': row['sale_margin'],
                                                            'replenishment_base_cost': row['replenishment_base_cost'],
                                                            'replenishment_base_cost_currency_id': currency_id,
                                                            'available_in_pos': row['available_in_pos'],
                                                            'pos_categ_id': pos_category_id,
                                                            'public_categ_ids': [(6, 0, public_category_ids)],
                                                            'taxes_id': [(6, 0, taxes_ids)],
                                                            'supplier_taxes_id': [(6, 0, supplier_taxes_ids)],
                                                            'image_1920': row['image_1920']
                                                        }])
                    print(f"Producto '{row['name']}' creado con ID {product_id}")

            print("Importación completada correctamente.")
        except Exception as e:
            print("Error durante la importación:", e)

    def _get_category_id(self, category_name):
        # Buscar el ID de la categoría dado su nombre.
        category_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                              'product.category', 'search', [[('name', '=', category_name)]])
        return category_ids[0] if category_ids else False

    def _get_pos_category_id(self, pos_category_name):
        # Buscar el ID de la categoría de POS dado su nombre.
        pos_category_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                                   'pos.category', 'search', [[('name', '=', pos_category_name)]])
        return pos_category_ids[0] if pos_category_ids else False

    def _get_public_category_ids(self, public_category_names):
        # Buscar los IDs de las categorías públicas dado sus nombres.
        public_category_ids = []
        if public_category_names:
            for name in public_category_names.split(','):
                category_id = self.models.execute_kw(self.db, self.uid, self.password,
                                                     'product.public.category', 'search', [[('name', '=', name.strip())]])
                if category_id:
                    public_category_ids.append(category_id[0])
        return public_category_ids

    def _get_taxes_ids(self, taxes_names, tax_type):
        # Buscar los IDs de los impuestos dado sus nombres y tipo (sale o purchase).
        taxes_ids = []
        if taxes_names:
            for name in taxes_names.split(','):
                tax_id = self.models.execute_kw(self.db, self.uid, self.password,
                                                'account.tax', 'search', [[('name', '=', name.strip()), ('type_tax_use', '=', tax_type)]])
                if tax_id:
                    taxes_ids.append(tax_id[0])
        return taxes_ids

    def _get_currency_id(self, currency_code):
        # Buscar el ID de la moneda dado su código.
        currency_ids = self.models.execute_kw(self.db, self.uid, self.password,
                                              'res.currency', 'search', [[('name', '=', currency_code)]])
        return currency_ids[0] if currency_ids else False

# Crear una instancia de la API de Odoo e importar los productos desde el archivo CSV
odoo = OdooAPI(url, db, username, password)
odoo.import_products_from_csv('productos_exportados.csv')
