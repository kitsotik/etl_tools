import xmlrpc.client

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

    def search_read_supplier_taxes(self, limit=1):
        fields = ['supplier_taxes_id']
        domain = [('active', '=', True)]  # Asegura obtener solo productos activos
        products = self.models.execute_kw(self.db, self.uid, self.password,
            'product.product', 'search_read', 
            [domain, fields], {'limit': limit})
        return products

odoo = OdooAPI(url, db, username, password)

# Recupera un producto de Odoo y muestra solo el campo supplier_taxes_id
products = odoo.search_read_supplier_taxes(limit=1)

# Muestra los detalles del supplier_taxes_id recuperado
if products:
    product = products[0]
    supplier_taxes_ids = product.get('supplier_taxes_id', [])
    print(f"supplier_taxes_id (IDs): {supplier_taxes_ids}")
else:
    print("No se recuperaron productos.")
