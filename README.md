# population-density-mapnik
An map style for displaying population density with mapnik based on OpenStreetMap data.

This map shows the population density in germany and was made from OpenStreetMap data. 
![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density.png)

## Workflow to determine population data for boundaries:
- Search for boundary-areas with admin_level 4, 6 or 8
- If the boundary-area has an population-tag the needed data is found
- When the boundary-area has no population-tag and the boundary has no multiple outers, search for an place-node from type "municipality","borough","suburb","city","town" or "village" within the area which has an population-tag and the same name as the area. If such an place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- When the boundary-area has no population-tag and the boundary has multiple outers, search for unique place-node from type "municipality","borough","suburb","city","town" or "village" within all outers which has an population-tag and the same name as the area. If such an place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- With the found population data and the size for the boundary-area the population density is calculated
- Use different shades for green for the density value

## Detailed data processing: 
Import osm data with osm2pgsql to postgis database ([osm2pgsql-Style](population-density.style), [mapnik-XML](population-density.xml)) and open psql.
```
osm2pgsql -d population -r pbf --create --cache 1024 -S population-density.style -s --number-processes 1 germany-latest.osm.pbf
psql population
```
SQL statements to create final table tPopulationDensity
```
--remove population data with invalid number format
update planet_osm_polygon set population=NULL where population not similar to '[0-9]+';
update planet_osm_point set population=NULL where population not similar to '[0-9]+';

--boundaries with multiple outers and population on boundary
DROP Table tMultiOuter1;
CREATE TABLE tMultiOuter1 as (SELECT area.way, area.way_area, area.osm_id, area.name FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population is not null and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1));

--sum all areas for boundaries with multiple outers
DROP Table tMultiOuter2;
CREATE TABLE tMultiOuter2 as (SELECT area.osm_id, area.name, Sum(ST_Area(ST_Transform(area.way,3035))/1000000) as area_km2, area.population as population FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population is not null and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1) group by name, osm_id, population);

--boundaries with multiple outers and no poplation on boundary, but population on node
Drop Table tMultiOuter3;
CREATE TABLE tMultiOuter3 as (SELECT area.way, area.way_area, area.name, area.osm_id, point.population FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population is not null WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population is null and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1));

--list of unique population of boundaries with multiple outers and no poplation on boundary, but population on node
Drop Table tMultiOuter4;
CREATE TABLE tMultiOuter4 as (select osm_id, name, population, count(population) from tMultiOuter3 where population is not null group by osm_id, name, population having count(*) = 1);

--areas in sum of boundaries with multiple outers and no poplation on boundary, but population on node
DROP Table tMultiOuter5;
CREATE TABLE tMultiOuter5 as (SELECT tMultiOuter3.osm_id, tMultiOuter3.name, Sum(ST_Area(ST_Transform(tMultiOuter3.way,3035))/1000000) as area_km2 FROM tMultiOuter3 group by name, osm_id);

--create main table and insert helper tables
DROP TABLE tPopulationDensity;
CREATE TABLE tPopulationDensity as (select tMultiOuter1.way, tMultiOuter1.way_area, tMultiOuter1.name, tMultiOuter1.osm_id, Round(tMultiOuter2.population::Integer/tMultiOuter2.area_km2) as population_per_km2 from tMultiOuter1, tMultiOuter2 where tMultiOuter1.osm_id = tMultiOuter2.osm_id);

INSERT INTO tPopulationDensity SELECT tMultiOuter3.way, tMultiOuter3.way_area, tMultiOuter3.name, tMultiOuter3.osm_id, Round(tMultiOuter4.population::Integer / tMultiOuter5.area_km2) FROM tMultiOuter3,tMultiOuter4,tMultiOuter5 where tMultiOuter3.osm_id = tMultiOuter4.osm_id and tMultiOuter3.osm_id = tMultiOuter5.osm_id;

--insert all boundaries with one outer and population on boundary or node
INSERT INTO tPopulationDensity SELECT area.way, area.way_area, area.name, area.osm_id, Round(COALESCE(area.population,point.population)::Integer/(ST_Area(ST_Transform(area.way,3035))/1000000)) as population_per_km2 FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population is not null WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and not (area.population is null and point.population is null) and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) = 1);

--insert boundaries without population (= -1)
INSERT INTO tPopulationDensity SELECT area.way, area.way_area, area.name, area.osm_id, -1 as population_per_km2 FROM planet_osm_polygon as area where area.boundary='administrative' and area.admin_level IN ('4','6','8')  and not exists (select tPopulationDensity.osm_id from tPopulationDensity Where tPopulationDensity.osm_id = area.osm_id); 
```

This should only be an demonstration how the process such OpenStreetMap data. If you really want exact and current population data, you should ask your goverment for official data.
