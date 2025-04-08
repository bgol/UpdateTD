"""
    Some constants needed to enhance data
"""
import re


PLANETARY_STATION_TYPES = {
    "CRATERPORT",
    "CRATEROUTPOST",
    "ONFOOTSETTLEMENT",
    "PLANETARYCONSTRUCTIONDEPOT",
}

STATION_TYPE_MAP = {
    "OUTPOST": 1,
    "CORIOLIS": 2,
    "OCELLUS": 3,
    "BERNAL": 3,
    "ORBIS": 4,
    "CRATEROUTPOST": 11,
    "CRATERPORT": 12,
    "MEGASHIP": 13,
    "ASTEROIDBASE": 14,
    "FLEETCARRIER": 24,
    "ONFOOTSETTLEMENT": 25,
}

PADSIZE_BY_STATION_TYPE = {
    "OUTPOST": "M",
    "ASTEROIDBASE": "L",
    "BERNAL": "L",
    "CORIOLIS": "L",
    "CRATEROUTPOST": "L",
    "CRATERPORT": "L",
    "FLEETCARRIER": "L",
    "MEGASHIP": "L",
    "OCELLUS": "L",
    "ORBIS": "L",
    "PLANETARYCONSTRUCTIONDEPOT": "L",
    "SPACECONSTRUCTIONDEPOT": "L",
}

# Categories to ignore. Drones end up here.
IGNORE_CATEGORY = {
    None,
    "NonMarketable",
}

STRONGHOLDCARRIER_REGEX = re.compile(r"($ShipName_StrongholdCarrier|Hochburg-Carrier|Portanaves bastión|Porte-vaisseaux de forteresse|Transportadora da potência|Носитель-база)", re.IGNORECASE)
STRONGHOLDCARRIER_NAME = "Stronghold Carrier"

COLONISATIONSHIP_REGEX = re.compile(r"\$EXT_PANEL_ColonisationShip", re.IGNORECASE)
COLONISATIONSHIP_NAME = "System Colonisation Ship"
