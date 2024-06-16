import xmlrpc.client

# Datos de conexión para la instancia de Odoo de origen
url_origen = 'http://odoo.local:8069'
db_origen = 'test1'
username_origen = 'admin'
password_origen = 'bgt56yhn*971'

# Datos de conexión para la instancia de Odoo de destino
url_destino = 'http://192.168.192.131:8069'
db_destino = 'test1'
username_destino = 'admin'
password_destino = 'bgt56yhn*971'

# Conexión a Odoo de origen
common_origen = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_origen))
uid_origen = common_origen.authenticate(db_origen, username_origen, password_origen, {})
models_origen = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_origen))

# Conexión a Odoo de destino
common_destino = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_destino))
uid_destino = common_destino.authenticate(db_destino, username_destino, password_destino, {})
models_destino = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_destino))

# Función para obtener las categorías de una tabla en el origen
def obtener_categorias(models, db, uid, password, model):
    return models.execute_kw(db, uid, password, model, 'search_read', [[], ['name', 'parent_id']])

# Función para buscar o crear una categoría en el destino
def buscar_o_crear_categoria(models, db, uid, password, model, categoria, categorias_origen, categorias_destino):
    # Buscar categoría por nombre
    categoria_destino = models.execute_kw(db, uid, password, model, 'search', [[['name', '=', categoria['name']]]])
    if categoria_destino:
        return categoria_destino[0]
    else:
        # Si no existe, crearla
        parent_id = False
        if categoria['parent_id']:
            parent_name = next((c['name'] for c in categorias_origen if c['id'] == categoria['parent_id'][0]), None)
            if parent_name:
                parent_dest_id = models.execute_kw(db, uid, password, model, 'search', [[['name', '=', parent_name]]])
                if parent_dest_id:
                    parent_id = parent_dest_id[0]
        return models.execute_kw(db, uid, password, model, 'create', [{
            'name': categoria['name'],
            'parent_id': parent_id
        }])

# Función para ordenar las categorías en base a su jerarquía
def ordenar_categorias(categorias):
    categorias_dict = {categoria['id']: categoria for categoria in categorias}
    categorias_ordenadas = []
    
    def add_categoria(categoria):
        if 'added' in categoria:
            return
        if categoria['parent_id']:
            parent_id = categoria['parent_id'][0]
            if parent_id in categorias_dict:
                add_categoria(categorias_dict[parent_id])
        categorias_ordenadas.append(categoria)
        categoria['added'] = True
    
    for categoria in categorias:
        add_categoria(categoria)
    
    return categorias_ordenadas

# Sincronización de categorías entre las tablas
modelos = ['product.category', 'pos.category', 'product.public.category']

for modelo in modelos:
    categorias_origen = obtener_categorias(models_origen, db_origen, uid_origen, password_origen, modelo)
    categorias_origen = ordenar_categorias(categorias_origen)
    categorias_destino = obtener_categorias(models_destino, db_destino, uid_destino, password_destino, modelo)
    
    for categoria in categorias_origen:
        categoria_id = buscar_o_crear_categoria(models_destino, db_destino, uid_destino, password_destino, modelo, categoria, categorias_origen, categorias_destino)
        
        # Verificar y actualizar el parent_id si es necesario
        if categoria['parent_id']:
            parent_name = next((c['name'] for c in categorias_origen if c['id'] == categoria['parent_id'][0]), None)
            if parent_name:
                parent_dest_id = models_destino.execute_kw(db_destino, uid_destino, password_destino, modelo, 'search', [[['name', '=', parent_name]]])
                if parent_dest_id:
                    # Actualizar el parent_id en la categoría de destino
                    models_destino.execute_kw(db_destino, uid_destino, password_destino, modelo, 'write', [[categoria_id], {
                        'parent_id': parent_dest_id[0]
                    }])

print("Sincronización completada.")
