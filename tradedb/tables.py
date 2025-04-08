"""
   auto generated on 2025-04-07T13:31:40Z
   database file: TradeDangerous.db
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
class Added:
    """TradeDangerous "Added" table"""
    added_id: int
    name: str = None

@dataclass(frozen=True)
class Category:
    """TradeDangerous "Category" table"""
    category_id: int
    name: str = None

@dataclass(frozen=True)
class FDevOutfitting:
    """TradeDangerous "FDevOutfitting" table"""
    id: int
    symbol: str = None
    category: str = None
    name: str = None
    mount: str = None
    guidance: str = None
    ship: str = None
    class_: str = None
    rating: str = None
    entitlement: str = None

@dataclass(frozen=True)
class FDevShipyard:
    """TradeDangerous "FDevShipyard" table"""
    id: int
    symbol: str = None
    name: str = None
    entitlement: str = None

@dataclass(frozen=True)
class Item:
    """TradeDangerous "Item" table"""
    item_id: int
    name: str = None
    category_id: int = None
    ui_order: int = 0
    avg_price: int = None
    fdev_id: int = None

@dataclass(frozen=True)
class RareItem:
    """TradeDangerous "RareItem" table"""
    rare_id: int
    station_id: int
    category_id: int
    name: str = None
    cost: int = None
    max_allocation: int = None
    illegal: str = '?'
    suppressed: str = '?'

@dataclass(frozen=True)
class Ship:
    """TradeDangerous "Ship" table"""
    ship_id: int
    name: str = None
    cost: int = None

@dataclass(frozen=True)
class ShipVendor:
    """TradeDangerous "ShipVendor" table"""
    ship_id: int
    station_id: int
    modified: str = field(default_factory = CURRENT_TIMESTAMP)

@dataclass(frozen=True)
class Station:
    """TradeDangerous "Station" table"""
    station_id: int
    name: str = None
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
class StationDemand:
    """TradeDangerous "StationDemand" table"""
    station_id: int
    item_id: int
    price: int
    units: int
    level: int
    modified: int
    from_live: int = 0

@dataclass(frozen=True)
class StationItem:
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
class StationSupply:
    """TradeDangerous "StationSupply" table"""
    station_id: int
    item_id: int
    price: int
    units: int
    level: int
    modified: int
    from_live: int = 0

@dataclass(frozen=True)
class System:
    """TradeDangerous "System" table"""
    system_id: int
    name: str = None
    pos_x: float = None
    pos_y: float = None
    pos_z: float = None
    added_id: int = None
    modified: str = field(default_factory = CURRENT_TIMESTAMP)

@dataclass(frozen=True)
class Upgrade:
    """TradeDangerous "Upgrade" table"""
    upgrade_id: int
    name: str = None
    class_: str = None
    rating: str = None
    ship: str = None

@dataclass(frozen=True)
class UpgradeVendor:
    """TradeDangerous "UpgradeVendor" table"""
    upgrade_id: int
    station_id: int
    modified: str
