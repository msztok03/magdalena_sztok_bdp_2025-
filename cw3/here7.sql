SELECT COUNT(*) AS sport_shops_near_parks
FROM t2019_kar_poi_table poi
JOIN land_use_a park ON ST_DWithin(poi.geom, park.geom, 300)
WHERE poi.category = 'Sporting Goods Store';
