select
	  Item.fdev_id as "rare_id"
	, Rareitem.market_id as "station_id"
	, Category.name as "name@Category.category_id"
	, Item.name as "name"
	, Rareitem.supply_price as "cost"
	, Rareitem.supply_units as "max_allocation"
	, case when Rareitem.item_flags & (1<<0) then 'Y' else 'N' end as "illegal"
	, case when Rareitem.item_flags & (1<<1) then 'Y' else 'N' end as "suppressed"
  from Rareitem
  join Item using(item_id)
  join Category using(category_id)
 order by Category.name, Item.name
