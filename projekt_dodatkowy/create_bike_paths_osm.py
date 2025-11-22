# create_bike_paths_osm.py
import os
import sys
import math
import duckdb
import pandas as pd

def install_check():
    try:
        import osmnx as ox  # noqa: F401
        import geopandas as gpd  # noqa: F401
        from shapely import wkt  # noqa: F401
    except Exception as e:
        print("Brak wymaganych pakietów (osmnx/geopandas/shapely). Zainstaluj: pip install osmnx geopandas shapely")
        raise e

DB_FILE = "mydatabase.duckdb"
TABLE_PATHS = "bike_paths_clean"
STATIONS_CSV = "processed/analysis_output.csv"

def bbox_from_stations(df, pad_meters=2000):
    min_lat, max_lat = df["lat"].min(), df["lat"].max()
    min_lon, max_lon = df["lon"].min(), df["lon"].max()
    mean_lat = (min_lat + max_lat) / 2.0
    deg_lat = pad_meters / 111320.0
    deg_lon = pad_meters / (111320.0 * max(0.01, math.cos(math.radians(mean_lat))))
    south = min_lat - deg_lat
    north = max_lat + deg_lat
    west = min_lon - deg_lon
    east = max_lon + deg_lon
    return north, south, east, west

def fetch_and_store_osm_paths(df_stations, db_file=DB_FILE, table_name=TABLE_PATHS):
    import osmnx as ox
    import geopandas as gpd

    n, s, e, w = bbox_from_stations(df_stations)
    print(f"[INFO] Pobieram OSM w bbox: north={n}, south={s}, east={e}, west={w}")

    tags = {"highway": True, "cycleway": True}
    bbox = (w, s, e, n)
    try:
        gdf = ox.features_from_bbox(bbox, tags)
    except Exception as e:
        print("[ERROR] Błąd pobierania OSM przez osmnx:", e)
        raise

    if gdf is None or gdf.empty:
        print("[WARN] Nie pobrano żadnych obiektów OSM w bbox.")
        gdf = gpd.GeoDataFrame(columns=["geometry"])

    def is_cyclelike(row):
        if "cycleway" in row and pd.notna(row["cycleway"]):
            return True
        hw = row.get("highway")
        if hw in ("cycleway", "path", "residential", "service", "primary", "secondary", "tertiary", "unclassified", "track"):
            if "bicycle" in row and pd.notna(row["bicycle"]):
                if str(row["bicycle"]).lower() in ("yes", "designated", "permissive"):
                    return True
                if str(row["bicycle"]).lower() == "no":
                    return False
            return True
        return False

    gdf["is_cyclelike"] = gdf.apply(lambda r: is_cyclelike(r), axis=1)
    candidates = gdf[gdf["is_cyclelike"] & gdf.geometry.notna()].copy()
    candidates = candidates[candidates.geometry.geom_type.isin(["LineString", "MultiLineString", "GeometryCollection"])]
    candidates = candidates.explode(ignore_index=True)
    candidates = candidates.to_crs(epsg=4326)
    candidates["wkt"] = candidates.geometry.apply(lambda g: g.wkt)

    out_df = pd.DataFrame({"id": range(1, len(candidates)+1), "geom": candidates["wkt"].values})
    if out_df.empty:
        print("[WARN] Brak candidate geometries po filtrowaniu.")
    else:
        print(f"[INFO] Przygotowano {len(out_df)} ścieżek do zapisu do DuckDB.")

    con = duckdb.connect(db_file)
    con.execute(f"DROP TABLE IF EXISTS {table_name};")
    con.register("tmp_paths_df", out_df)
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM tmp_paths_df;")
    con.unregister("tmp_paths_df")
    con.close()
    print(f"[OK] Zapisano {len(out_df)} geometrii do tabeli {table_name} w {db_file}")
    return len(out_df)

def recompute_distances_with_db_paths(db_file=DB_FILE, table_paths=TABLE_PATHS, stations_csv=STATIONS_CSV, output_csv=STATIONS_CSV):
    import duckdb
    import pandas as pd
    from shapely import wkt
    from shapely.geometry import Point, LineString, MultiLineString

    df = pd.read_csv(stations_csv)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)

    con = duckdb.connect(db_file)
    tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
    if table_paths not in tables:
        print(f"[ERROR] Tabela {table_paths} nie istnieje w DB.")
        return False

    rows = con.execute(f"SELECT geom FROM {table_paths}").fetchall()
    geometries = []
    for (geom_wkt,) in rows:
        try:
            g = wkt.loads(geom_wkt)
            if isinstance(g, (LineString, MultiLineString)):
                geometries.append(g)
        except Exception:
            continue

    if not geometries:
        print("[WARN] Brak poprawnych geometrii do wyliczeń.")
        return False

    print(f"[INFO] Liczymy minimalne odległości dla {len(df)} stacji i {len(geometries)} ścieżek...")

    out = []
    for idx, row in df.iterrows():
        point = Point(row["lon"], row["lat"])
        min_dist = float("inf")
        for geom in geometries:
            dist_deg = point.distance(geom)
            dist_m = dist_deg * 111320
            if dist_m < min_dist:
                min_dist = dist_m
        out.append({
            "station_id": row["station_id"],
            "name": row.get("name", ""),
            "lat": row["lat"],
            "lon": row["lon"],
            "min_distance_m": min_dist
        })

    pd.DataFrame(out).to_csv(output_csv, index=False)
    print(f"[OK] Policzone odległości i zapisano do {output_csv}")
    return True

def main():
    install_check()
    if not os.path.exists(STATIONS_CSV):
        print(f"[ERROR] Nie znaleziono pliku stacji: {STATIONS_CSV}. Uruchom analysis.py, by go wygenerować.")
        sys.exit(1)

    df = pd.read_csv(STATIONS_CSV)
    if df.empty:
        print("[ERROR] Plik stacji jest pusty.")
        sys.exit(1)

    n = fetch_and_store_osm_paths(df)
    if n == 0:
        print("[WARN] Nie pobrano żadnych ścieżek OSM. Sprawdź bounding box i połączenie internetowe.")

    recompute_distances_with_db_paths()

if __name__ == "__main__":
    main()
