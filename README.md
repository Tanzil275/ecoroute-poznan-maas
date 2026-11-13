# 🌱 EcoRoute Poznań: Multimodal Carbon-Aware Route Planner

An interactive Mobility-as-a-Service (MaaS) web application built in Python to evaluate urban transport sustainability in Poznań, Poland.

## Key Features
- **Multimodal Comparison:** Evaluates travel time, distance, and CO₂ emissions across Petrol Car, Electric Vehicle (EV), Public Transit (ZTM Tram/Bus), Bicycle, and Walking.
- **Real-Time Geospatial Routing:** Integrates separate OpenStreetMap (OSRM) routing engines for road networks, cycling lanes, and pedestrian paths.
- **Geocoding:** Supports custom street and landmark searches across Poznań via Nominatim.
- **Interactive Visualization:** Renders color-coded urban corridors using Folium and Leaflet.js.

## Tech Stack
- **Language:** Python 3
- **Frontend & UI:** Streamlit
- **Geospatial & Routing:** Folium, Geopy, OSRM API
