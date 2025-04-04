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
        "metric": "reach,total_interactions,accounts_engaged,likes,comments,saves,shares,replies,follows_and_unfollows,profile_links_taps",
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

def process_data(data, date_str):
    """
    Procesa los datos obtenidos de la API y los convierte en un DataFrame.

    Parámetros:
    - data: Datos en formato JSON obtenidos de la API.
    - date_str: Fecha en formato 'dd/mm/yyyy'.

    Retorna:
    - DataFrame con las métricas estructuradas.
    """
    expected_metrics = [
        "reach", "total_interactions", "accounts_engaged", "likes", "comments",
        "saves", "shares", "replies", "follows_and_unfollows", "profile_links_taps"
    ]
    
    # Diccionario con valores predeterminados en 0
    metrics = {metric: 0 for metric in expected_metrics}

    # Extraer valores de la API
    for metric in data.get('data', []):
        metric_name = metric['name']
        if metric_name in metrics and 'total_value' in metric and 'value' in metric['total_value']:
            metrics[metric_name] = metric['total_value']['value']

    # Crear DataFrame con la fecha proporcionada
    df = pd.DataFrame([metrics])
    
    # Convertir la fecha a formato `datetime`
    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')

    df['Date'] = date_obj.strftime('%d/%m/%Y')
    df['Month'] = date_obj.strftime('%B')
    df['Day of the Week'] = date_obj.strftime('%A')

    # Reordenar columnas
    columns_order = ['Month', 'Date', 'Day of the Week'] + expected_metrics
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
    access_token = "EABCSxik8s3MBO3d2GWN26zvDBZCnMOrdqAtY0WA6YpKO8tUVb2KE9lTSHjTRdWe8Ngl9E1KlpmVxfTcStipCbtmXXJiqO4JcEvp3UXBzqoBVZB8vF4iIgfyVZAGObZBna34h7wHLYrfKWEXjUlvhAZCFQzhOOoGcUzYrkW8XjJcBPMOgpbZBCGJysRacOHrjD48Fejmcpfhypk7ngy6xp9iJJAHHgJpmtrvxp3fNoG"
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
            new_data_df = process_data(data, date_to_fetch)

            # Actualizar el DataFrame existente
            existing_df = update_data(existing_df, new_data_df)

    # Guardar los datos actualizados
    existing_df.to_csv("lordconejo_dataupdate.csv", index=False)

    print("Datos actualizados correctamente:")
    print(existing_df)

# Ejecutar el script
if __name__ == "__main__":
    main()
