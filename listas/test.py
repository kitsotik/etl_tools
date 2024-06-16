import pandas as pd

# Leer el archivo Excel con los encabezados en la segunda fila
file_path = 'RND.xlsx'
excel_data = pd.read_excel(file_path, header=1)

# Mostrar los nombres de las columnas para verificar
print(excel_data.columns)
