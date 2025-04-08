"""

Plugin for updating your local TradeDangerous database.

"""

import logging
import os
import tkinter as tk
import tkinter.filedialog

import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from config import appname, config
from companion import CAPIData, SERVER_LIVE

from tradedb import TradeDB

PLUGIN_NAME = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

__version_info__ = (0, 1, 0)
__version__ = ".".join(map(str, __version_info__))

PLUGIN_URL = "https://github.com/bgol/UpdateTD"
PREFSNAME_DBFILENAME = "updatetd_dbfilename"

class This:
    """Module global variables."""
    default_db_filename = "~/data/TradeDangerous.db"
    db_filename: str = None
    prefs_db_filename: tk.StringVar = None
    tradedb: TradeDB = None

this = This()


def plugin_start3(plugin_dir: str) -> str:
    logger.info(f"{__version__ = }")

    this.db_filename = config.get_str(PREFSNAME_DBFILENAME)
    this.prefs_db_filename = tk.StringVar(value = this.db_filename)
    this.tradedb = TradeDB(logger, this.db_filename)

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

    return frame

def prefs_changed(cmdr: str, is_beta: bool) -> None:
   this.db_filename = this.prefs_db_filename.get()
   config.set(PREFSNAME_DBFILENAME, this.db_filename)
   this.tradedb.change_db_filename(this.db_filename)

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
        this.tradedb.update_system(entry, cmdrname)

    if entry["event"] == "NavRoute":
        for route in entry["Route"]:
            this.tradedb.update_system({"timestamp": entry["timestamp"], **route}, cmdrname)

    if entry["event"] == "Docked":
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
        this.tradedb.update_market(data["lastStarport"])
        this.tradedb.update_shipyard(data["lastStarport"])
        this.tradedb.update_outfitting(data["lastStarport"])
