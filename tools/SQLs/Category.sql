select name as "name"
  from Category
 where category_id in (select category_id from Item)
 order by name
