import xmlrpc.client
import csv
import time

# Establecer el límite del tamaño de campo CSV
csv.field_size_limit(1000000)

# Permitir caracteres unicode
xmlrpc.client.Transport.use_unicode = True

# Detalles de conexión a Odoo
url = 'http://localhost:8069'
db = 'o16dbs'
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
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url), allow_none=True, use_datetime=True)
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url), allow_none=True, use_datetime=True)

    def export_products_to_csv(self, filename):
        """
        Exporta los productos de Odoo a un archivo CSV.
        """
        try:
            # Recupera los productos desde Odoo en lotes
            batch_size = 100  # Tamaño del lote
            offset = 0
            products = []

            while True:
                batch = self._get_products_batch(batch_size, offset)
                if not batch:
                    break
                products.extend(batch)
                offset += batch_size
                print(f"Lote {offset // batch_size} recuperado, total de productos hasta ahora: {len(products)}")

            total_products = len(products)
            print(f"Total de productos a exportar: {total_products}")

            # Obtener todos los IDs únicos para las consultas
            categ_ids = list(set(p['categ_id'][0] for p in products if isinstance(p['categ_id'], (list, tuple)) and p['categ_id']))
            pos_categ_ids = list(set(p['pos_categ_id'][0] for p in products if isinstance(p['pos_categ_id'], (list, tuple)) and p['pos_categ_id']))
            public_categ_ids = list(set(id for p in products for id in p['public_categ_ids'] if isinstance(p['public_categ_ids'], list)))
            taxes_ids = list(set(id for p in products for id in p['taxes_id'] if isinstance(p['taxes_id'], list)))
            supplier_taxes_ids = list(set(id for p in products for id in p['supplier_taxes_id'] if isinstance(p['supplier_taxes_id'], list)))

            # Consultar todos los datos necesarios de una sola vez
            categories = self._read_records('product.category', categ_ids, ['name'])
            pos_categories = self._read_records('pos.category', pos_categ_ids, ['name'])
            public_categories = self._read_records('product.public.category', public_categ_ids, ['name'])
            taxes = self._read_records('account.tax', taxes_ids, ['name'])
            supplier_taxes = self._read_records('account.tax', supplier_taxes_ids, ['name'])

            # Crear diccionarios para acceso rápido
            categ_dict = {rec['id']: rec['name'] for rec in categories}
            pos_categ_dict = {rec['id']: rec['name'] for rec in pos_categories}
            public_categ_dict = {rec['id']: rec['name'] for rec in public_categories}
            taxes_dict = {rec['id']: rec['name'] for rec in taxes}
            supplier_taxes_dict = {rec['id']: rec['name'] for rec in supplier_taxes}

            # Abre el archivo CSV para escritura
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Define los nombres de las columnas del CSV
                fieldnames = ['default_code', 'name', 'category', 'type', 'list_price_type',
                              'sale_margin', 'replenishment_base_cost', 'replenishment_base_cost_currency',
                              'available_in_pos', 'pos_category', 'public_category', 'taxes', 'supplier_taxes',
                              'image_1920']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()

                # Escribe cada producto en el archivo CSV y muestra el progreso
                for index, product in enumerate(products, start=1):
                    categ_id = product.get('categ_id', (None,))
                    pos_categ_id = product.get('pos_categ_id', (None,))
                    public_categ_ids = product.get('public_categ_ids', [])
                    taxes_ids = product.get('taxes_id', [])
                    supplier_taxes_ids = product.get('supplier_taxes_id', [])

                    category_name = categ_dict.get(categ_id[0], '') if isinstance(categ_id, (list, tuple)) and categ_id else ''
                    pos_categ_name = pos_categ_dict.get(pos_categ_id[0], '') if isinstance(pos_categ_id, (list, tuple)) and pos_categ_id else ''
                    public_categ_name = ', '.join([public_categ_dict.get(id, '') for id in public_categ_ids if isinstance(public_categ_ids, list)])
                    taxes_name = ', '.join([taxes_dict.get(id, '') for id in taxes_ids if isinstance(taxes_ids, list)])
                    supplier_taxes_name = ', '.join([supplier_taxes_dict.get(id, '') for id in supplier_taxes_ids if isinstance(supplier_taxes_ids, list)])

                    # Escribe los datos en el CSV
                    writer.writerow({'default_code': product.get('default_code', ''),
                                     'name': product.get('name', ''),
                                     'category': category_name,
                                     'type': product.get('type', ''),
                                     'list_price_type': product.get('list_price_type', ''),
                                     'sale_margin': product.get('sale_margin', ''),
                                     'replenishment_base_cost': product.get('replenishment_base_cost', ''),
                                     'replenishment_base_cost_currency': product.get('replenishment_base_cost_currency_id', ('', ''))[1] if isinstance(product.get('replenishment_base_cost_currency_id', (None,)), (list, tuple)) else '',
                                     'available_in_pos': product.get('available_in_pos', ''),
                                     'pos_category': pos_categ_name,
                                     'public_category': public_categ_name,
                                     'taxes': taxes_name,
                                     'supplier_taxes': supplier_taxes_name,
                                     'image_1920': product.get('image_1920', '')})

                    # Muestra el progreso
                    print(f"Exportando producto {index}/{total_products}: {product.get('name', '')}")

            print("Exportación completada correctamente.")
        except Exception as e:
            print("Error durante la exportación:", e)

    def _get_products_batch(self, batch_size, offset):
        """
        Recupera un lote de productos desde Odoo.
        """
        attempts = 3
        for attempt in range(attempts):
            try:
                return self.models.execute_kw(self.db, self.uid, self.password,
                                              'product.product', 'search_read',
                                              [[]],
                                              {'fields': ['default_code', 'name', 'categ_id',
                                                          'type', 'list_price_type',
                                                          'sale_margin', 'replenishment_base_cost',
                                                          'replenishment_base_cost_currency_id',
                                                          'available_in_pos', 'pos_categ_id',
                                                          'public_categ_ids', 'taxes_id',
                                                          'supplier_taxes_id', 'image_1920'],
                                               'limit': batch_size, 'offset': offset})
            except Exception as e:
                print(f"Error al recuperar lote, intento {attempt + 1} de {attempts}: {e}")
                time.sleep(5)
        return []

    def _read_records(self, model, ids, fields):
        """
        Lee registros de Odoo en lotes para evitar problemas de memoria.
        """
        records = []
        batch_size = 100
        attempts = 3
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            for attempt in range(attempts):
                try:
                    records.extend(self.models.execute_kw(self.db, self.uid, self.password,
                                                          model, 'read', [batch_ids], {'fields': fields}))
                    break
                except Exception as e:
                    print(f"Error al leer registros del modelo {model}, intento {attempt + 1} de {attempts}: {e}")
                    time.sleep(5)
        return records

# Crear una instancia de la API de Odoo y exportar los productos a un archivo CSV
odoo = OdooAPI(url, db, username, password)
odoo.export_products_to_csv('productos_exportados.csv')
