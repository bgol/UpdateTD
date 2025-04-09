from typing import Any
from collections.abc import Iterable, Callable
from dataclasses import dataclass, fields


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

def get_from_StationServices(service_list: Iterable[str], key: str):
    if service_list is None:
        return "?"
    return "Y" if key.upper() in service_list else "N"

def shipyard_iterator(data: dict[str, dict | list]) -> Iterable[dict]:
    if "shipyard_list" in data:
        yield from data["shipyard_list"].values()
    if "unavailable_list" in data:
        yield from data["unavailable_list"]

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
