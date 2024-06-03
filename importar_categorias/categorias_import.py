import xmlrpc.client
import openpyxl

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
    def __init__(self, odoo, excel_file):
        self.odoo = odoo
        self.excel_file = excel_file

    def import_categories(self, model):
        workbook = openpyxl.load_workbook(self.excel_file)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name, parent_name = row
            if not name:
                continue
            parent_id = False
            if parent_name:
                parent_id = self.find_category_by_name(model, parent_name)
            vals = {'name': name}
            if parent_id:
                vals['parent_id'] = parent_id
            self.odoo.models.execute_kw(self.odoo.dbname, self.odoo.uid, self.odoo.password,model, "create", [vals])

    def find_category_by_name(self, model, name):
        domain = [('name', '=', name)]
        category = self.odoo.models.execute_kw(self.odoo.dbname, self.odoo.uid, self.odoo.password,model, "search_read", [domain])
        if category:
            return category[0]['id']
        return False

if __name__ == "__main__":
    odoo = OdooConnector('o16db', 'admin', 'bgt56yhn*971', 'http://localhost:8069')
    importer = CategoryImporter(odoo, '_categorias.xlsx')
    importer.import_categories('product.category')
    importer.import_categories('pos.category')
    importer.import_categories('product.public.category')