
import pandas as pd

CSV_FILE = "processed/analysis_output.csv"

def validate_stations(csv_path=CSV_FILE):
    df = pd.read_csv(csv_path)

    required_columns = ["station_id", "lat", "lon", "min_distance_m"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Brak wymaganej kolumny: {col}")

 
    if df[required_columns].isnull().any().any():
        raise ValueError("W danych znajdują się brakujące wartości!")


    if not df["lat"].between(-90, 90).all():
        raise ValueError("Są wartości lat poza zakresem -90 do 90")
    if not df["lon"].between(-180, 180).all():
        raise ValueError("Są wartości lon poza zakresem -180 do 180")
    if (df["min_distance_m"] < 0).any():
        raise ValueError("Są wartości min_distance_m mniejsze niż 0")


    if len(df) == 0:
        raise ValueError("Tabela stacji jest pusta!")

    print(" Walidacja danych stacji zakończona sukcesem")
    print(f"Liczba stacji: {len(df)}")

if __name__ == "__main__":
    validate_stations()
