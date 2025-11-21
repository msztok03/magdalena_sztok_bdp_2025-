import pandas as pd
import numpy as np
import streamlit as st
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium


CSV_FILE = "processed/analysis_output.csv"

@st.cache_data
def load_data(csv_path=CSV_FILE):
    df = pd.read_csv(csv_path)

   
    for col in ["lat", "lon", "availableBikes", "min_distance_m"]:
        if col not in df.columns:
            df[col] = np.nan

    df = df.dropna(subset=["lat", "lon"])
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    if "availableBikes" in df.columns:
        df["availableBikes"] = df["availableBikes"].fillna(0).astype(int)
    if "min_distance_m" in df.columns:
        df["min_distance_m"] = df["min_distance_m"].astype(float)
    return df

df = load_data()

st.title("Dashboard stacji rowerowych")
st.sidebar.header("Filtry")


min_bikes = st.sidebar.slider(
    "Minimalna liczba dostępnych rowerów",
    0, int(df["availableBikes"].max() if "availableBikes" in df.columns else 0), 0
)
df_filtered = df[df["availableBikes"] >= min_bikes]

st.subheader("Heatmapa dostępnych rowerów")
map_center = [df_filtered["lat"].mean(), df_filtered["lon"].mean()] if not df_filtered.empty else [52.0, 21.0]
m = folium.Map(location=map_center, zoom_start=12)
heat_data = [[row["lat"], row["lon"], row["availableBikes"]] for idx, row in df_filtered.iterrows()]
if heat_data:
    HeatMap(heat_data).add_to(m)
st_folium(m, width=700, height=500)

st.subheader("Stacje z markerami i klastrami")
m2 = folium.Map(location=map_center, zoom_start=12)
marker_cluster = MarkerCluster().add_to(m2)

for idx, row in df_filtered.iterrows():
    popup_text = f"Stacja: {row.get('name','-')}<br>Rowery: {row.get('availableBikes','-')}<br>Odległość od ścieżki: {row.get('min_distance_m','-'):.2f} m"
    folium.Marker([row["lat"], row["lon"]], popup=popup_text).add_to(marker_cluster)

st_folium(m2, width=700, height=500)


st.subheader("Top N stacji najdalej od ścieżek")
top_n = st.sidebar.number_input("Ilość stacji do wyświetlenia", min_value=1, max_value=50, value=10, step=1)
if "min_distance_m" in df_filtered.columns:
    df_top = df_filtered.sort_values("min_distance_m", ascending=False).head(top_n)
    st.dataframe(df_top[["station_id", "name", "min_distance_m", "availableBikes"]])
else:
    st.info("Kolumna 'min_distance_m' nie istnieje. Uruchom najpierw analysis.py aby ją wygenerować.")

st.subheader("Histogram odległości od najbliższej ścieżki")
if "min_distance_m" in df_filtered.columns:
    st.bar_chart(df_filtered["min_distance_m"])
else:
    st.info("Brak kolumny 'min_distance_m' – histogram nie może zostać wyświetlony.")
