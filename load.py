"""

Plugin for updating your local TradeDangerous database.

"""

import logging
import os
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog

import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from config import appname, config
from companion import CAPIData, SERVER_LIVE

from tradedb import TradeDB, import_standard_data, fill_RareItem_cache

PLUGIN_NAME = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

__version_info__ = (0, 3, 2)
__version__ = ".".join(map(str, __version_info__))

PLUGIN_URL = "https://github.com/bgol/UpdateTD"
PREFSNAME_DBFILENAME = "updatetd_dbfilename"
PREFSNAME_CREATE_ = "updatetd_create_"
PREFSNAME_USE_RAREITEM_CACHE = "updatetd_use_rareitem_cache"

class This:
    """Module global variables."""
    plugin_dir: str = None
    default_db_filename = "~/data/TradeDangerous.db"
    db_filename: str = None
    prefs_db_filename: tk.StringVar = None
    tradedb: TradeDB = None
    create_item: bool = True
    create_ship: bool = True
    create_module: bool = False
    use_rareitem_cache: bool = False
    prefs_create_item: tk.BooleanVar = None
    prefs_create_ship: tk.BooleanVar = None
    prefs_create_module: tk.BooleanVar = None
    prefs_use_rareitem_cache: tk.BooleanVar = None

    def __str__(self) -> str:
        return ("\n".join(line for line in ("",
            f"{self.plugin_dir = }",
            f"{self.default_db_filename = }",
            f"{self.db_filename = }",
            f"{self.tradedb = }",
            f"{self.create_item = }",
            f"{self.create_ship = }",
            f"{self.create_module = }",
            f"{self.use_rareitem_cache = }",
        )))

this = This()


def plugin_start3(plugin_dir: str) -> str:
    logger.info(f"{__version__ = }")

    this.plugin_dir = plugin_dir
    this.db_filename = config.get_str(PREFSNAME_DBFILENAME)
    this.create_item = config.get_bool(f"{PREFSNAME_CREATE_}item", default=True)
    this.create_ship = config.get_bool(f"{PREFSNAME_CREATE_}ship", default=True)
    this.create_module = config.get_bool(f"{PREFSNAME_CREATE_}module", default=False)
    this.use_rareitem_cache = config.get_bool(PREFSNAME_USE_RAREITEM_CACHE, default=False)
    this.prefs_db_filename = tk.StringVar(value = this.db_filename)
    this.prefs_create_item = tk.BooleanVar(value = this.create_item)
    this.prefs_create_ship = tk.BooleanVar(value = this.create_ship)
    this.prefs_create_module = tk.BooleanVar(value = this.create_module)
    this.prefs_use_rareitem_cache = tk.BooleanVar(value = this.use_rareitem_cache)
    this.tradedb = TradeDB(
        logger, this.db_filename, this.create_item,
        this.create_ship, this.create_module, this.use_rareitem_cache
    )
    fill_RareItem_cache(this.tradedb, this.plugin_dir)
    logger.debug(f"{this = !s}")

    return PLUGIN_NAME

def plugin_stop() -> None:
    this.tradedb.close()

def filedialog(parent: nb.Frame, title: str, pathvar: tk.StringVar) -> None:
    filename = tkinter.filedialog.askopenfilename(
        parent = parent,
        title = title,
        initialdir = os.path.dirname(this.db_filename or this.default_db_filename),
        initialfile = os.path.basename(this.db_filename or this.default_db_filename),
        filetypes = [
            ("SQLite database files", ("*.db", "*.sqlite", "*.db3")),
            ("All files", "*")
        ]
    )
    logger.info(f"selected {filename = !r}")
    if filename:
        pathvar.set(filename)

def import_data_button() -> None:
    db_filename = this.prefs_db_filename.get()
    this.tradedb.change_settings(db_filename, True, True, True, False)
    import_standard_data(this.tradedb, this.plugin_dir)
    this.tradedb.change_settings(
        this.db_filename, this.create_item, this.create_ship,
        this.create_module, this.use_rareitem_cache
    )

def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> tk.Frame:
    # EDMC defaults
    PADX, PADY = 5, 2
    this.prefs_db_filename.set(this.db_filename)

    frame = nb.Frame(parent)
    frame.columnconfigure(2, weight=1)

    HyperlinkLabel(
        frame, text="TradeDangerous DB-Update",
        background=nb.Label().cget("background"),
        url=PLUGIN_URL, underline=True
    ).grid(row=1, column=1, columnspan=2, padx=2*PADX, sticky=tk.W)
    nb.Label(frame, text = "Version %s" % __version__).grid(row=1, column=3, padx=PADX, sticky=tk.E)

    nb.Label(frame, text="Databasefile:").grid(row=2, column=1, padx=2*PADX, pady=(0, PADY), sticky=tk.W)
    db_entry = nb.EntryMenu(frame, takefocus=False, textvariable=this.prefs_db_filename)
    db_entry.grid(row=2, column=2, padx=PADX, pady=(0, PADY), sticky=tk.EW)
    db_entry['state'] = 'readonly'
    nb.Button(
        frame,
        text="Select...",
        command=lambda: filedialog(frame, "Databasefile", this.prefs_db_filename)
    ).grid(row=2, column=3, padx=PADX, pady=(0, PADY), sticky=tk.E)

    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=3, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=tk.EW)

    nb.Checkbutton(
        frame, text='Create unknown Item and Category', variable=this.prefs_create_item
    ).grid(row=4, column=2, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Checkbutton(
        frame, text='Create unknown Ship', variable=this.prefs_create_ship
    ).grid(row=5, column=2, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Checkbutton(
        frame, text='Create unknown Module', variable=this.prefs_create_module
    ).grid(row=6, column=2, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)

    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=7, column=2, padx=PADX, pady=PADY, sticky=tk.EW)

    nb.Checkbutton(
        frame, text='Use RareItem cache (insert known RareItems of a station when docking)',
        variable=this.prefs_use_rareitem_cache
    ).grid(row=8, column=2, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)

    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=9, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=tk.EW)

    nb.Button(
        frame, text="Import", command=import_data_button
    ).grid(row=10, column=1, padx=2*PADX, pady=(0, PADY), sticky=tk.E)
    nb.Label(
        frame, text="Import standard values for Categories, Items, Ships and Upgrades"
    ).grid(row=10, column=2, padx=PADX, pady=(0, PADY), sticky=tk.W)

    return frame

def prefs_changed(cmdr: str, is_beta: bool) -> None:
    this.db_filename = this.prefs_db_filename.get()
    this.create_item = this.prefs_create_item.get()
    this.create_ship = this.prefs_create_ship.get()
    this.create_module = this.prefs_create_module.get()
    this.use_rareitem_cache = this.prefs_use_rareitem_cache.get()
    config.set(PREFSNAME_DBFILENAME, this.db_filename)
    config.set(f"{PREFSNAME_CREATE_}item", this.create_item)
    config.set(f"{PREFSNAME_CREATE_}ship", this.create_ship)
    config.set(f"{PREFSNAME_CREATE_}module", this.create_module)
    config.set(PREFSNAME_USE_RAREITEM_CACHE, this.use_rareitem_cache)
    this.tradedb.change_settings(
        this.db_filename, this.create_item, this.create_ship,
        this.create_module, this.use_rareitem_cache
    )
    fill_RareItem_cache(this.tradedb, this.plugin_dir)
    logger.debug(f"{this = !s}")

def journal_entry(
    cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict
) -> None:
    if is_beta:
        logger.info("Beta game ignored.")
        return

    if not this.tradedb.is_connected:
        logger.info("Database not connected.")
        return

    if entry["event"] in {"FSDJump", "Location", "CarrierJump"}:
        logger.info("Check system data from Jump / Location.")
        this.tradedb.update_system(entry, cmdrname)

    if entry["event"] == "NavRoute":
        logger.info("Check system data from NavRoute.")
        for route in entry.get("Route", []):
            this.tradedb.update_system({"timestamp": entry["timestamp"], **route}, cmdrname)

    if entry["event"] == "Docked":
        logger.info("Check station data.")
        this.tradedb.update_station(entry)

def cmdr_data(data: CAPIData, is_beta: bool) -> None:
    """
    We have new data on our commander
    """
    if is_beta:
        logger.info("Beta game ignored.")
        return

    if not this.tradedb.is_connected:
        logger.info("Database not connected.")
        return

    if data.source_host == SERVER_LIVE and "lastStarport" in data:
        logger.info("Update starport data.")
        this.tradedb.update_market(data["lastStarport"])
        this.tradedb.update_shipyard(data["lastStarport"])
        this.tradedb.update_outfitting(data["lastStarport"])
