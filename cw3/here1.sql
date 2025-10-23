CREATE TABLE new_or_renovated_buildings AS
SELECT b2019.*
FROM t2019_kar_buildings b2019
LEFT JOIN t2018_kar_buildings b2018
ON ST_Equals(b2019.geom, b2018.geom)
WHERE b2018.geom IS NULL
   OR b2019.last_edit_date > b2018.last_edit_date;
