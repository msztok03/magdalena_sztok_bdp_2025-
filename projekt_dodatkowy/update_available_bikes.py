import os
import json
import pandas as pd

CSV_FILE = "processed/analysis_output.csv"
JSON_DIR = "stations/stations"
MAX_FILES = 100

csv_df = pd.read_csv(CSV_FILE)
csv_df["station_id"] = csv_df["station_id"].astype(str)

all_stations = []

json_files = sorted(os.listdir(JSON_DIR))[:MAX_FILES]

for idx, jf in enumerate(json_files, 1):
    print(f"Wczytuję plik {idx}/{len(json_files)}: {jf}")
    try:
        with open(os.path.join(JSON_DIR, jf), "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        print(" - błąd JSON, pomijam")
        continue

    stations_list = (
        data.get("stations_data")
        or data.get("stations")
        or data.get("station_data")
        or None
    )

    if not stations_list:
        print(" - brak listy stacji, pomijam")
        continue

    for s in stations_list:
        station_id = (
            s.get("uid") or
            s.get("number") or
            s.get("id") or
            s.get("station_id")
        )
        if station_id is None:
            continue

        available_bikes = (
            s.get("availabilityStatus", {}).get("availableBikes")
            or s.get("availableBikes")
            or s.get("num_bikes_available")
            or 0
        )

        all_stations.append({
            "station_id": str(station_id),
            "availableBikes": int(available_bikes)
        })

if not all_stations:
    print("Nie znaleziono żadnych danych o stacjach — żaden JSON nie miał właściwej struktury.")
else:
    df_stations = pd.DataFrame(all_stations)
    df_stations["station_id"] = df_stations["station_id"].astype(str)

    df_merged = csv_df.merge(df_stations, on="station_id", how="left")
    df_merged["availableBikes"] = df_merged["availableBikes"].fillna(0).astype(int)

    df_merged.to_csv(CSV_FILE, index=False)
    print(f"️ Zaktualizowano {len(df_stations)} stacji")
