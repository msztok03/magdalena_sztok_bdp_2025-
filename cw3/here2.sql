CREATE TABLE new_pois_near_buildings AS
SELECT p2019.category, COUNT(*) AS poi_count
FROM t2019_kar_poi_table p2019
LEFT JOIN t2018_kar_poi_table p2018
ON p2019.poi_id = p2018.poi_id
WHERE p2018.poi_id IS NULL  -- nowe POI
AND EXISTS (
    SELECT 1 FROM new_or_renovated_buildings b
    WHERE ST_DWithin(p2019.geom, b.geom, 500)
)
GROUP BY p2019.category;
