    import xmlrpc.client
    import csv

    # Establecer el límite del tamaño de campo CSV
    csv.field_size_limit(1000000)

    # Permitir caracteres unicode
    xmlrpc.client.Transport.use_unicode = True

    # Detalles de conexión a Odoo
    url = 'http://192.168.192.131:8069'
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

        def export_products_to_csv(self, filename):
            """
            Exporta los productos de Odoo a un archivo CSV.
            """
            try:
                # Recupera los productos desde Odoo
                products = self.models.execute_kw(self.db, self.uid, self.password,
                                                'product.product', 'search_read',
                                                [[]],
                                                {'fields': ['default_code', 'name', 'categ_id',
                                                            'type', 'list_price_type',
                                                            'sale_margin', 'replenishment_base_cost',
                                                            'replenishment_base_cost_currency_id',
                                                            'available_in_pos', 'pos_categ_id',
                                                            'public_categ_ids', 'taxes_id',
                                                            'supplier_taxes_id', 'image_1920']
                                                })

                total_products = len(products)
                print(f"Total de productos a exportar: {total_products}")

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
                        category_name = self._get_category_name(product.get('categ_id', ()))
                        pos_categ_name = self._get_pos_category_name(product.get('pos_categ_id', ()))
                        public_categ_name = self._get_public_category_name(product.get('public_categ_ids', []))
                        taxes_name = self._get_taxes_name(product.get('taxes_id', []))
                        supplier_taxes_name = self._get_taxes_name(product.get('supplier_taxes_id', []))

                        # Escribe los datos en el CSV
                        writer.writerow({'default_code': product.get('default_code', ''),
                                        'name': product.get('name', ''),
                                        'category': category_name,
                                        'type': product.get('type', ''),
                                        'list_price_type': product.get('list_price_type', ''),
                                        'sale_margin': product.get('sale_margin', ''),
                                        'replenishment_base_cost': product.get('replenishment_base_cost', ''),
                                        'replenishment_base_cost_currency': product.get('replenishment_base_cost_currency_id', ('', ''))[1],
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

        def _get_category_name(self, categ_id):
            # Devuelve el nombre de la categoría dado su ID.
            if categ_id:
                category = self.models.execute_kw(self.db, self.uid, self.password,
                                            'product.category', 'read',
                                            [categ_id[0]], {'fields': ['name']})
                return category[0]['name'] if category else ''
            return ''


        def _get_pos_category_name(self, pos_categ_id):
            #  Devuelve el nombre de la categoría de POS dado su ID.
            if pos_categ_id:
                pos_category = self.models.execute_kw(self.db, self.uid, self.password,
                                                    'pos.category', 'read',
                                                    [pos_categ_id[0]], {'fields': ['name']})
                return pos_category[0]['name'] if pos_category else ''
            return ''

        def _get_public_category_name(self, public_categ_ids):
            # Devuelve los nombres de las categorías públicas dado sus IDs.
            if public_categ_ids:
                public_categories = self.models.execute_kw(self.db, self.uid, self.password,
                                                        'product.public.category', 'read',
                                                        public_categ_ids, {'fields': ['name']})
                return ', '.join([category['name'] for category in public_categories])
            return ''

        def _get_taxes_name(self, taxes_ids):
            # Devuelve los nombres de los impuestos dado sus IDs.
            if taxes_ids:
                taxes = self.models.execute_kw(self.db, self.uid, self.password,
                                            'account.tax', 'read',
                                            taxes_ids, {'fields': ['name']})
                return ', '.join([tax['name'] for tax in taxes])
            return ''

    # Crear una instancia de la API de Odoo y exportar los productos a un archivo CSV
    odoo = OdooAPI(url, db, username, password)
    odoo.export_products_to_csv('productos_exportados.csv')
