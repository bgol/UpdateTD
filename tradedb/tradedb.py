import logging
import time
import sqlite3
import os.path

from typing import Self, Any
from collections.abc import Iterable
from datetime import datetime
from dataclasses import asdict, astuple

from companion import CAPIData
from edmc_data import companion_category_map, ship_name_map


from .misc import (
    snap_to_grid, update_from_dict, insert_from_dict, get_from_StationServices, make_number,
    build_insert_stmt, get_field_names, shipyard_iterator, convert_entry_to_StationItem,
    list_or_dict_iterator,
)
from .const import (
    PLANETARY_STATION_TYPES, STATION_TYPE_MAP, PADSIZE_BY_STATION_TYPE,
    STRONGHOLDCARRIER_NAME, STRONGHOLDCARRIER_REGEX, COLONISATIONSHIP_NAME, COLONISATIONSHIP_REGEX
)
from .tables import Added, Category, Item, Ship, Upgrade, Station, System, RareItem
from .tables import StationItem, ShipVendor, UpgradeVendor

class TradeDB:
    """Database class for interaction."""

    timestamp: str = None

    added_by_name: dict[str, Added] = {}
    category_by_name: dict[str, Category] = {}
    category_by_id: dict[int, Category] = {}
    item_by_id: dict[int, Item] = {}
    rareitem_by_id: dict[int, RareItem] = {}
    rareitem_cache: dict[int, list[RareItem]] = {}
    ship_by_id: dict[int, Ship] = {}
    upgrade_by_id: dict[int, Upgrade] = {}

    system_by_id: dict[int, System] = {}
    station_by_id: dict[int, Station] = {}

    def __init__(
        self: Self, logger: logging.Logger, db_filename: str, create_item: bool = True,
        create_ship: bool = True, create_module: bool = True, use_rareitem_cache: bool = False
    ):
        self.logger = logger
        self.db_filename = db_filename
        self.conn = None
        self.reorder_item = False
        self.create_item = create_item
        self.create_ship = create_ship
        self.create_module = create_module
        self.use_rareitem_cache = use_rareitem_cache
        self.connect()
        self.load()

    @property
    def is_connected(self: Self) -> bool:
        return bool(self.conn)

    def get_db(self: Self) -> sqlite3.Connection:
        if self.conn:
            return self.conn

        self.logger.info(f"Connect to DB: {self.db_filename = !r}")
        conn = sqlite3.connect(self.db_filename)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA journal_mode=WAL")

        # SQLite does only ASCII upper/lower, replace them
        conn.create_function("upper", 1, str.upper)
        conn.create_function("lower", 1, str.lower)

        return conn

    def close(self: Self) -> None:
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed.")
        self.conn = None

    def connect(self: Self) -> None:
        self.close()
        if not self.db_filename:
            self.logger.info("No databasefile configured.")
            return
        if not os.path.isfile(self.db_filename):
            self.logger.error(f"{self.db_filename!r}: not a file.")
            return

        self.conn = self.get_db()

    def execute(self: Self, stmt: str, bind: Iterable|None=None, many=False) -> sqlite3.Cursor:
        conn = self.get_db()
        curs = conn.cursor()
        time_ms = time.perf_counter()*-1000
        if many:
            ret = curs.executemany(stmt, bind)
        else:
            ret = curs.execute(stmt, bind or ())
        conn.commit()
        time_ms += time.perf_counter()*1000
        self.logger.debug(f"{time_ms}: {stmt} ({bind})")
        return ret

    def change_settings(
        self: Self, db_filename: str, create_item: bool = True,
        create_ship: bool = True, create_module: bool = True,
        use_rareitem_cache: bool = False
    ) -> None:
        self.create_item = create_item
        self.create_ship = create_ship
        self.create_module = create_module
        self.use_rareitem_cache = use_rareitem_cache
        if db_filename != self.db_filename:
            self.db_filename = db_filename
            self.logger.info(f"new DB filename: {self.db_filename = !r}")
            self.connect()
            self.load()

    def load(self: Self) -> None:
        if not self.is_connected:
            return

        self._load_Added()
        self._load_Category()
        self._load_Item()
        self._load_RareItem()
        self._load_Ship()
        self._load_Upgrade()

    def _load_Added(self: Self) -> None:
        self.added_by_name.clear()
        columns = ",".join(get_field_names(Added))
        for row in self.execute(f"SELECT {columns} FROM Added"):
            added = Added(*row)
            self.added_by_name[added.name.upper()] = added
        self.logger.debug(f"Added: {self.added_by_name}")

    def _load_Category(self: Self) -> None:
        self.category_by_name.clear()
        columns = ",".join(get_field_names(Category))
        for row in self.execute(f"SELECT {columns} FROM Category"):
            category = Category(*row)
            self.category_by_name[category.name.upper()] = category
            self.category_by_id[category.category_id] = category
        self.logger.debug(f"Category: {self.category_by_name}")

    def _load_Item(self: Self) -> None:
        self.item_by_id.clear()
        columns = ",".join(get_field_names(Item))
        for row in self.execute(f"SELECT {columns} FROM Item"):
            item = Item(*row)
            self.item_by_id[item.item_id] = item
        self.logger.debug(f"Item: {self.item_by_id}")

    def _load_RareItem(self: Self) -> None:
        self.rareitem_by_id.clear()
        self.rareitem_cache.clear()
        columns = ",".join(get_field_names(RareItem))
        for row in self.execute(f"SELECT {columns} FROM RareItem"):
            rareitem = RareItem(*row)
            self.rareitem_by_id[rareitem.rare_id] = rareitem
        self.logger.debug(f"RareItem: {self.rareitem_by_id}")

    def _load_Ship(self: Self) -> None:
        self.ship_by_id.clear()
        columns = ",".join(get_field_names(Ship))
        for row in self.execute(f"SELECT {columns} FROM Ship"):
            ship = Ship(*row)
            self.ship_by_id[ship.ship_id] = ship
        self.logger.debug(f"Ship: {self.ship_by_id}")

    def _load_Upgrade(self: Self) -> None:
        self.upgrade_by_id.clear()
        columns = ",".join(get_field_names(Upgrade))
        for row in self.execute(f"SELECT {columns} FROM Upgrade"):
            upgrade = Upgrade(*row)
            self.upgrade_by_id[upgrade.upgrade_id] = upgrade
        self.logger.debug(f"Upgrade: {self.upgrade_by_id}")

    def get_Added(self: Self, name: str) -> Added:
        if not (added := self.added_by_name.get(name.upper())):
            added = Added(self.execute("INSERT INTO Added(name) VALUES(?)", (name,)).lastrowid, name)
            self.added_by_name[added.name.upper()] = added
            self.logger.info(f"created {added = }")
        return added

    def get_Category(self: Self, name: str) -> Category | None:
        if not (name := companion_category_map.get(name, name)):
            return None
        if not (category := self.category_by_name.get(name.upper())) and self.create_item:
            category = Category(self.execute("INSERT INTO Category(name) VALUES(?)", (name,)).lastrowid, name)
            self.category_by_name[category.name.upper()] = category
            self.category_by_id[category.category_id] = category
            self.logger.info(f"created {category = }")
            self.reorder_item = True
        return category

    def get_Item(self: Self, item_id: int) -> Item | None:
        return self.item_by_id.get(item_id)

    def get_RareItem(self: Self, rare_id: int) -> RareItem | None:
        return self.rareitem_by_id.get(rare_id)

    def get_Ship(self: Self, ship_id: int) -> Ship | None:
        return self.ship_by_id.get(ship_id)

    def get_Upgrade(self: Self, upgrade_id: int) -> Upgrade | None:
        return self.upgrade_by_id.get(upgrade_id)

    def get_System(self: Self, address: int) -> System | None:
        if not (system := self.system_by_id.get(address)):
            columns = ",".join(get_field_names(System))
            if row := self.execute(f"SELECT {columns} FROM System WHERE system_id = ?", (address,)).fetchone():
                system = System(*row)
                self.system_by_id[address] = system
        self.logger.debug(f"get_System({address = }) -> {system = }")
        return system

    def get_Station(self: Self, market_id: int) -> Station | None:
        if not (station := self.station_by_id.get(market_id)):
            columns = ",".join(get_field_names(Station))
            if row := self.execute(f"SELECT {columns} FROM Station WHERE station_id = ?", (market_id,)).fetchone():
                station = Station(*row)
                self.station_by_id[market_id] = station
        self.logger.debug(f"get_Station({market_id = }) -> {station = }")
        return station

    def make_Item(self: Self, entry: dict) -> Item | None:
        if self.get_RareItem(entry["id"]) is not None:
            return None
        if not (item := self.get_Item(entry["id"])) and self.create_item:
            item = Item(
                item_id = entry["id"],
                name = entry["locName"],
                category_id = self.get_Category(entry["categoryname"]).category_id,
                ui_order = 0,
                avg_price = make_number(entry["meanPrice"]),
                fdev_id = entry["id"],
            )
            stmt, bind = insert_from_dict("Item", asdict(item))
            self.execute(stmt, bind)
            self.item_by_id[item.item_id] = item
            self.logger.info(f"created {item = }")
            self.reorder_item = True
        return item

    def make_Upgrade(self: Self, entry: dict) -> Upgrade | None:
        if not (upgrade := self.get_Upgrade(entry["id"])) and self.create_module:
            upgrade = Upgrade(
                upgrade_id = entry["id"],
                name = entry["name"],
                class_ = "?",
                rating = "?",
            )
            stmt, bind = insert_from_dict("Upgrade", asdict(upgrade))
            self.execute(stmt, bind)
            self.upgrade_by_id[upgrade.upgrade_id] = upgrade
            self.logger.info(f"created {upgrade = }")
        return upgrade

    def make_Ship(self: Self, entry: dict) -> Ship | None:
        if not (ship := self.get_Ship(entry["id"])) and self.create_ship:
            ship = Ship(
                ship_id = entry["id"],
                name = ship_name_map.get(entry["name"].lower(), entry["name"]),
                cost = make_number(entry["basevalue"]),
            )
            stmt, bind = insert_from_dict("Ship", asdict(ship))
            self.execute(stmt, bind)
            self.ship_by_id[ship.ship_id] = ship
            self.logger.info(f"created {ship = }")
        return ship

    def check_for_rareitems(self: Self, station_id: int) -> None:
        if not self.use_rareitem_cache:
            return

        for rareitem in self.rareitem_cache.pop(station_id, []):
            if rareitem.rare_id in self.rareitem_by_id:
                continue
            stmt, bind = insert_from_dict("RareItem", asdict(rareitem))
            self.execute(stmt, bind)
            self.rareitem_by_id[rareitem.rare_id] = rareitem
            self.logger.info(f"created {rareitem = }")

    def update_item_ui_order(self: Self) -> None:
        if not (self.reorder_item and self.create_item):
            return

        for category in {self.category_by_id[item.category_id] for item in self.item_by_id.values()}:
            for i, item in enumerate(sorted(
                (item for item in self.item_by_id.values() if item.category_id == category.category_id),
                key = lambda x: x.name.upper()
            ), start = 1):
                if item.ui_order == i:
                    continue
                self.execute("UPDATE Item SET ui_order=? WHERE item_id=?", (i, item.item_id))

        self.reorder_item = False

    def update_entry(self: Self, tbl_name: str, old_entry: Any, new_entry: Any, **id_columns) -> None:
        if old_entry == new_entry:
            info_text = "up-to-date"
        else:
            if old_entry is None:
                info_text = "created"
                stmt, bind = insert_from_dict(tbl_name, asdict(new_entry))
            else:
                info_text = "updated"
                upd_columns = {}
                for col_name, old_value in asdict(old_entry).items():
                    new_value = getattr(new_entry, col_name)
                    if new_value != old_value:
                        upd_columns[col_name] = new_value
                upd_columns["modified"] = self.timestamp
                stmt, bind = update_from_dict(tbl_name, upd_columns, **id_columns)
            self.execute(stmt, bind)
            if tbl_name == "System":
                self.system_by_id[new_entry.system_id] = self.get_System(new_entry.system_id)
            elif tbl_name == "Station":
                self.station_by_id[new_entry.station_id] = self.get_Station(new_entry.station_id)
        self.logger.info(f"{info_text} {tbl_name} {new_entry.name!r}")

    def update_system(self: Self, entry: dict, cmdrname: str) -> None:
        self.timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        old_system = self.get_System(entry["SystemAddress"])
        new_system = System(
            system_id = entry["SystemAddress"],
            name = entry.get("StarSystem", entry.get("SystemName", entry.get("System"))),
            pos_x = snap_to_grid(entry["StarPos"][0]),
            pos_y = snap_to_grid(entry["StarPos"][1]),
            pos_z = snap_to_grid(entry["StarPos"][2]),
            added_id = old_system.added_id if old_system else self.get_Added(cmdrname).added_id,
            modified = old_system.modified if old_system else self.timestamp,
        )
        self.update_entry("System", old_system, new_system, system_id=new_system.system_id)

    def update_station(self, entry: dict) -> None:
        if not (system := self.get_System(entry["SystemAddress"])):
            self.logger.info(f"update_station(): System {entry['SystemAddress']} not found")
            return

        self.timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        service_set = {service.upper() for service in entry.get("StationServices", [])}
        stn_type: str = entry.get("StationType", "")

        landing_pads = entry.get("LandingPads", {})
        if landing_pads.get("Large", 0) > 0:
            max_pad_size = "L"
        elif landing_pads.get("Medium", 0) > 0:
            max_pad_size = "M"
        elif landing_pads.get("Small", 0) > 0:
            max_pad_size = "S"
        else:
            max_pad_size = PADSIZE_BY_STATION_TYPE.get(stn_type.upper(), "?")
        if stn_type.upper().endswith("CONSTRUCTIONDEPOT"):
            # Elite bug: Some construction sites report wrong pad sizes.
            max_pad_size = "L"

        stn_name = entry["StationName"]
        # Elite bug: Some station names are localised
        if COLONISATIONSHIP_REGEX.match(stn_name):
            stn_name = COLONISATIONSHIP_NAME
        elif STRONGHOLDCARRIER_REGEX.match(stn_name):
            stn_name = STRONGHOLDCARRIER_NAME

        old_station = self.get_Station(entry["MarketID"])
        new_station = Station(
            station_id = entry["MarketID"],
            name = stn_name,
            system_id = system.system_id,
            ls_from_star = round(entry.get("DistFromStarLS", 0)),
            blackmarket = get_from_StationServices(service_set, "BlackMarket"),
            max_pad_size = max_pad_size,
            market = get_from_StationServices(service_set, "Commodities"),
            shipyard = get_from_StationServices(service_set, "Shipyard"),
            modified = old_station.modified if old_station else self.timestamp,
            outfitting = get_from_StationServices(service_set, "Outfitting"),
            rearm = get_from_StationServices(service_set, "Rearm"),
            refuel = get_from_StationServices(service_set, "Refuel"),
            repair = get_from_StationServices(service_set, "Repair"),
            planetary = "Y" if stn_type.upper() in PLANETARY_STATION_TYPES else "N",
            type_id = STATION_TYPE_MAP.get(stn_type.upper(), 0),
        )
        self.update_entry("Station", old_station, new_station, station_id=new_station.station_id)
        self.check_for_rareitems(new_station.station_id)

    def update_market(self, data: dict) -> None:
        if "commodities" not in data:
            self.logger.info("no market data")
            return
        if not (station := self.get_Station(data["id"])):
            self.logger.info(f"station not in database, market id: {data['id']}")
            return
        self.check_for_rareitems(station.station_id)

        self.timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        self.reorder_item = False
        item_list = []
        for entry in data["commodities"]:
            check_name = entry.get("categoryname")
            if not companion_category_map.get(check_name, check_name):
                continue
            if self.get_RareItem(entry["id"]) is not None:
                self.logger.debug(f"ignore rareitem: {entry['id']} - {entry['name']}")
                continue
            if not (item := self.make_Item(entry)):
                self.logger.warning(f"unknown item: {entry['id']} - {entry['name']}")
                continue
            if stn_item := convert_entry_to_StationItem(station, item, self.timestamp, entry):
                item_list.append(astuple(stn_item))

        self.execute("DELETE FROM StationItem WHERE station_id = ?", (station.station_id,))
        if item_list:
            stmt = build_insert_stmt("StationItem", get_field_names(StationItem))
            self.execute(stmt, item_list, many=True)
        list_len = len(item_list)
        self.logger.info(f"market updated ({list_len} item{'' if list_len == 1 else 's'})")

        self.update_item_ui_order()

    def update_shipyard(self, data: CAPIData) -> None:
        if "ships" not in data:
            self.logger.info("no shipyard data")
            return
        if not (station := self.get_Station(data["id"])):
            self.logger.info(f"station not in database, market id: {data['id']}")
            return

        self.timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        ship_list = []
        for entry in shipyard_iterator(data["ships"]):
            if not (ship := self.make_Ship(entry)):
                self.logger.warning(f"unknown ship: {entry['id']} - {entry['name']}")
                continue
            ship_list.append(astuple(ShipVendor(
                ship_id = ship.ship_id,
                station_id = station.station_id,
                modified = self.timestamp,
            )))

        self.execute("DELETE FROM ShipVendor WHERE station_id = ?", (station.station_id,))
        if ship_list:
            stmt = build_insert_stmt("ShipVendor", get_field_names(ShipVendor))
            self.execute(stmt, ship_list, many=True)
        list_len = len(ship_list)
        self.logger.info(f"shipyard updated ({list_len} ship{'' if list_len == 1 else 's'})")

    def update_outfitting(self, data: CAPIData) -> None:
        if "modules" not in data:
            self.logger.info("no outfitting data")
            return
        if not (station := self.get_Station(data["id"])):
            self.logger.info(f"station not in database, market id: {data['id']}")
            return

        self.timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        module_list = []
        for entry in list_or_dict_iterator(data["modules"]):
            if not (module := self.make_Upgrade(entry)):
                self.logger.warning(f"unknown module: {entry['id']} - {entry['name']}")
                continue
            module_list.append(astuple(UpgradeVendor(
                upgrade_id = module.upgrade_id,
                station_id = station.station_id,
                modified = self.timestamp,
            )))

        self.execute("DELETE FROM UpgradeVendor WHERE station_id = ?", (station.station_id,))
        if module_list:
            stmt = build_insert_stmt("UpgradeVendor", get_field_names(UpgradeVendor))
            self.execute(stmt, module_list, many=True)
        list_len = len(module_list)
        self.logger.info(f"outfitting updated ({list_len} module{'' if list_len == 1 else 's'})")
