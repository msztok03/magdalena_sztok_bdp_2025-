import duckdb
import pandas as pd
import os
import json
import math

DB_FILE = "mydatabase.duckdb"
STATIONS_FOLDER = r"C:\Users\mszto\OneDrive\Pulpit\projekt_bazy\stations\stations"
TABLE_PATHS = "bike_paths_clean"

OUTPUT_CSV = "processed/analysis_output.csv"
os.makedirs("processed", exist_ok=True)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))


def parse_wkt_points(wkt):
    if not isinstance(wkt, str):
        return []

    txt = wkt.strip()


    if txt.upper().startswith("SRID="):
        txt = txt.split(";", 1)[1]

    txt = txt.strip()


    if txt.upper().startswith("POINT"):
        inner = txt[txt.find("(")+1 : txt.rfind(")")]
        parts = inner.split()
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            return [(lat, lon)]
        return []


    if txt.upper().startswith("LINESTRING"):
        inner = txt[txt.find("(")+1 : txt.rfind(")")]
        pts = []
        for pair in inner.split(","):
            parts = pair.strip().split()
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                pts.append((lat, lon))
        return pts

    return []



def load_stations():
    stations = []

    for root, _, files in os.walk(STATIONS_FOLDER):
        for file in files:
            if not file.endswith(".json"):
                continue
            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                continue

            items = data.get("stations_data") or []
            for s in items:
                lat = s.get("geoCoords", {}).get("lat")
                lon = s.get("geoCoords", {}).get("lng")
                if lat is None or lon is None:
                    continue

                stations.append({
                    "station_id": str(s.get("uid")),
                    "name": s.get("name"),
                    "lat": float(lat),
                    "lon": float(lon),
                })

    df = pd.DataFrame(stations)
    df = df.drop_duplicates(subset=["station_id"])
    return df



def load_paths_from_duckdb(con):
    try:
        rows = con.execute(f"SELECT id, geom FROM {TABLE_PATHS} ORDER BY id").fetchall()
    except Exception as e:
        print(f"[ERROR] Nie można odczytać {TABLE_PATHS}: {e}")
        return []

    all_points = []

    for row in rows:
        geom_text = row[1]
        pts = parse_wkt_points(geom_text)
        all_points.extend(pts)

 
    uniq = list({(round(a, 7), round(b, 7)) for (a, b) in all_points})
    return [(lat, lon) for (lat, lon) in uniq]



def compute_min_distance(st_lat, st_lon, path_points):
    best = float("inf")
    for lat, lon in path_points:
        d = haversine(st_lat, st_lon, lat, lon)
        if d < best:
            best = d
    return best



def main():
    print("[INFO] Łączenie z DuckDB…")
    con = duckdb.connect(DB_FILE)

    print("[INFO] Wczytywanie stacji…")
    df = load_stations()
    print(f"[INFO] Wczytano {len(df)} stacji.")

    print("[INFO] Wczytywanie ścieżek rowerowych z DB…")
    path_points = load_paths_from_duckdb(con)

    if not path_points:
        print("[WARN] Brak geometrii ścieżek — liczę dystans do centrum Warszawy.")
        path_points = [(52.2297, 21.0122)]

    print(f"[INFO] Punkty ścieżek: {len(path_points)}")

    print("[INFO] Liczenie minimalnych odległości…")
    distances = []

    for _, row in df.iterrows():
        dist = compute_min_distance(row["lat"], row["lon"], path_points)
        distances.append(dist)

    df["min_distance_m"] = distances
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[OK] Zapisano: {OUTPUT_CSV}")
    print("[DONE] Analiza zakończona.")


if __name__ == "__main__":
    main()
