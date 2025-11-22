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
    df["availableBikes"] = df["availableBikes"].fillna(0).astype(int)
    df["min_distance_m"] = df["min_distance_m"].astype(float)

    return df


df = load_data()

df = df.drop_duplicates(subset=["station_id"])

st.title("Dashboard stacji rowerowych")
st.sidebar.header("Filtry")


max_bikes = int(df["availableBikes"].max()) if not df.empty else 0

min_bikes = st.sidebar.slider(
    "Minimalna liczba dostępnych rowerów",
    min_value=0,
    max_value=max_bikes if max_bikes > 0 else 1,
    value=0
)

df_filtered = df[df["availableBikes"] >= min_bikes]

st.subheader("Heatmapa dostępnych rowerów")

if df_filtered.empty:
    map_center = [52.0, 21.0]
else:
    map_center = [df_filtered["lat"].mean(), df_filtered["lon"].mean()]

m = folium.Map(location=map_center, zoom_start=12)

heat_data = [
    [row["lat"], row["lon"], row["availableBikes"]]
    for _, row in df_filtered.iterrows()
]

if heat_data:
    HeatMap(heat_data).add_to(m)
else:
    st.info("Brak danych do wygenerowania HeatMap.")

st_folium(m, width=700, height=500)


st.subheader("Stacje z markerami i klastrami")

m2 = folium.Map(location=map_center, zoom_start=12)
marker_cluster = MarkerCluster().add_to(m2)

for _, row in df_filtered.iterrows():
    popup_text = (
        f"Stacja: {row.get('name','-')}<br>"
        f"Rowery: {row.get('availableBikes','-')}<br>"
        f"Odległość od ścieżki: {row.get('min_distance_m', np.nan):.2f} m"
    )

    folium.Marker(
        [row["lat"], row["lon"]],
        popup=popup_text
    ).add_to(marker_cluster)

st_folium(m2, width=700, height=500)

st.subheader("Top N stacji najdalej od ścieżek")

max_rows = max(len(df_filtered), 1)

top_n = st.sidebar.number_input(
    "Ilość stacji do wyświetlenia",
    min_value=1,
    max_value=max_rows,
    value=min(10, max_rows),
    step=1
)

if "min_distance_m" in df_filtered.columns and not df_filtered.empty:
    df_top = df_filtered.sort_values("min_distance_m", ascending=False).head(top_n)
    st.dataframe(df_top[["station_id", "name", "min_distance_m", "availableBikes"]])
else:
    st.info("Brak danych do rankingu.")

st.subheader("Histogram odległości od najbliższej ścieżki")

if not df_filtered.empty:
    st.bar_chart(df_filtered["min_distance_m"].fillna(0))
else:
    st.info("Brak danych do histogramu.")
