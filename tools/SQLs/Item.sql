select
	  Item.fdev_id as "item_id"
	, Item.name as "name"
	, Category.name as "name@Category.category_id"
	, row_number() over (partition by Item.category_id order by Item.name) as "ui_order"
	, Item.mean_price as "avg_price"
	, Item.fdev_id as "fdev_id"
  from Item
  join Category using(category_id)
 where not Item.is_rare
 order by Category.name, Item.name
