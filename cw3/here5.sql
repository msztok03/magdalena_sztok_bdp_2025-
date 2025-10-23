ALTER TABLE input_points ADD COLUMN geom_3068 geometry(Point, 3068);

UPDATE input_points
SET geom_3068 = ST_Transform(geom, 3068);
