
from fastapi import FastAPI
import pandas as pd
import joblib
from math import radians, sin, cos, sqrt, atan2

app = FastAPI()

model = joblib.load('/content/drive/MyDrive/ev_project/wait_time_model.pkl')
station_id_map = joblib.load('/content/drive/MyDrive/ev_project/station_id_map.pkl')
stations_df = pd.read_csv('/content/drive/MyDrive/ev_project/stations.csv')

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

@app.get("/recommend")
def recommend_stations(user_lat: float, user_lon: float, hour: int, day_of_week: int, is_raining: bool, top_n: int = 5):
    results = []
    for idx, station in stations_df.iterrows():
        dist = haversine_distance(user_lat, user_lon, station['latitude'], station['longitude'])
        encoded_id = station_id_map[station['station_id']]
        
        input_row = pd.DataFrame([{
            'station_id': encoded_id,
            'day_of_week': day_of_week,
            'hour': hour,
            'is_raining': int(is_raining)
        }])
        predicted_wait = model.predict(input_row)[0]
        score = predicted_wait + (dist * 2)
        
        results.append({
            'name': station['name'],
            'distance_km': round(dist, 2),
            'predicted_wait_min': round(float(predicted_wait), 1),
            'score': round(float(score), 2)
        })
    
    results = sorted(results, key=lambda x: x['score'])[:top_n]
    return {"recommendations": results}
