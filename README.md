# population-density-mapnik
An map style for displaying population density with mapnik based on OpenStreetMap data.

This map shows the population denstity in germany and was made from OpenStreetMap data. The population-tag in OpenStreetMap from boundaries or place-notes within the boundaries was devided by the size of the boundary. So we get the number of people per square kilormetre and we use different shades of green to show this value.

![alt text](https://github.com/codingABI/population-density-mapnik/blob/master/population-density-legend.png)

Workflow to determine population data for bounaries:
- Search for boundary-relations with admin_level 6 or 8
- If the boundary-relation has an population-tag the needed data is found
- When the boundary-relation has no population-tag, search for an place-node "municipality","borough","suburb","city","town" or "village" within the the erea of the relation which has an population-tag and the same name as the relation. If such an place-node is found the population of the node is used for the boundary-relation and the needed data is found too.
- With the found population data and the size for the boundary-relation the population density is calculated

The database query for this workflow looks like
```
SELECT DISTINCT area.way, area.osm_id, area.name, Round(COALESCE(area.population,point.population)::Integer/(ST_Area(ST_Transform(area.way,3035))/1000000)) as population_per_km2 FROM planet_osm_polygon as area FULL OUTER JOIN planet_osm_point as point ON st_contains(area.way,point.way) and point.place IN ('municipality','borough','suburb','city','town','village') and area.name=point.name and point.population is not null WHERE area.boundary='administrative' and area.admin_level IN ('6','8') and not (area.population is null and point.population is null) order by arey.way_area DESC) AS population_area
```

This should only be an demonstration how the process such OpenStreetMap data. If you really want exact and current population data, you should ask your goverment for official data.


More content and scripts is coming soon...
