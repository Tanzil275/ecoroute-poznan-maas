import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# 1. Page Setup
st.set_page_config(page_title="EcoRoute Poznań | MaaS Planner", layout="wide")
st.title("🌱 EcoRoute: Multimodal Carbon-Aware Route Planner")
st.write("Evaluating urban transport sustainability in Poznań across Petrol Car, EV, Public Transit, Cycling, and Walking.")

# 2. Pre-set landmarks + Custom Address option
preset_locations = {
    "Poznań Główny (Main Train Station)": (52.4021, 16.9118),
    "Poznan University of Technology (Campus)": (52.4036, 16.9496),
    "Stary Rynek (Old Market Square)": (52.4082, 16.9335),
    "Malta Lake (Recreational Area)": (52.4044, 16.9698),
    "Poznań-Ławica Airport": (52.4210, 16.8263),
    "Custom Address in Poznań...": None
}

# Helper function to convert typed address to (lat, lon)
def geocode_address(address_text):
    geolocator = Nominatim(user_agent="ecoroute_put_student_project")
    location = geolocator.geocode(f"{address_text}, Poznań, Poland", timeout=10)
    if location:
        return (location.latitude, location.longitude)
    return None

# 3. Sidebar Inputs
st.sidebar.header("1. Select Origin & Destination")
start_choice = st.sidebar.selectbox("Starting Point", list(preset_locations.keys()), index=0)
if start_choice == "Custom Address in Poznań...":
    custom_start = st.sidebar.text_input("Enter Start Street/Place", "ul. Półwiejska 42")
    start_coords = geocode_address(custom_start)
    start_label = custom_start
else:
    start_coords = preset_locations[start_choice]
    start_label = start_choice

end_choice = st.sidebar.selectbox("Destination", list(preset_locations.keys()), index=1)
if end_choice == "Custom Address in Poznań...":
    custom_end = st.sidebar.text_input("Enter Destination Street/Place", "Cytadela Park")
    end_coords = geocode_address(custom_end)
    end_label = custom_end
else:
    end_coords = preset_locations[end_choice]
    end_label = end_choice

# Carbon Emission Factors (g CO2 per passenger-km, EEA European averages)
st.sidebar.header("2. Emission Factors (g CO₂/km)")
car_factor = st.sidebar.slider("Petrol Car", 120, 250, 170)
ev_factor = st.sidebar.slider("Electric Car (Poland Grid Mix)", 40, 120, 75)
transit_factor = st.sidebar.slider("ZTM Tram / Bus (per passenger)", 15, 60, 35)

# 4. Separate Routing Engines for Car, Bike, and Foot
def get_osrm_route(start_latlon, end_latlon, mode):
    lat1, lon1 = start_latlon
    lat2, lon2 = end_latlon
    
    # Dedicated servers for each mode so bike lanes & footpaths are used accurately
    servers = {
        "car": "routed-car",
        "bike": "routed-bike",
        "foot": "routed-foot"
    }
    
    domain = "routing.openstreetmap.de"
    path = "/".join([servers[mode], "route", "v1", "driving", f"{lon1},{lat1};{lon2},{lat2}"])
    url = "https://" + domain + "/" + path + "?overview=full&geometries=geojson"
    
    response = requests.get(url, timeout=10).json()
    route_data = next(iter(response["routes"]))
    dist_km = round(route_data["distance"] / 1000, 2)
    time_min = round(route_data["duration"] / 60, 1)
    geometry = route_data["geometry"]
    return dist_km, time_min, geometry

# 5. Main Execution
if not start_coords or not end_coords:
    st.warning("Could not find one of the custom addresses in Poznań. Try adding a street name or landmark.")
elif start_coords == end_coords:
    st.warning("Please select two different locations.")
else:
    try:
        # Fetch separate real routes for Car, Bike, and Walking
        car_dist, car_time, car_geom = get_osrm_route(start_coords, end_coords, "car")
        bike_dist, bike_time, bike_geom = get_osrm_route(start_coords, end_coords, "bike")
        walk_dist, walk_time, walk_geom = get_osrm_route(start_coords, end_coords, "foot")

        # Model Multimodal ZTM Public Transit (approx 1.15x road distance, avg 22 km/h + 5 min stop wait)
        transit_dist = round(car_dist * 1.15, 2)
        transit_time = round((transit_dist / 22.0) * 60 + 5, 1)

        # Calculate Emissions (grams of CO2)
        car_co2 = round(car_dist * car_factor)
        ev_co2 = round(car_dist * ev_factor)
        transit_co2 = round(transit_dist * transit_factor)

        # Unpack coordinates safely to center the map
        lat1, lon1 = start_coords
        lat2, lon2 = end_coords
        m = folium.Map(location=[(lat1 + lat2) / 2, (lon1 + lon2) / 2], zoom_start=13)
        
        folium.GeoJson(car_geom, name="🚗 Car / EV Route", style_function=lambda x: {"color": "red", "weight": 5, "opacity": 0.6}).add_to(m)
        folium.GeoJson(bike_geom, name="🚲 Bicycle Route", style_function=lambda x: {"color": "green", "weight": 5, "opacity": 0.7}).add_to(m)
        folium.GeoJson(walk_geom, name="🚶 Walking Route", style_function=lambda x: {"color": "blue", "weight": 4, "opacity": 0.7, "dashArray": "5, 5"}).add_to(m)

        folium.Marker(list(start_coords), popup=f"Start: {start_label}", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(list(end_coords), popup=f"End: {end_label}", icon=folium.Icon(color="red")).add_to(m)
        folium.LayerControl().add_to(m)

        # Display 5-Mode Sustainability Matrix
        st.subheader("📊 Multimodal Sustainability Comparison")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.markdown("### 🚗 Petrol Car")
            st.metric("Time", f"{car_time} min")
            st.write(f"Distance: **{car_dist} km**")
            st.error(f"CO₂: **{car_co2} g**")

        with c2:
            st.markdown("### ⚡ Electric Car")
            st.metric("Time", f"{car_time} min")
            st.write(f"Distance: **{car_dist} km**")
            st.warning(f"CO₂: **{ev_co2} g** (-{car_co2 - ev_co2} g)")

        with c3:
            st.markdown("### 🚋 Public Transit")
            st.metric("Time", f"{transit_time} min")
            st.write(f"Distance: **{transit_dist} km**")
            st.info(f"CO₂: **{transit_co2} g** (-{car_co2 - transit_co2} g)")

        with c4:
            st.markdown("### 🚲 Bicycle")
            st.metric("Time", f"{bike_time} min")
            st.write(f"Distance: **{bike_dist} km**")
            st.success(f"CO₂: **0 g** (-{car_co2} g)")

        with c5:
            st.markdown("### 🚶 Walking")
            st.metric("Time", f"{walk_time} min")
            st.write(f"Distance: **{walk_dist} km**")
            st.success(f"CO₂: **0 g** (-{car_co2} g)")

        # Display Map
        st.subheader("🗺️ Urban Corridor Visualization")
        st_folium(m, width=1100, height=500)

    except Exception as e:
        st.error(f"Error calculating routes: {e}")
