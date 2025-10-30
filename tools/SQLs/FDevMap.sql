select
	  Item.fdev_id
	, Item.fdev_name
  from Item
 where not Item.is_rare
 order by Item.fdev_name
