import duckdb
import geopandas as gpd
import pandas as pd
import os
import json

DB_PATH = "spatial_duck.db"


def load_geojson_as_df(path):
    gdf = gpd.read_file(path)
    
    gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkt if geom else None)
    return gdf


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return pd.DataFrame(data)
    

    elif isinstance(data, dict):
        first_key = list(data.keys())[0]
        return pd.DataFrame(data[first_key])
    
    else:
        raise ValueError("Nieznany format JSON")

def load_csv(path):
    return pd.read_csv(path)

def main():
    con = duckdb.connect(DB_PATH)
    
    
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    print("Ładowanie danych...")

    
    if os.path.exists("bike_paths.json"):
        con.execute("DROP TABLE IF EXISTS bike_paths;")
        
        df_paths = load_json("bike_paths.json")
        con.register("df_paths", df_paths)
        con.execute("CREATE TABLE bike_paths AS SELECT * FROM df_paths;")
        print("Załadowano bike_paths.json")

    if os.path.exists("bike_stations_with_attributes.geojson"):
        con.execute("DROP TABLE IF EXISTS bike_stations;")
        
        gdf_stations = load_geojson_as_df("bike_stations_with_attributes.geojson")
        con.register("gdf_stations", gdf_stations)
        con.execute("CREATE TABLE bike_stations AS SELECT * FROM gdf_stations;")
        print("Załadowano stacje rowerowe")

    if os.path.exists("weather_data.csv"):
        con.execute("DROP TABLE IF EXISTS weather;")
        
        df_weather = load_csv("weather_data.csv")
        con.register("df_weather", df_weather)
        con.execute("CREATE TABLE weather AS SELECT * FROM df_weather;")
        print("Załadowano dane pogodowe")

    print("Wszystkie dane zostały załadowane do DuckDB!")

if __name__ == "__main__":
    main()
