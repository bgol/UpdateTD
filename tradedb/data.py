import csv
import os.path

from typing import TYPE_CHECKING, Any
from dataclasses import asdict


from .misc import insert_from_dict, update_from_dict, convert_dict_to_class
from .tables import Category, Item, Ship, Upgrade, RareItem

if TYPE_CHECKING:
    from .tradedb import TradeDB


def update_import_entry(
    tdb: "TradeDB", tbl_name: str, old_entry: Any, new_entry: Any, **id_columns
) -> bool:
    if old_entry != new_entry:
        if old_entry is None:
            stmt, bind = insert_from_dict(tbl_name, asdict(new_entry))
            tdb.logger.info(f"created {new_entry}")
        else:
            upd_columns = {}
            for col_name, old_value in asdict(old_entry).items():
                new_value = getattr(new_entry, col_name)
                if new_value != old_value:
                    upd_columns[col_name] = new_value
            stmt, bind = update_from_dict(tbl_name, upd_columns, **id_columns)
            tdb.logger.info(f"updated {id_columns}, {upd_columns}")
        tdb.execute(stmt, bind)
        return True
    return False

def import_standard_data(tdb: "TradeDB", plugin_dir: str) -> None:
    for table_name, table_class, table_cache, id_column in (
        ("Category", Category, tdb.category_by_id, "category_id"),
        ("Item", Item, tdb.item_by_id, "item_id"),
        ("Ship", Ship, tdb.ship_by_id, "ship_id"),
        ("Upgrade", Upgrade, tdb.upgrade_by_id, "upgrade_id"),
    ):
        import_file = os.path.join(plugin_dir, "data", f"{table_name}.csv")
        if not os.path.isfile(import_file):
            tdb.logger.warning(f"import file {import_file!r} not found")
            continue
        tdb.logger.info(f"import {import_file!r}")
        with open(import_file, encoding="UTF-8", newline="") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if table_name == "Category":
                    _ = tdb.get_Category(row["name"])
                    continue
                elif table_name == "Item":
                    row["category_id"] = tdb.get_Category(row.pop("name@Category.category_id")).category_id
                new_entry = convert_dict_to_class(table_class, row)
                id_value = getattr(new_entry, id_column)
                old_entry = table_cache.get(id_value)
                if update_import_entry(
                    tdb, table_name, old_entry, new_entry, **{id_column: id_value}
                ):
                    table_cache[id_value] = new_entry
                    if table_name == "Item":
                        tdb.reorder_item = True

    tdb.update_item_ui_order()
    tdb.logger.info("import done")

def fill_RareItem_cache(tdb: "TradeDB", plugin_dir: str) -> None:
    tdb.rareitem_cache.clear()
    if not tdb.use_rareitem_cache:
        return
    table_name = "RareItem"
    import_file = os.path.join(plugin_dir, "data", f"{table_name}.csv")
    if not os.path.isfile(import_file):
        tdb.logger.warning(f"import file {import_file!r} not found")
        return
    tdb.logger.info(f"fill cache {import_file!r}")
    with open(import_file, encoding="UTF-8", newline="") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if not (category := tdb.get_Category(row.pop("name@Category.category_id"))):
                continue
            row["category_id"] = category.category_id
            rareitem: RareItem = convert_dict_to_class(RareItem, row)
            if rareitem.rare_id in tdb.rareitem_by_id:
                continue
            if rareitem.station_id not in tdb.rareitem_cache:
                tdb.rareitem_cache[rareitem.station_id] = []
            tdb.rareitem_cache[rareitem.station_id].append(rareitem)
        tdb.logger.debug(f"{tdb.rareitem_cache = }")
    tdb.logger.info("cache filled")
