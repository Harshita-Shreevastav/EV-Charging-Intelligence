# EV Charging Intelligence Platform

A Streamlit application that helps drivers find EV charging stations in Bengaluru. Enter an address or share your current location to see nearby stations ranked using predicted wait time and distance.

Live demo
https://ev-charging-intelligence-gaw8ebnrcrfrml6k8utnad.streamlit.app/

## Features

- Search for a Bengaluru address with OpenStreetMap geocoding.
- Use browser geolocation to find stations near your current position.
- Display nearby stations on an interactive Folium map.
- Predict station wait times using the bundled machine-learning model.
- Include time of day, day of week, and current rain conditions in predictions.
- Open turn-by-turn directions for a station in Google Maps.

## ML Approach

The platform uses XGBoost regression to predict EV charging
station wait time.

Features:
- Station ID
- Hour of day
- Day of week
- Rain condition

Model Performance:
- MAE: 1.58 minutes
- RMSE: 3.51 minutes

## Requirements

- Python 3.10 or newer
- An OpenWeatherMap API key
- A browser that can access location services, if using current location

## Installation

From the project directory, create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Create `.streamlit/secrets.toml` in the project directory and add your OpenWeatherMap key:

```toml
OWM_KEY = "your-openweathermap-api-key"
```

Do not commit this file or expose the key in source control. The application reads it with `st.secrets["OWM_KEY"]`.

## Run the application

```powershell
streamlit run streamlit_app.py
```

Streamlit normally opens the app at `http://localhost:8501`.

The browser may ask for permission to use your location. You can either allow it or search for a location manually. Weather data requires an active internet connection and a valid OpenWeatherMap key.

## How recommendations are ranked

For each station, the app predicts a wait time from:

- Encoded station ID
- Current hour
- Current day of the week
- Whether it is raining

The displayed ranking uses this score:

```text
score = predicted_wait_minutes + (distance_km * 2)
```

The eight stations with the lowest scores are shown.

## Project structure

| File | Purpose |
| --- | --- |
| `streamlit_app.py` | Main Streamlit user interface and recommendation workflow |
| `stations.csv` | Station locations and connector metadata for Bengaluru |
| `demand_data.csv` | Historical station demand and wait-time data |
| `wait_time_model.pkl` | Trained wait-time prediction model |
| `station_id_map.pkl` | Station ID encoding used by the model |
| `requirements.txt` | Python dependencies |
| `app.py` | Legacy FastAPI prototype; it is not the main application entry point |

## Data notes

The application expects the model artifacts, `stations.csv`, and `streamlit_app.py` to remain in the same directory. Station coordinates and metadata come from `stations.csv`; live weather is fetched from OpenWeatherMap; wait-time predictions come from the bundled model rather than a live charging-network feed.

## Development container

The repository includes `.devcontainer/devcontainer.json` for a Python 3.11 development container. It installs the requirements, forwards port `8501`, and starts the Streamlit app when the container is attached.
