import requests
import pandas as pd
import datetime
import time

def fetch_insights(access_token, user_id, date_str):
    """
    Obtiene métricas de insights de Instagram para un usuario en una fecha específica.

    Parámetros:
    - access_token: Token de acceso a la API de Meta.
    - user_id: ID de la cuenta de Instagram.
    - date_str: Fecha en formato 'dd/mm/yyyy'.

    Retorna:
    - JSON con los datos obtenidos de la API.
    """
    # Convertir la fecha a timestamp con hora 00:00:00 (inicio del día)
    since_timestamp = int(time.mktime(datetime.datetime.strptime(date_str, '%d/%m/%Y').replace(hour=0, minute=0, second=0).timetuple()))

    # Convertir la fecha a timestamp con hora 23:59:59 (final del día)
    until_timestamp = int(time.mktime(datetime.datetime.strptime(date_str, '%d/%m/%Y').replace(hour=23, minute=59, second=59).timetuple()))

    url = f"https://graph.facebook.com/v22.0/{user_id}/insights"

    params = {
        "metric": "reach,total_interactions,accounts_engaged,likes,comments,saves,shares,replies,profile_links_taps",
        "period": "day",
        "metric_type": "total_value",
        "access_token": access_token,
        "since": since_timestamp,  # Timestamp con hora 00:00:00
        "until": until_timestamp    # Timestamp con hora 23:59:59
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error en la solicitud para {date_str}: {response.json()}")
        return None

def fetch_follower_count(access_token, user_id, date_str):
    """
    Obtiene el conteo de seguidores para una fecha específica.
    
    Parámetros:
    - access_token: Token de acceso a la API de Meta.
    - user_id: ID de la cuenta de Instagram.
    - date_str: Fecha en formato 'dd/mm/yyyy'.
    
    Retorna:
    - Número de seguidores o None si hay un error.
    """
    # Convertir la fecha a timestamp con hora 00:00:00 (inicio del día)
    since_timestamp = int(time.mktime(datetime.datetime.strptime(date_str, '%d/%m/%Y').replace(hour=0, minute=0, second=0).timetuple()))
    
    # Convertir la fecha a timestamp con hora 23:59:59 (final del día)
    until_timestamp = int(time.mktime(datetime.datetime.strptime(date_str, '%d/%m/%Y').replace(hour=23, minute=59, second=59).timetuple()))
    
    url = f"https://graph.facebook.com/v22.0/{user_id}/insights"
    
    params = {
        "metric": "follower_count",
        "period": "day",
        "access_token": access_token,
        "since": since_timestamp,
        "until": until_timestamp
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0 and 'values' in data['data'][0] and len(data['data'][0]['values']) > 0:
                return data['data'][0]['values'][0]['value']
            else:
                print(f"No se encontraron datos de seguidores para {date_str}")
                return None
        else:
            print(f"Error al obtener el conteo de seguidores: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error al obtener el conteo de seguidores: {str(e)}")
        return None

def process_data(data, date_str, follower_count=None):
    """
    Procesa los datos obtenidos de la API y los convierte en un DataFrame.
    
    Parámetros:
    - data: Datos en formato JSON obtenidos de la API.
    - date_str: Fecha en formato 'dd/mm/yyyy'.
    - follower_count: Conteo de seguidores (opcional).
    
    Retorna:
    - DataFrame con las métricas estructuradas.
    """
    expected_metrics = [
        "reach", "total_interactions", "accounts_engaged", "likes", "comments",
        "saves", "shares", "replies", "profile_links_taps"
    ]
    
    # Diccionario con valores predeterminados en 0
    metrics = {metric: 0 for metric in expected_metrics}
    
    # Añadir follower_count si está disponible
    if follower_count is not None:
        metrics["follower_count"] = follower_count
    else:
        metrics["follower_count"] = 0
    
    # Extraer valores de la API
    for metric in data.get('data', []):
        metric_name = metric['name']
        if metric_name in metrics and 'total_value' in metric and 'value' in metric['total_value']:
            metrics[metric_name] = metric['total_value']['value']
    
    # Crear DataFrame con la fecha proporcionada
    df = pd.DataFrame([metrics])
    
    # Usar la fecha proporcionada en date_str
    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')
    df['Date'] = date_str
    df['Month'] = date_obj.strftime('%B')
    df['Day of the Week'] = date_obj.strftime('%A')
    
    # Rename columns to match the desired format
    column_mapping = {
        'reach': 'Reach',
        'total_interactions': 'Total_interactions',
        'accounts_engaged': 'Accounts_engaged',
        'likes': 'Likes',
        'comments': 'Comments',
        'saves': 'Saves',
        'shares': 'Shares',
        'replies': 'Replies',
        'follower_count': 'Follower_count',
        'profile_links_taps': 'Profile_links_taps'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Reorder columns
    columns_order = ['Month', 'Date', 'Day of the Week', 'Reach', 'Total_interactions', 
                     'Accounts_engaged', 'Likes', 'Comments', 'Saves', 'Shares', 
                     'Replies', 'Follower_count', 'Profile_links_taps']
    
    df = df[columns_order]
    return df

def update_data(existing_df, new_data_df):
    """
    Actualiza un DataFrame existente con nuevos datos, evitando duplicados.

    Parámetros:
    - existing_df: DataFrame existente con datos previos.
    - new_data_df: DataFrame con nuevos datos a agregar.

    Retorna:
    - DataFrame actualizado con los nuevos datos agregados.
    """
    if existing_df is None or existing_df.empty:
        return new_data_df  # Si no hay datos previos, solo retornamos los nuevos datos

    # Unir los datos, eliminando duplicados según la columna 'Date'
    updated_df = pd.concat([existing_df, new_data_df]).drop_duplicates(subset=['Date'], keep='last').reset_index(drop=True)
    
    return updated_df

def main():
    """
    Función principal para ejecutar la obtención y actualización de datos de forma iterativa.
    """
    access_token = "EABCSxik8s3MBOx966Vgv2l8jPwPclfanFeEOZBtnOX2AQqGlm5CPzy9Ry2UO75qmHW5OMU7a4gY6LAgWhoDUR7YsOr4Lx9JYZAJcDRRdA4uSmXvBoQyTwqnNnbAuGSMOIYPlELR4ACzZCzx0pDLKM71MN8gomZAYoCskQXziy3SZCz76NkcJk1wRWX2XTNfuISPmsHlgkTkCr6Nj6WaTpVGZBAHwbvOjGuDYgjonCT"
    user_id = "17841409297279102"
    
    # Número de días hacia atrás a consultar
    days_back = 30

    # Cargar datos previos si existen
    try:
        existing_df = pd.read_csv("lordconejo_dataupdate.csv")
    except FileNotFoundError:
        existing_df = pd.DataFrame()

    # Iterar sobre los últimos días
    for i in range(days_back):
        # Calcular la fecha a consultar
        date_to_fetch = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%d/%m/%Y')
        
        print(f"Consultando datos para: {date_to_fetch}")

        # Obtener datos de la API
        data = fetch_insights(access_token, user_id, date_to_fetch)

        if data:
            # Obtener el conteo de seguidores por separado
            follower_count = fetch_follower_count(access_token, user_id, date_to_fetch)
            
            # Procesar los datos con el conteo de seguidores
            new_data_df = process_data(data, date_to_fetch, follower_count)

            # Actualizar el DataFrame existente
            existing_df = update_data(existing_df, new_data_df)

    # Guardar los datos actualizados
    existing_df.to_csv("lordconejo_dataupdate.csv", index=False)

    print("Datos actualizados correctamente:")
    print(existing_df)

# Ejecutar el script
if __name__ == "__main__":
    main()
