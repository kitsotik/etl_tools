import pandas as pd

# Leer el archivo Excel sin encabezado
file_path = 'RND.xlsx'
excel_data = pd.read_excel(file_path, header=None)

# Asignar manualmente los nombres de las columnas
excel_data.columns = ['ignore', 'CODIGO', 'IMAGEN', 'DESCRIPCION', 'UNIT', 'CANT.']

# Mostrar las primeras filas del DataFrame para verificar
print(excel_data.head())

# Crear una lista para almacenar los datos filtrados
filtered_data = []

# Iterar a través de las filas del DataFrame
for index, row in excel_data.iterrows():
    # Imprimir valores actuales para depuración
    print(f"Row {index}: CODIGO={row['CODIGO']}, IMAGEN={row['IMAGEN']}, DESCRIPCION={row['DESCRIPCION']}, CANT.={row['CANT.']}")
    
    if pd.notnull(row['IMAGEN']) and pd.notnull(row['DESCRIPCION']) and pd.notnull(row['CANT.']):
        product = {
            'name': row['DESCRIPCION'],
            'costo': row['CANT.'],
            'imagen': row['IMAGEN'],
            'codigo': row['CODIGO']
        }
        filtered_data.append(product)

# Verificar si se encontraron productos
print(f"Productos encontrados: {len(filtered_data)}")
print(f"Productos filtrados: {filtered_data}")

# Convertir la lista a un DataFrame de pandas
filtered_df = pd.DataFrame(filtered_data)

# Verificar el DataFrame
print(filtered_df.head())

# Guardar el DataFrame en un archivo CSV
csv_output_path = 'productos_filtrados.csv'
filtered_df.to_csv(csv_output_path, index=False)

print(f'Los datos han sido guardados en {csv_output_path}')

