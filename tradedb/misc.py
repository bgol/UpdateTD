from typing import Any
from collections.abc import Iterable, Callable
from dataclasses import dataclass, fields

from .const import REGEX_NORMALIZE_NAME
from .tables import Station, Item, StationItem


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
        station: Station, item: Item, timestamp: str, entry: dict[str, Any]
) -> StationItem | None:
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
        # If there is no stockBracket ignore supply
        supply_price = 0
        supply_units = 0
    else:
        # otherwise don't care about demand
        demand_units = 0
        demand_level = 0

    if supply_level == 0 and demand_level == 0:
        # not on the market, just in ship cargo
        return None

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
