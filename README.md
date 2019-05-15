# population-density-mapnik
An map style for displaying population density with mapnik based on OpenStreetMap data.

This map shows the population denstity in germany and was made from OpenStreetMap data. 
![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density.png)

![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density-legend.png)

Workflow to determine population data for boundaries:
- Search for boundary-areas with admin_level 4, 6 or 8
- If the boundary-area has an population-tag the needed data is found
- When the boundary-area has no population-tag and the boundary has no multiple outers, search for an place-node from type "municipality","borough","suburb","city","town" or "village" within the the area which has an population-tag and the same name as the area. If such an place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- With the found population data and the size for the boundary-area the population density is calculated
- Use different shades for green for the density value

Import osm data with osm2pgsql to postgis database ([osm2pgsql-Style](population-density.style), [mapnik-XML](population-density.xml)) and remove population data with no number format.
```
osm2pgsql -d population -r pbf --create --cache 1024 -S population-density.style -s --number-processes 1 germany-latest.osm.pbf
psql population -c "update planet_osm_polygon set population=NULL where population not similar to '[0-9]+';"
psql population -c "update planet_osm_point set population=NULL where population not similar to '[0-9]+';"
```
Create two helper tables for boundaries with more than one outer areas, check population-tag and calculate the sum of all outer ereas.
```
DROP Table tMulitOuter1;
CREATE TABLE tMultiOuter1 as (SELECT area.way, area.osm_id, area.name FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population is not null and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1));

DROP Table tMulitOuter2;
CREATE TABLE tMultiOuter2 as (SELECT area.osm_id, area.name, Sum(ST_Area(ST_Transform(area.way,3035))/1000000) as area_km2, area.population as population FROM planet_osm_polygon as area WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and area.population is not null and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) > 1) group by name, osm_id, population);
```
Create tPopulationDensity table and insert the helper tables.
```
DROP TABLE tPopulationDensity;
CREATE TABLE tPopulationDensity as (select tMultiOuter1.way, tMultiOuter1.name, tMultiOuter1.osm_id, Round(tMultiOuter2.population::Integer/tMultiOuter2.area_km2) as population_per_km2 from tMultiOuter1, tMultiOuter2 where tMultiOuter1.osm_id = tMultiOuter2.osm_id);
```
Insert all boundary areas with one outer area and an existing population-tag on the boundary or on an place-node within the area
```
INSERT INTO tPopulationDensity SELECT area.way, area.name, area.osm_id, Round(COALESCE(area.population,point.population)::Integer/(ST_Area(ST_Transform(area.way,3035))/1000000)) as population_per_km2 FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population is not null WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and not (area.population is null and point.population is null) and exists (select multi_outer_check.osm_id from planet_osm_polygon as multi_outer_check where multi_outer_check.osm_id = area.osm_id group by multi_outer_check.osm_id having count(*) = 1);
```
Insert boundary areas without an found population-tag and mark them with the value -1
```
INSERT INTO tPopulationDensity SELECT area.way, area.name, area.osm_id, -1 as population_per_km2 FROM planet_osm_polygon as area where area.boundary='administrative' and area.admin_level IN ('4','6','8')  and not exists (select tPopulationDensity.osm_id from tPopulationDensity Where tPopulationDensity.osm_id = area.osm_id); 

```

This should only be an demonstration how the process such OpenStreetMap data. If you really want exact and current population data, you should ask your goverment for official data.
