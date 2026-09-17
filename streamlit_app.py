
import streamlit as st
import pandas as pd
import joblib
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime

st.set_page_config(page_title="EV Charge Finder", page_icon="🔋", layout="wide")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding: 0 32px !important; max-width: 100% !important; }

    @media (max-width: 900px) {
        div[data-testid="stHorizontalBlock"]:has(iframe) { flex-direction: column !important; }
    }

    div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    div[data-testid="element-container"] { margin: 0 !important; padding: 0 !important; }
    .stButton, .stLinkButton { margin: 0 !important; }

    .top-bar-wrapper { padding: 18px 0 14px 0; border-bottom: 1px solid #E5E7EB; }

    .brand-icon-only { display: none; }
    @media (max-width: 700px) {
        .brand-full { display: none !important; }
        .brand-icon-only { display: block !important; }
    }

    div[data-testid="stTextInput"] input {
        border-radius: 8px !important; border: 1px solid #E2E8F0 !important;
        padding: 8px 14px !important; font-size: 16px !important; font-weight: 700 !important; height: 42px !important;
    }
    div[data-testid="stTextInput"] input:focus { border-color: #7C3AED !important; box-shadow: none !important; }
    div[data-testid="stTextInput"] input::placeholder { font-weight: 600 !important; color: #94A3B8 !important; }

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) div[data-testid="column"]:nth-of-type(3) button {
        border-radius: 8px !important; border: none !important;
        background: #0F172A !important; color: white !important; font-weight: 800 !important;
        font-size: 16px !important; padding: 9px 16px !important; height: 42px !important;
        white-space: nowrap !important; width: auto !important;
    }

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) div[data-testid="column"]:nth-of-type(4) button {
        border-radius: 24px !important; border: 1px solid #BFDBFE !important;
        background: #DBEAFE !important; color: #1D4ED8 !important; font-weight: 700 !important;
        font-size: 15px !important; padding: 9px 18px !important; height: 42px !important;
        white-space: nowrap !important; width: auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) div[data-testid="column"]:nth-of-type(4) button:hover {
        background: #BFDBFE !important;
    }

    div[data-testid="stRadio"] {
        background: #FCFCFD; border: 1px solid #EEF0F3; border-radius: 12px;
        padding: 12px 16px; margin: 0 20px 12px 20px;
    }
    div[data-testid="stRadio"] label { font-size: 14px !important; color: #374151 !important; padding: 8px 4px !important; border-radius: 8px; }
    div[data-testid="stRadio"] label:hover { background: #F0FDF4; }

    .match-heading { padding: 16px 20px 2px 20px; font-size: 15px; color: #0F172A; font-weight: 800; }
    .match-subtext { padding: 0 20px 12px 20px; font-size: 13px; color: #94A3B8; }
    .confirm-wrap { padding: 0 20px 20px 20px; }
    .confirm-wrap button { background: #16A34A !important; border: none !important; }

    .panel { height: calc(100vh - 96px); overflow-y: auto; background: #FCFCFD; border-left: 1px solid #EEF0F3; padding: 18px 4px 60px 16px; }
    @media (max-width: 900px) {
        .panel { height: auto !important; border-left: none !important; border-top: 1px solid #EEF0F3; }
    }

    .weather-row { display: flex; gap: 18px; padding: 2px 4px 16px 4px; border-bottom: 1px solid #EEF0F3; margin-bottom: 14px !important; }
    .w-item { flex: 1; }
    .w-label { font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
    .w-value { font-size: 16px; color: #0F172A; font-weight: 700; margin-top: 1px; }

    .count-row { font-size: 13px; font-weight: 800; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 4px 12px 4px !important; }

    .station-card { background: #FFFFFF; border: 1px solid #EEF0F3; border-radius: 12px; padding: 14px 16px; margin: 0 0 10px 0 !important; }
    .station-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
    .station-name { font-size: 16px; font-weight: 700; color: #0F172A; line-height: 1.3; }
    .station-meta { font-size: 13px; color: #94A3B8; margin-top: 3px; }
    .wait-pill { font-size: 13px; font-weight: 800; padding: 4px 11px; border-radius: 20px; white-space: nowrap; }
    .wait-low { background: #D1FAE5; color: #047857; }
    .wait-med { background: #FEF3C7; color: #B45309; }
    .wait-high { background: #FEE2E2; color: #B91C1C; }

    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

model = joblib.load('wait_time_model.pkl')
station_id_map = joblib.load('station_id_map.pkl')
stations_df = pd.read_csv('stations.csv')

OWM_KEY = st.secrets["OWM_KEY"]
geolocator = Nominatim(user_agent="ev_charge_finder_app_v1")

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def get_weather(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OWM_KEY, "units": "metric"}
    resp = requests.get(url, params=params).json()
    if 'weather' not in resp:
        return False, None, "Unavailable"
    condition = resp['weather'][0]['main'].lower()
    is_raining = 'rain' in condition or 'drizzle' in condition
    return is_raining, resp['main']['temp'], resp['weather'][0]['description']

def escape_html(text):
    return str(text).replace("&", "&amp;").replace("'", "&#39;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def geocode_address(address):
    try:
        locations = geolocator.geocode(address + ", Bangalore, India", exactly_one=False, limit=5, timeout=10)
        if not locations:
            locations = geolocator.geocode(address, exactly_one=False, limit=5, timeout=10)
        return locations
    except Exception:
        return None

if 'user_lat' not in st.session_state:
    st.session_state.user_lat = None
    st.session_state.user_lon = None
if 'search_options' not in st.session_state:
    st.session_state.search_options = None

st.markdown("<div class='top-bar-wrapper'>", unsafe_allow_html=True)
top1, top2, top3, top4 = st.columns([0.9, 3, 1, 1.8])

with top1:
    st.markdown("<div class='brand-full' style='font-size:24px; font-weight:900; color:#0F172A; padding-top:2px; white-space:nowrap;'>⚡ EV Finder<div style='font-size:11px; font-weight:600; color:#94A3B8; margin-top:-2px;'>Bengaluru only</div></div><div class='brand-icon-only' style='font-size:26px; padding-top:6px;'>⚡</div>", unsafe_allow_html=True)

with top2:
    address = st.text_input(" ", placeholder="Search a location in Bengaluru...", label_visibility="collapsed")

with top3:
    search_clicked = st.button("Search", use_container_width=True)

with top4:
    locate_clicked = st.button("➤ Use my Current Location", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
if 'requesting_location' not in st.session_state:
    st.session_state.requesting_location = False

if locate_clicked:
    st.session_state.requesting_location = True

if st.session_state.requesting_location:
    loc_data = get_geolocation()
    if loc_data and 'error' in loc_data:
        error_code = loc_data['error']['code']
        error_msg = loc_data['error']['message']
        st.session_state.requesting_location = False
        if error_code == 1:
            st.error("Location permission was denied in the browser. Please allow location access and try again.")
        else:
            st.warning(f"Geolocation error: {error_msg}")
    elif loc_data and 'coords' in loc_data:
        st.session_state.user_lat = loc_data['coords']['latitude']
        st.session_state.user_lon = loc_data['coords']['longitude']
        st.session_state.search_options = None
        st.session_state.requesting_location = False
        st.rerun()
    else:
        st.info("Waiting for your browser's location response...")
if search_clicked and address:
    locations = geocode_address(address)
    if locations:
        if len(locations) == 1:
            st.session_state.user_lat = locations[0].latitude
            st.session_state.user_lon = locations[0].longitude
            st.session_state.search_options = None
        else:
            st.session_state.search_options = locations
    else:
        st.warning("Location not found — try a more specific address or an official place name.")
        st.session_state.search_options = None

if st.session_state.search_options:
    st.markdown("<div class='match-heading'>Multiple matches found</div><div class='match-subtext'>Select the correct location below</div>", unsafe_allow_html=True)
    options_labels = [loc.address for loc in st.session_state.search_options]
    chosen = st.radio(" ", options_labels, label_visibility="collapsed")
    st.markdown("<div class='confirm-wrap'>", unsafe_allow_html=True)
    if st.button("Confirm location"):
        idx = options_labels.index(chosen)
        selected = st.session_state.search_options[idx]
        st.session_state.user_lat = selected.latitude
        st.session_state.user_lon = selected.longitude
        st.session_state.search_options = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

user_lat = st.session_state.user_lat
user_lon = st.session_state.user_lon

@st.fragment
def show_results(user_lat, user_lon):
    is_raining, temp, description = get_weather(user_lat, user_lon)
    now = datetime.now()
    hour, day_of_week = now.hour, now.weekday()

    results = []
    for idx, station in stations_df.iterrows():
        dist = haversine_distance(user_lat, user_lon, station['latitude'], station['longitude'])
        encoded_id = station_id_map[station['station_id']]
        input_row = pd.DataFrame([{'station_id': encoded_id, 'day_of_week': day_of_week, 'hour': hour, 'is_raining': int(is_raining)}])
        predicted_wait = model.predict(input_row)[0]
        results.append({'Station': station['name'], 'Distance (km)': round(dist, 2), 'Wait': round(float(predicted_wait), 1), 'lat': station['latitude'], 'lon': station['longitude']})

    results_df = pd.DataFrame(results).assign(Score=lambda d: d['Wait'] + d['Distance (km)']*2).sort_values('Score').head(8).reset_index(drop=True)

    map_col, panel_col = st.columns([1.6, 1])

    with map_col:
        m = folium.Map(location=[user_lat, user_lon], zoom_start=13, tiles="OpenStreetMap", zoom_control=False)
        folium.Marker([user_lat, user_lon], icon=folium.Icon(color="blue", icon="circle", prefix="fa"), tooltip="You").add_to(m)
        for i, row in results_df.iterrows():
            color = "green" if row['Wait'] < 8 else "orange" if row['Wait'] < 15 else "red"
            folium.Marker([row['lat'], row['lon']], icon=folium.Icon(color=color, icon="bolt", prefix="fa"), tooltip=row['Station'] + " — " + str(row['Wait']) + " min").add_to(m)
        st_folium(m, height=780, use_container_width=True)

    with panel_col:
        weather_html = ""
        if temp:
            weather_html = "<div class='weather-row'><div class='w-item'><div class='w-label'>Temp</div><div class='w-value'>" + str(temp) + "°C</div></div><div class='w-item'><div class='w-label'>Sky</div><div class='w-value'>" + escape_html(description.title()) + "</div></div><div class='w-item'><div class='w-label'>Rain</div><div class='w-value'>" + ("Yes" if is_raining else "No") + "</div></div></div>"

        cards_html = "<div class='panel'>" + weather_html + "<div class='count-row'>" + str(len(results_df)) + " Stations Nearby</div>"

        for i, row in results_df.iterrows():
            badge_class = "wait-low" if row['Wait'] < 8 else "wait-med" if row['Wait'] < 15 else "wait-high"
            maps_url = "https://www.google.com/maps/dir/?api=1&origin=" + str(user_lat) + "," + str(user_lon) + "&destination=" + str(row['lat']) + "," + str(row['lon'])
            station_name_safe = escape_html(row['Station'])
            card = "<div class='station-card'><div class='station-top'><div><div class='station-name'>" + station_name_safe + "</div><div class='station-meta'>" + str(row['Distance (km)']) + " km away</div></div><div class='wait-pill " + badge_class + "'>" + str(row['Wait']) + " min</div></div><a href='" + maps_url + "' target='_blank' style='display:block; text-align:center; margin-top:8px; padding:7px 0; background:#7C3AED; color:white; border-radius:8px; font-size:13.5px; font-weight:700; text-decoration:none;'>Navigate</a></div>"
            cards_html = cards_html + card

        cards_html = cards_html + "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

if user_lat is not None and not st.session_state.search_options:
    show_results(user_lat, user_lon)
elif not st.session_state.search_options:
    st.markdown("""
    <div style='padding:32px 20px 8px 20px; max-width:820px;'>
        <div style='font-size:15px; color:#374151; line-height:1.6; margin-bottom:24px;'>
            Charging your EV shouldn't mean guessing which station has a free slot. 
            <b>EV Finder</b> looks at real charging stations in Bengaluru and predicts how long you'll likely wait at each one right now — based on time of day, weekday patterns, and weather — so you can head to the station that'll actually save you time.
        </div>
        <div style='display:flex; gap:24px; flex-wrap:wrap; margin-bottom:8px;'>
            <div style='flex:1; min-width:200px;'>
                <div style='font-size:13px; font-weight:800; color:#7C3AED; margin-bottom:4px;'>1. SHARE YOUR LOCATION</div>
                <div style='font-size:13px; color:#6B7280;'>Search an address or use your current location</div>
            </div>
            <div style='flex:1; min-width:200px;'>
                <div style='font-size:13px; font-weight:800; color:#7C3AED; margin-bottom:4px;'>2. SEE PREDICTED WAIT TIMES</div>
                <div style='font-size:13px; color:#6B7280;'>Nearby stations ranked by wait time + distance</div>
            </div>
            <div style='flex:1; min-width:200px;'>
                <div style='font-size:13px; font-weight:800; color:#7C3AED; margin-bottom:4px;'>3. NAVIGATE THERE</div>
                <div style='font-size:13px; color:#6B7280;'>One tap opens directions in Google Maps</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
