import xmlrpc.client
import csv

class OdooConnector:
    def __init__(self, dbname, username, password, url):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.url = url
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.uid = self.common.authenticate(dbname, username, password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

class CategoryImporter:
    def __init__(self, odoo, csv_file):
        self.odoo = odoo
        self.csv_file = csv_file

    def import_categories(self, model):
        with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            for row in reader:
                name, parent_name = row
                if not name:
                    continue
                parent_id = False
                if parent_name:
                    parent_id = self.find_category_by_name(model, parent_name)
                vals = {'name': name}
                if parent_id:
                    vals['parent_id'] = parent_id
                self.odoo.models.execute_kw(self.odoo.dbname, self.odoo.uid, self.odoo.password, model, "create", [vals])

    def find_category_by_name(self, model, name):
        domain = [('name', '=', name)]
        category = self.odoo.models.execute_kw(self.odoo.dbname, self.odoo.uid, self.odoo.password, model, "search_read", [domain])
        if category:
            return category[0]['id']
        return False

if __name__ == "__main__":
    odoo = OdooConnector('test1', 'admin', 'bgt56yhn*971', 'http://odoo.local:8069')
    importer = CategoryImporter(odoo, '_categorias.csv')
    importer.import_categories('product.category')
    importer.import_categories('pos.category')
    importer.import_categories('product.public.category')
