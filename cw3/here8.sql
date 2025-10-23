CREATE TABLE t2019_kar_bridges AS
SELECT ST_Intersection(r.geom, w.geom) AS geom
FROM railways r
JOIN water_lines w
ON ST_Intersects(r.geom, w.geom);
