-- c
SELECT 
    name, 
    ST_Area(geometry) AS area
FROM buildings
ORDER BY name;

