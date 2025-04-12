# TradeDangerous DB-Update plugin for [EDMC](https://github.com/EDCD/EDMarketConnector/wiki)

This plugin will update the database of [TradeDangerous](https://github.com/eyeonus/Trade-Dangerous) directly while playing the game. No export / import needed anymore.

## Installation

* On EDMC's Plugins settings tab press the “Open” button. This reveals the `plugins` folder where EDMC looks for plugins.
* Download the [latest release](https://github.com/bgol/UpdateTD/releases/latest).
* Open the `.zip` archive that you downloaded and move the `UpdateTD` folder contained inside into the `plugins` folder.

You will need to re-start EDMC for it to notice the new plugin.

## Settings

* Databasefile: The TradeDangerous database file
  - `~/data/TradeDangerous.db` (default suggestion)
* Create unknown Item and Category (default: True)
* Create unknown Ship (default: True)
* Create unknown Module (default: False)
* Use RareItem cache (insert known RareItems of a station when docking, default: False)
* Import button: Import standard values for Categories, Items, Ships and Upgrades

## License

Copyright © 2025 Bernd Gollesch.

Licensed under the [MIT License](LICENSE.md).
