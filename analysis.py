import duckdb
import pandas as pd
import json
import os

DB_FILE = "mydatabase.duckdb"
TABLE_PATHS = "bike_paths_clean"
TABLE_STATIONS = "stations_static"
OUTPUT_GEOJSON = "processed/analysis_output.geojson"
OUTPUT_CSV = "processed/analysis_output.csv"


STATIONS_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "stations",
    "stations"
)


def load_stations_to_duckdb(con):
    """Wczytuje maksymalnie 100 plików JSON z folderu i tworzy tabelę stations_static w DuckDB"""
    if not os.path.exists(STATIONS_FOLDER):
        raise FileNotFoundError(f"Nie znaleziono folderu stacji: {STATIONS_FOLDER}")


    json_files = sorted(
        [f for f in os.listdir(STATIONS_FOLDER) if f.lower().endswith(".json")]
    )[:100]

    if not json_files:
        raise FileNotFoundError(f"Nie znaleziono żadnego pliku JSON w folderze: {STATIONS_FOLDER}")

    print(f"[INFO] Wczytywane pliki JSON: {len(json_files)} (limit = 100)")

    all_stations = []

    for file_name in json_files:
        path = os.path.join(STATIONS_FOLDER, file_name)
        print(f"[INFO] Wczytywany plik stacji: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for s in data.get("stations_data", []):
            all_stations.append({
                "station_id": s["uid"],
                "name": s.get("name", ""),
                "lat": s["geoCoords"]["lat"],
                "lon": s["geoCoords"]["lng"]
            })

    df_stations = pd.DataFrame(all_stations)
    con.execute(f"CREATE OR REPLACE TABLE {TABLE_STATIONS} AS SELECT * FROM df_stations")
    print(f"[INFO] Tabela {TABLE_STATIONS} utworzona w DuckDB")


def main():
    print("[INFO] Łączenie z DuckDB...")
    con = duckdb.connect(DB_FILE)

    print("[INFO] Instalacja i ładowanie rozszerzenia spatial...")
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    print("[INFO] Wczytywanie stacji z JSON do DuckDB...")
    load_stations_to_duckdb(con)

    print("[INFO] Tworzenie geometrii stacji i ścieżek rowerowych...")
    geom_paths = "ST_GeomFromText(geom)"
    geom_stations = "ST_Point(lon, lat)"

    print("[INFO] Liczenie odległości stacji od najbliższej ścieżki rowerowej...")
    query = f"""
    WITH stations AS (
        SELECT
            station_id,
            name,
            {geom_stations} AS geom
        FROM {TABLE_STATIONS}
    ),
    paths AS (
        SELECT
            id AS path_id,
            {geom_paths} AS geom
        FROM {TABLE_PATHS}
    ),
    distances AS (
        SELECT
            s.station_id,
            s.name,
            MIN(ST_Distance(s.geom, p.geom)) AS min_distance_m
        FROM stations s
        JOIN paths p
        ON TRUE
        GROUP BY s.station_id, s.name
    )
    SELECT *
    FROM distances
    ORDER BY min_distance_m;
    """

    df = con.execute(query).fetchdf()
    print("[INFO] Przykładowe wyniki:")
    print(df.head())

    os.makedirs("processed", exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[OK] Wynik zapisany do: {OUTPUT_CSV}")

    print("[INFO] Generowanie GeoJSON z lokalizacjami stacji...")
    geo_query = f"""
    WITH stations AS (
        SELECT
            station_id,
            name,
            {geom_stations} AS geom
        FROM {TABLE_STATIONS}
    ),
    distances AS (
        SELECT
            s.station_id,
            s.name,
            s.geom,
            MIN(ST_Distance(s.geom, p.geom)) AS min_distance_m
        FROM stations s
        JOIN (
            SELECT {geom_paths} AS geom FROM {TABLE_PATHS}
        ) p
        ON TRUE
        GROUP BY s.station_id, s.name, s.geom
    )
    SELECT
        station_id,
        name,
        min_distance_m,
        ST_AsGeoJSON(geom) AS geometry
    FROM distances;
    """

    gdf = con.execute(geo_query).fetchdf()

    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        f.write(
            '{"type":"FeatureCollection","features":[' +
            ",".join([
                (
                    f'{{"type":"Feature","geometry":{row.geometry},'
                    f'"properties":{{"station_id":"{row.station_id}",'
                    f'"name":"{row.name}",'
                    f'"min_distance_m":{row.min_distance_m}}}}}'
                )
                for _, row in gdf.iterrows()
            ]) +
            "]}"
        )

    print(f"[OK] GeoJSON zapisany do: {OUTPUT_GEOJSON}")
    print("[DONE] Analiza zakończona pomyślnie.")


if __name__ == "__main__":
    main()
