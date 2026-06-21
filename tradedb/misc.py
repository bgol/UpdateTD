import sqlite3

from typing import Any
from collections.abc import Iterable, Callable
from dataclasses import dataclass, fields

from .const import REGEX_NORMALIZE_NAME
from .tables import Station, Item, StationItem
from .tables_new import StationNew, ItemNew, StationItemNew


def snap_to_grid(val: float) -> float:
    """snap coordinates to the 1/32 ly grid"""
    val = float(val) * 32
    val += -0.5 if val < 0 else 0.5
    return int(val) / 32.0

def make_number(
        val: Any, default: int | float=0, convert_func: Callable[[Any], int | float]=int
) -> int | float:
    """convert value to a number (defaults to int)"""
    try:
        ret = convert_func(val)
    except (ValueError, TypeError):
        ret = default
    return ret

def table_exists(conn: sqlite3.Connection, tbl_name: str) -> bool:
    return bool(
        conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", tbl_name)
        ).fetchone()[0]
    )

def column_exists(conn: sqlite3.Connection, tbl_name: str, col_name: str) -> bool:
    return bool(
        conn.execute(
            "SELECT COUNT(*) FROM pragma_table_info(?) WHERE name = ?",
            (tbl_name, col_name)
        ).fetchone()[0]
    )

def database_is_new_schema(conn: sqlite3.Connection) -> bool:
    if all(table_exists(conn, tbl_name) for tbl_name in ("Added", "RareItem", "Upgrade")):
        return False
    return all(
        column_exists(conn, tbl_name, col_name)
        for tbl_name, col_name in (
            ("Item", "rare_station_id"),
            ("Station", "lookup_name"),
            ("System", "lookup_name"),
        )
    )

def get_field_names(data_class: dataclass) -> tuple[str]:
    return tuple(field.name.rstrip("_") for field in fields(data_class))

def convert_dict_to_class(data_class: dataclass, row: dict) -> dataclass:
    args = (
        field.type(row[field.name.rstrip("_")]) if row.get(field.name.rstrip("_")) else None
        for field in fields(data_class)
    )
    return data_class(*args)

def get_from_StationServices(service_list: Iterable[str], key: str):
    if service_list is None:
        return "?"
    return "Y" if key.upper() in service_list else "N"

def convert_entry_to_StationItem(
        station: Station | StationNew, item: Item | ItemNew, timestamp: str, entry: dict[str, Any]
) -> StationItem | StationItemNew | None:
    demand_price = make_number(entry["sellPrice"])
    demand_units = make_number(entry["demand"])
    demand_level = make_number(entry["demandBracket"])
    supply_price = make_number(entry["buyPrice"])
    supply_units = make_number(entry["stock"])
    supply_level = make_number(entry["stockBracket"])

    if supply_level and demand_level:
        # there should only be supply or demmand, save it anyway (ed bug)
        # reset level based on units
        if supply_units == 0:
            supply_level = 0
        if demand_units == 0:
            demand_level = 0

    if supply_level == 0:
        if demand_level == 0:
            # not on the market, just in ship cargo
            return None
        # If there is no stockBracket ignore supply
        supply_price = 0
        supply_units = 0
    elif demand_price == 0:
        # no price means you can not sell it
        demand_units = 0
        demand_level = 0
    else:
        # you can still sell it without demand
        demand_units = -1
        demand_level = -1

    if isinstance(station, StationNew):
        return StationItemNew(
            station.station_id, item.item_id, demand_price, demand_units, demand_level,
            supply_price, supply_units, supply_level, modified=timestamp, from_live=0
        )
    return StationItem(
        station.station_id, item.item_id, demand_price, demand_units, demand_level,
        supply_price, supply_units, supply_level, modified=timestamp, from_live=0
    )

def list_or_dict_iterator(data: dict[str, Any] | list[Any]) -> Iterable[Any]:
    if isinstance(data, dict):
        yield from data.values()
    elif isinstance(data, list):
        yield from data

def shipyard_iterator(data: dict[str, dict | list]) -> Iterable[dict]:
    if "shipyard_list" in data:
        yield from list_or_dict_iterator(data["shipyard_list"])
    if "unavailable_list" in data:
        yield from list_or_dict_iterator(data["unavailable_list"])

def construction_depot_iterator(data: dict[str, dict[str, dict] | list[dict]]) -> Iterable[tuple[str, dict]]:
    if "requiredConstructionResources" in data:
        yield from data["requiredConstructionResources"]["commodities"].items()
    if "ResourcesRequired" in data:
        # convert to the same format as the above
        for org_entry in data["ResourcesRequired"]:
            fdev_name = REGEX_NORMALIZE_NAME.match(org_entry["Name"]).group("name")
            entry = {
                "required": org_entry["RequiredAmount"],
                "provided": org_entry["ProvidedAmount"],
                "complete": org_entry["RequiredAmount"] == org_entry["ProvidedAmount"],
                "creditsPerUnit": org_entry["Payment"],
            }
            yield fdev_name, entry

def build_insert_stmt(tbl_name: str, columns: Iterable[str], replace: bool=False) -> str:
    return (
        f"{replace and 'REPLACE' or 'INSERT'}"
        f" INTO {tbl_name}({','.join(column.rstrip('_') for column in columns)})"
        f" VALUES({','.join('?'*len(columns))})"
    )

def build_update_stmt(tbl_name: str, columns: Iterable[str], *columns_id: str) -> str:
    return (
        f"UPDATE {tbl_name} SET {'=?,'.join(column.rstrip('_') for column in columns)}=?"
        f" WHERE {'=? AND '.join(columns_id)}=?"
    )

def insert_from_dict(
        tbl_name: str, ins_columns: dict[str, Any], replace: bool=False
) -> tuple[str, str | int | float | None]:
    columns, bind = zip(*[col_pair for col_pair in ins_columns.items()])
    stmt = build_insert_stmt(tbl_name, columns, replace=replace)
    return stmt, bind

def update_from_dict(
        tbl_name: str, upd_columns: dict[str, Any], **id_columns: Any
) -> tuple[str, str | int | float | None]:
    columns, bind = zip(*[col_pair for col_pair in upd_columns.items()])
    columns_id, bind_id = zip(*[col_pair for col_pair in id_columns.items()])
    bind += bind_id
    stmt = build_update_stmt(tbl_name, columns, *columns_id)
    return stmt, bind

# copy from original tradedangerous code: 'corrections.py'
# ---- Lookup-key normalisation ----
# Single source of truth for the normalisation applied to System and Station
# names when building the lookup_name schema column and when resolving partial
# names. It lives here -- a dependency-free, top-level module -- so every writer
# of those rows (the resolver, the CSV importer, the spansh upsert, and the
# external listener) computes the same key without pulling in DB/ORM machinery.
# Two-stage rule (mirrors the historical TradeDB.normalizeTrans / trimTrans):
#   stage 1 -- uppercase a-z, delete  [ ] ( ) * + - . , { } :
#   stage 2 -- delete space and apostrophe

# Stage 1: uppercase a-z, delete [ ] ( ) * + - . , { } :
_normalize_trans = str.maketrans(
    'abcdefghijklmnopqrstuvwxyz',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '[]()*+-.,{}:'
)
# Stage 2: delete space and apostrophe
_trim_trans = str.maketrans('', '', " '")


def normalize_str(s):
    """Return the two-stage normalised lookup key for *s*.

    Stage 1 uppercases and strips punctuation; stage 2 strips spaces and
    apostrophes. This is what populates System.lookup_name / Station.lookup_name
    and what partial-name candidate gathering compares against, so every
    producer of those rows must use this exact function.
    """
    return s.translate(_normalize_trans).translate(_trim_trans)
