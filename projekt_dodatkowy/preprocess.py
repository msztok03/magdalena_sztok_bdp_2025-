import duckdb
from utils import DB_PATH


con = duckdb.connect(str(DB_PATH))
con.execute("LOAD spatial;")


con.execute("DROP TABLE IF EXISTS bike_paths_clean;")
con.execute('''
CREATE TABLE bike_paths_clean AS
SELECT
*,
ST_Length(geom) AS length_m,
ST_IsValid(geom) AS valid_geom
FROM bike_paths;
''')


con.execute("DROP TABLE IF EXISTS stations_snapshots;")
con.execute('''
CREATE TABLE stations_snapshots AS
SELECT
json_extract_scalar(value, '$.station_id')::INTEGER AS station_id,
json_extract_scalar(value, '$.last_update') AS last_update,
json_extract_scalar(value, '$.available_bikes')::INTEGER AS available_bikes,
json_extract_scalar(value, '$.free_places')::INTEGER AS free_places,
json_extract_scalar(value, '$.latitude')::DOUBLE AS latitude,
json_extract_scalar(value, '$.longitude')::DOUBLE AS longitude
FROM (SELECT json_parse(json) AS value FROM stations_raw)
WHERE json_extract_scalar(value, '$.latitude') IS NOT NULL;
''')

con.execute("ALTER TABLE stations_snapshots ADD COLUMN geom GEOMETRY;")
con.execute("UPDATE stations_snapshots SET geom = ST_Point(longitude, latitude) WHERE longitude IS NOT NULL AND latitude IS NOT NULL;")



con.execute("DROP TABLE IF EXISTS stations_hourly_summary;")
con.execute('''
CREATE TABLE stations_hourly_summary AS
SELECT
station_id,
date_trunc('hour', TO_TIMESTAMP(last_update)) AS hour,
AVG(available_bikes) AS avg_available_bikes,
MIN(available_bikes) AS min_available_bikes,
MAX(available_bikes) AS max_available_bikes
FROM stations_snapshots
GROUP BY station_id, date_trunc('hour', TO_TIMESTAMP(last_update));
''')


con.close()
