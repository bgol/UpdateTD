"""
   auto generated on 2026-06-21T11:01:30Z
   database file: tools/TradeDangerous.db
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).replace(microsecond = 0)

def CURRENT_TIME():
    return now().time().isoformat()

def CURRENT_DATE():
    return now().date().isoformat()

def CURRENT_TIMESTAMP():
    return now().isoformat(sep = " ")


@dataclass(frozen=True)
class CategoryNew:
    """TradeDangerous "Category" table"""
    category_id: int
    name: str = None

@dataclass(frozen=True)
class FDevShipyardNew:
    """TradeDangerous "FDevShipyard" table"""
    id: int
    symbol: str = None
    name: str = None
    entitlement: str = None

@dataclass(frozen=True)
class ItemNew:
    """TradeDangerous "Item" table"""
    item_id: int
    name: str = None
    category_id: int = None
    ui_order: int = 0
    avg_price: int = None
    fdev_id: int = None
    rare_station_id: int = None

@dataclass(frozen=True)
class ShipNew:
    """TradeDangerous "Ship" table"""
    ship_id: int
    name: str = None
    cost: int = None

@dataclass(frozen=True)
class ShipVendorNew:
    """TradeDangerous "ShipVendor" table"""
    ship_id: int
    station_id: int
    modified: str = field(default_factory = CURRENT_TIMESTAMP)

@dataclass(frozen=True)
class StationNew:
    """TradeDangerous "Station" table"""
    station_id: int
    name: str = None
    lookup_name: str = None
    system_id: int = None
    ls_from_star: int = 0
    blackmarket: str = '?'
    max_pad_size: str = '?'
    market: str = '?'
    shipyard: str = '?'
    modified: str = field(default_factory = CURRENT_TIMESTAMP)
    outfitting: str = '?'
    rearm: str = '?'
    refuel: str = '?'
    repair: str = '?'
    planetary: str = '?'
    type_id: int = 0

@dataclass(frozen=True)
class StationItemNew:
    """TradeDangerous "StationItem" table"""
    station_id: int
    item_id: int
    demand_price: int
    demand_units: int
    demand_level: int
    supply_price: int
    supply_units: int
    supply_level: int
    modified: str = field(default_factory = CURRENT_TIMESTAMP)
    from_live: int = 0

@dataclass(frozen=True)
class SystemNew:
    """TradeDangerous "System" table"""
    system_id: int
    name: str = None
    lookup_name: str = None
    pos_x: float = None
    pos_y: float = None
    pos_z: float = None
    modified: str = field(default_factory = CURRENT_TIMESTAMP)
