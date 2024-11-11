import os
import pandas as pd

def import_and_clean_data(data_folder='./dataset'):
    """
    Importa y limpia los archivos CSV en la carpeta especificada.
    
    Args:
        data_folder (str): Ruta a la carpeta que contiene los archivos CSV.
        
    Returns:
        pd.DataFrame: DataFrame limpio con datos de productos.
    """
    dataframes = []
    
    # Tasa de conversión de Rupias a Dólares (1 INR = 0.012 USD, por ejemplo)
    inr_to_usd = 0.012

    for file in os.listdir(data_folder):
        if file.endswith('.csv'):
            file_path = os.path.join(data_folder, file)
            df = pd.read_csv(file_path)

            if df.empty:
                print(f"El archivo {file} está vacío y será ignorado.")
                continue

            dataframes.append(df)

    if not dataframes:
        print("No hay archivos válidos para procesar.")
        return None

    df = pd.concat(dataframes, ignore_index=True)

    # Limpieza de datos
    df['ratings'] = pd.to_numeric(df['ratings'], errors='coerce')
    df = df.dropna(subset=['ratings'])

    df['no_of_ratings'] = pd.to_numeric(df['no_of_ratings'].str.replace(',', '', regex=True), errors='coerce')
    df['discount_price'] = df['discount_price'].str.replace('â‚¹', '').str.replace('₹', '').str.replace(',', '')
    df['actual_price'] = df['actual_price'].str.replace('â‚¹', '').str.replace('₹', '').str.replace(',', '')

    df['discount_price'] = pd.to_numeric(df['discount_price'], errors='coerce')
    df['actual_price'] = pd.to_numeric(df['actual_price'], errors='coerce')

    # Convertir los precios de Rupias a Dólares
    df['discount_price'] = df['discount_price'] * inr_to_usd
    df['actual_price'] = df['actual_price'] * inr_to_usd

    # Filtrar valores válidos para precios y cantidad de reseñas
    max_discount_price = 300
    max_actual_price = 1000
    max_no_of_ratings = 1500

    df_clean = df[ 
        (df['discount_price'] <= max_discount_price) & 
        (df['actual_price'] <= max_actual_price) & 
        (df['no_of_ratings'] <= max_no_of_ratings)
    ]
    
    # Eliminar filas con valores NaN en cualquier columna importante
    df_clean = df_clean.dropna(subset=['ratings', 'no_of_ratings', 'discount_price', 'actual_price'])

    return df_clean
