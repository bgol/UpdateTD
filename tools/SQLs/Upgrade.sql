select
	  Module.fdev_id as "upgrade_id"
	, Modulegroup.name as "name"
	, Module.class as "class"
	, Module.rating as "rating"
	, Ship.name as "ship"
  from Module
  join Modulegroup using(modulegroup_id)
  left join ModuleShip using(module_id)
  left join Ship using(ship_id)
 order by ship, name, class, rating
