
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE obiekty (
    id SERIAL PRIMARY KEY,
    nazwa VARCHAR(50),
    geometria geometry
);

-- a. obiekt1
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt1', ST_GeomFromText('LINESTRING(0 1, 1 1, 2 0, 3 1, 4 2, 5 1, 6 1)', 0));

-- b. obiekt2
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt2', ST_GeomFromText('POLYGON((10 6, 14 6, 16 4, 14 2, 13 2, 12 0, 10 2, 10 6))', 0));

-- c. obiekt3
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt3', ST_GeomFromText('POLYGON((7 15, 10 17, 12 13, 7 15))', 0));

-- d. obiekt4
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt4', ST_GeomFromText('POLYGON((20 20, 20.5 19.5, 22 19, 25 22, 26 21, 27 24, 25 25, 20 20))', 0));

-- e. obiekt5
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt5', ST_GeomFromText('LINESTRINGZ(30 30 59, 38 32 234)', 0));

-- f. obiekt6
INSERT INTO obiekty (nazwa, geometria) VALUES
('obiekt6', ST_GeomFromText('GEOMETRYCOLLECTION(LINESTRING(1 1, 3 2), POINT(4 2))', 0));

-- ZADANIE 1

WITH objs AS (
    SELECT
        (SELECT geometria FROM obiekty WHERE nazwa='obiekt3') AS g3,
        (SELECT geometria FROM obiekty WHERE nazwa='obiekt4') AS g4
),
shortest AS (
    SELECT ST_ShortestLine(g3, g4) AS sline FROM objs
)
SELECT 
    '1) Pole powierzchni bufora wokół najkrótszej linii' AS opis,
    ST_Area(ST_Buffer(sline, 5))::numeric(20,4) AS pole_bufora
FROM shortest;


-- ZADANIE 2

WITH src AS (
  SELECT id, geometria FROM obiekty WHERE nazwa='obiekt4'
),
prepared AS (
  SELECT id,
         CASE 
           WHEN GeometryType(geometria) LIKE '%LINESTRING%' THEN
                CASE 
                    WHEN ST_IsClosed(geometria) THEN geometria
                    ELSE ST_AddPoint(geometria, ST_StartPoint(geometria))
                END
           ELSE geometria
         END AS linia
  FROM src
),
poly AS (
  SELECT id,
         CASE 
            WHEN GeometryType(linia) LIKE '%LINESTRING%' THEN ST_MakePolygon(linia)
            ELSE linia
         END AS poly_geom
  FROM prepared
)
UPDATE obiekty o
SET geometria = (SELECT ST_MakeValid(poly_geom) FROM poly WHERE poly.id=o.id)
WHERE o.nazwa='obiekt4';



SELECT 
  '2) Obiekt4 po konwersji na POLYGON' AS opis,
  nazwa, ST_GeometryType(geometria) AS typ, ST_IsValid(geometria) AS poprawny
FROM obiekty WHERE nazwa='obiekt4';


-- ZADANIE 3

INSERT INTO obiekty (nazwa, geometria)
VALUES (
  'obiekt7',
  ST_Union(
    (SELECT geometria FROM obiekty WHERE nazwa='obiekt3'),
    (SELECT geometria FROM obiekty WHERE nazwa='obiekt4')
  )
);


-- ZADANIE 4

SELECT 
  '4) Suma pól buforów dla obiektów bez łuków' AS opis,
  SUM(ST_Area(ST_Buffer(geometria,5)))::numeric(20,4) AS suma_pol_buforow
FROM obiekty
WHERE ST_AsEWKT(geometria) = ST_AsEWKT(ST_CurveToLine(geometria));
