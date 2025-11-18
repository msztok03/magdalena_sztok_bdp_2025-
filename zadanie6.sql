
CREATE TABLE schema_name.intersects AS  
SELECT a.rast, b.municipality 
FROM rasters.dem AS a, vectors.porto_parishes AS b  
WHERE ST_Intersects(a.rast, b.geom) AND b.municipality ILIKE 'porto';

ALTER TABLE schema_name.intersects
ADD COLUMN rid SERIAL PRIMARY KEY;

CREATE INDEX idx_intersects_rast_gist ON schema_name.intersects
USING gist (ST_ConvexHull(rast));

SELECT AddRasterConstraints('schema_name','intersects','rast');


CREATE TABLE schema_name.clip AS  
SELECT ST_Clip(a.rast, b.geom, true) AS rast, b.municipality  
FROM rasters.dem AS a, vectors.porto_parishes AS b  
WHERE ST_Intersects(a.rast, b.geom) AND b.municipality ILIKE 'porto';



CREATE TABLE schema_name.union AS  
SELECT ST_Union(ST_Clip(a.rast, b.geom, true)) AS rast
FROM rasters.dem AS a, vectors.porto_parishes AS b  
WHERE b.municipality ILIKE 'porto' AND ST_Intersects(b.geom,a.rast);



CREATE TABLE schema_name.porto_parishes AS 
WITH r AS (SELECT rast FROM rasters.dem LIMIT 1)
SELECT ST_AsRaster(a.geom, r.rast, '8BUI', a.id, -32767) AS rast
FROM vectors.porto_parishes AS a, r
WHERE a.municipality ILIKE 'porto';

DROP TABLE schema_name.porto_parishes;

CREATE TABLE schema_name.porto_parishes AS 
WITH r AS (SELECT rast FROM rasters.dem LIMIT 1)
SELECT ST_Union(ST_AsRaster(a.geom, r.rast, '8BUI', a.id, -32767)) AS rast
FROM vectors.porto_parishes AS a, r
WHERE a.municipality ILIKE 'porto';

DROP TABLE schema_name.porto_parishes;

CREATE TABLE schema_name.porto_parishes AS 
WITH r AS (SELECT rast FROM rasters.dem LIMIT 1)
SELECT ST_Tile(
    ST_Union(ST_AsRaster(a.geom, r.rast, '8BUI', a.id, -32767)),
    128, 128, true, -32767
) AS rast
FROM vectors.porto_parishes AS a, r
WHERE a.municipality ILIKE 'porto';


CREATE TABLE schema_name.intersection AS  
SELECT 
    a.rid, 
    (ST_Intersection(b.geom,a.rast)).geom,
    (ST_Intersection(b.geom,a.rast)).val
FROM rasters.landsat8 AS a, vectors.porto_parishes AS b  
WHERE b.parish ILIKE 'paranhos' AND ST_Intersects(b.geom,a.rast);

CREATE TABLE schema_name.dumppolygons AS 
SELECT 
    a.rid,
    (ST_DumpAsPolygons(ST_Clip(a.rast,b.geom))).geom,
    (ST_DumpAsPolygons(ST_Clip(a.rast,b.geom))).val
FROM rasters.landsat8 AS a, vectors.porto_parishes AS b  
WHERE b.parish ILIKE 'paranhos' AND ST_Intersects(b.geom,a.rast);



CREATE TABLE schema_name.landsat_nir AS 
SELECT rid, ST_Band(rast,4) AS rast
FROM rasters.landsat8;

CREATE TABLE schema_name.paranhos_dem AS 
SELECT a.rid, ST_Clip(a.rast, b.geom,true) AS rast
FROM rasters.dem AS a, vectors.porto_parishes AS b 
WHERE b.parish ILIKE 'paranhos' AND ST_Intersects(b.geom,a.rast);

CREATE TABLE schema_name.paranhos_slope AS 
SELECT a.rid, ST_Slope(a.rast,1,'32BF','PERCENTAGE') AS rast
FROM schema_name.paranhos_dem AS a;


CREATE TABLE schema_name.paranhos_slope_reclass AS 
SELECT a.rid,
ST_Reclass(a.rast,1,']0-15]:1,(15-30]:2,(30-9999:3','32BF',0)
FROM schema_name.paranhos_slope AS a;


SELECT ST_SummaryStats(a.rast)
FROM schema_name.paranhos_dem AS a;


SELECT ST_SummaryStats(ST_Union(a.rast))
FROM schema_name.paranhos_dem AS a;

WITH t AS (
    SELECT ST_SummaryStats(ST_Union(a.rast)) AS stats
    FROM schema_name.paranhos_dem AS a
)
SELECT (stats).min, (stats).max, (stats).mean FROM t;

WITH t AS (
 SELECT b.parish AS parish, ST_SummaryStats(ST_Union(ST_Clip(a.rast,b.geom,true))) AS stats
 FROM rasters.dem AS a, vectors.porto_parishes AS b
 WHERE b.municipality ILIKE 'porto' AND ST_Intersects(b.geom,a.rast)
 GROUP BY b.parish
)
SELECT parish,(stats).min,(stats).max,(stats).mean FROM t;

SELECT b.name, ST_Value(a.rast,(ST_Dump(b.geom)).geom)
FROM rasters.dem a, vectors.places AS b
WHERE ST_Intersects(a.rast,b.geom)
ORDER BY b.name;


CREATE TABLE schema_name.tpi30 AS 
SELECT ST_TPI(a.rast,1) AS rast
FROM rasters.dem a;

CREATE INDEX idx_tpi30_rast_gist ON schema_name.tpi30
USING gist (ST_ConvexHull(rast));

SELECT AddRasterConstraints('schema_name','tpi30','rast');


CREATE TABLE schema_name.tpi30_porto AS 
SELECT ST_TPI(a.rast,1) AS rast
FROM rasters.dem AS a, vectors.porto_parishes AS b  
WHERE ST_Intersects(a.rast, b.geom) AND b.municipality ILIKE 'porto';

CREATE INDEX idx_tpi30_porto_rast_gist ON schema_name.tpi30_porto
USING gist (ST_ConvexHull(rast));

SELECT AddRasterConstraints('schema_name','tpi30_porto','rast');



CREATE TABLE schema_name.porto_ndvi AS  
WITH r AS (
 SELECT a.rid, ST_Clip(a.rast, b.geom, true) AS rast
 FROM rasters.landsat8 AS a, vectors.porto_parishes AS b
 WHERE b.municipality ILIKE 'porto' AND ST_Intersects(b.geom,a.rast)
)
SELECT
 r.rid,
 ST_MapAlgebra(
   r.rast, 1,
   r.rast, 4,
   '([rast2.val] - [rast1.val]) / ([rast2.val] + [rast1.val])::float',
   '32BF'
 ) AS rast
FROM r;

CREATE INDEX idx_porto_ndvi_rast_gist ON schema_name.porto_ndvi
USING gist (ST_ConvexHull(rast));

SELECT AddRasterConstraints('schema_name','porto_ndvi','rast');


CREATE OR REPLACE FUNCTION schema_name.ndvi(
 value double precision[][][],
 pos integer[][],
 VARIADIC userargs text[]
) RETURNS double precision AS
$$
BEGIN
 RETURN (value[2][1][1] - value[1][1][1])/
        (value[2][1][1] + value[1][1][1]);
END;
$$ LANGUAGE plpgsql IMMUTABLE COST 1000;

CREATE TABLE schema_name.porto_ndvi2 AS  
WITH r AS (
 SELECT a.rid,ST_Clip(a.rast, b.geom,true) AS rast
 FROM rasters.landsat8 AS a, vectors.porto_parishes AS b
 WHERE b.municipality ILIKE 'porto' AND ST_Intersects(b.geom,a.rast)
)
SELECT
 r.rid,
 ST_MapAlgebra(
   r.rast, ARRAY[1,4],
   'schema_name.ndvi(double precision[], integer[], text[])'::regprocedure,
   '32BF'
 ) AS rast
FROM r;

CREATE INDEX idx_porto_ndvi2_rast_gist ON schema_name.porto_ndvi2
USING gist (ST_ConvexHull(rast));

SELECT AddRasterConstraints('schema_name','porto_ndvi2','rast');



SELECT ST_AsTiff(ST_Union(rast))
FROM schema_name.porto_ndvi;


SELECT ST_AsGDALRaster(
    ST_Union(rast),
    'GTiff',
    ARRAY['COMPRESS=DEFLATE','PREDICTOR=2','ZLEVEL=9']
)
FROM schema_name.porto_ndvi;

CREATE TABLE tmp_out AS
SELECT lo_from_bytea(
        0,
        ST_AsGDALRaster(
            ST_Union(rast),
            'GTiff',
            ARRAY['COMPRESS=DEFLATE','PREDICTOR=2','ZLEVEL=9']
        )
    ) AS loid
FROM schema_name.porto_ndvi;


