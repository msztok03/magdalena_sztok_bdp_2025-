CREATE TABLE streets_reprojected AS
SELECT id, ST_Transform(geom, 3068) AS geom
FROM t2019_kar_streets;
