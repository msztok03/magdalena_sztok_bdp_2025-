CREATE TABLE input_line AS
SELECT ST_MakeLine(geom_3068 ORDER BY id) AS geom FROM input_points;


CREATE TABLE nearby_intersections AS
SELECT n.*
FROM t2019_street_node n
JOIN input_line l ON ST_DWithin(ST_Transform(n.geom, 3068), l.geom, 200);
