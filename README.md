# population-density-mapnik
A map style for displaying population density with mapnik based on OpenStreetMap data.

This map shows the population density in the OpenStreetMap germany extract (https://download.geofabrik.de/europe/germany.html) and the named areas with the highest and lowest density:
![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density.png) 

## Workflow to determine population data for boundaries:
- Search for boundary-areas with admin_level 4, 6 or 8
- If the boundary-area has a population-tag the needed data is found
- When the boundary-area has no population-tag and the boundary has no multiple outers, search for a place-node from type "municipality","borough","suburb","city","town" or "village" within the area which has a population-tag and the same name as the area. If such a place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- When the boundary-area has no population-tag and the boundary has multiple outers, search for unique place-node from type "municipality","borough","suburb","city","town" or "village" within all outers which has a population-tag and the same name as the area. If such a place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- With the found population data and the size for the boundary-area the population density is calculated
- Use orange for boundary-areas where no population was found
- Use different shades for green for the density value

## Detailed data processing: 
Import osm data with osm2pgsql to postgis database ([osm2pgsql-Style](population-density.style)) and open psql to start SQL statements. The import is time consuming and my notebook needs ~24h.
```
osm2pgsql -d population -r pbf --create --cache 1024 -S population-density.style -s --number-processes 1 germany-latest.osm.pbf
psql population
```
SQL statements to create the final table **tPopulationDensity**:
```
--Helper table 1: boundaries with multiple outers and population on boundary
DROP Table tMultiOuterPopulationOnPoly;
CREATE TABLE tMultiOuterPopulationOnPoly as (SELECT area.way, area.way_area, area.osm_id, area.name FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population similar to '[0-9]+' and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1));

--Helper table 2: sum all areas for boundaries with one or more outers
DROP Table tAreaSumKm2;
CREATE TABLE tAreaSumKm2 as (SELECT area.osm_id, area.name, Sum(ST_Area(ST_Transform(area.way,3035))/1000000) as area_km2 FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') group by area.osm_id, area.name);

--Helper table 3: boundaries with multiple outers and no poplation on boundary, but population on node
Drop Table tMultiOuterPopulationOnNode;
CREATE TABLE tMultiOuterPopulationOnNode as (SELECT area.way, area.way_area, area.name, area.osm_id, point.population FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population similar to '[0-9]+' WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and (area.population is null or  area.population not similar to '[0-9]+') and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1));

--Helper table 4: list of unique population of boundaries with multiple outers and no poplation on boundary, but population on node
Drop Table tMultiOuterPopulationOnUniqueNode;
CREATE TABLE tMultiOuterPopulationOnUniqueNode as (select osm_id, name, population, count(population) from tMultiOuterPopulationOnNode where population similar to '[0-9]+' group by osm_id, name, population having count(*) = 1);

--Create main table and insert helper tables
DROP TABLE tPopulationDensity;
CREATE TABLE tPopulationDensity as (select tMultiOuterPopulationOnPoly.way, tMultiOuterPopulationOnPoly.way_area, tMultiOuterPopulationOnPoly.name, tMultiOuterPopulationOnPoly.osm_id, Round(area.population::Integer/tAreaSumKm2.area_km2) as population_per_km2, area.population::Integer as population, tAreaSumKm2.area_km2 from tMultiOuterPopulationOnPoly, tAreaSumKm2,planet_osm_polygon as area where tMultiOuterPopulationOnPoly.osm_id = tAreaSumKm2.osm_id and tMultiOuterPopulationOnPoly.osm_id = area.osm_id);

INSERT INTO tPopulationDensity SELECT tMultiOuterPopulationOnNode.way, tMultiOuterPopulationOnNode.way_area, tMultiOuterPopulationOnNode.name, tMultiOuterPopulationOnNode.osm_id, Round(tMultiOuterPopulationOnUniqueNode.population::Integer / tAreaSumKm2.area_km2), tMultiOuterPopulationOnUniqueNode.population::Integer as population, tAreaSumKm2.area_km2  FROM tMultiOuterPopulationOnNode,tMultiOuterPopulationOnUniqueNode,tAreaSumKm2 where tMultiOuterPopulationOnNode.osm_id = tMultiOuterPopulationOnUniqueNode.osm_id and tMultiOuterPopulationOnNode.osm_id = tAreaSumKm2.osm_id;

--Insert all boundaries with one outer and population on boundary or node
INSERT INTO tPopulationDensity SELECT area.way, area.way_area, area.name, area.osm_id, Round(COALESCE(area.population,point.population)::Integer/(ST_Area(ST_Transform(area.way,3035))/1000000)) as population_per_km2, COALESCE(area.population,point.population)::Integer as population, ST_Area(ST_Transform(area.way,3035))/1000000 as area_km2 FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population similar to '[0-9]+' WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and (area.population similar to '[0-9]+' or point.population similar to '[0-9]+') and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) = 1);

--Insert boundaries with names and admin_level 6 or 8 and without population (set to null)
INSERT INTO tPopulationDensity SELECT area.way, area.way_area, area.name, area.osm_id, null as population_per_km2, null as population, tAreaSumKm2.area_km2 FROM planet_osm_polygon as area, tAreaSumKm2 where area.boundary='administrative' and area.admin_level IN ('6','8') and area.name is not null and area.osm_id = tAreaSumKm2.osm_id and not exists (select tPopulationDensity.osm_id from tPopulationDensity Where tPopulationDensity.osm_id = area.osm_id); 

--When creating a map for a specific country, it may be a good idea to filter only areas for the country
--DROP TABLE tPopulationDensityDE;
--CREATE Temp TABLE tPopulationDensityDE as (select tPopulationDensity.* from tPopulationDensity, planet_osm_polygon as border where ST_Contains(border.way,tPopulationDensity.way) and border.name = 'Deutschland' and border.admin_level = '2' and border.boundary='administrative');
--DROP TABLE tPopulationDensity;
--CREATE TABLE tPopulationDensity as (select * from tPopulationDensityDE);

--Add column for biggest and smallest population density
alter table tPopulationDensity add column flags varchar;
update tPopulationDensity SET flags = 'max' where population_per_km2 = (select max(population_per_km2) from tPopulationDensity);
update tPopulationDensity SET flags = 'min' where population_per_km2 = (select min(population_per_km2) from tPopulationDensity);
```
Now you can use renderd or an [Python-Script](population-density.py) to create a map ([mapnik-XML](population-density.xml)).

This should only be a demonstration how the process such OpenStreetMap data. If you really want exact and current population data, you should ask your goverment for official data.
