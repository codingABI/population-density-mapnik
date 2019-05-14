# population-density-mapnik
An map style for displaying population density with mapnik based on OpenStreetMap data.

This map shows the population denstity in germany and was made from OpenStreetMap data. 
![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density.png)

![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density-legend.png)

Workflow to determine population data for boundaries:
- Search for boundary-areas with admin_level 4, 6 or 8
- If the boundary-area has an population-tag the needed data is found
- When the boundary-area has no population-tag, search for an place-node from type "municipality","borough","suburb","city","town" or "village" within the the area which has an population-tag and the same name as the area. If such an place-node is found the population of the node is used for the boundary-area and the needed data is found too.
- With the found population data and the size for the boundary-area the population density is calculated
- Use different shades for green for the density value

The database query for this workflow looks like ([osm2pgsql-Style](population-density.style); [mapnik-XML](population-density.xml))
```
SELECT DISTINCT area.way, area.osm_id, area.name, Round(COALESCE(area.population,point.population)::Integer/(ST_Area(ST_Transform(area.way,3035))/1000000)) as population_per_km2 FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population is not null WHERE area.boundary='administrative' and area.admin_level IN ('4','6','8') and not (area.population is null and point.population is null) and ST_Area(ST_Transform(area.way,3035))/1000000) > 0 order by arey.way_area DESC) AS population_area
```

This should only be an demonstration how the process such OpenStreetMap data. If you really want exact and current population data, you should ask your goverment for official data.
