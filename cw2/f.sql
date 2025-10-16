-- f
SELECT 
    ST_Area(ST_Difference(bc.geometry, ST_Buffer(bb.geometry, 0.5))) AS area
FROM buildings bc
JOIN buildings bb ON bb.name = 'BuildingB'
WHERE bc.name = 'BuildingC';


