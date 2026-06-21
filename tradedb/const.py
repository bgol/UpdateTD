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

STATION_TYPE_MAP_NEW = {
    "ASTEROIDBASE": 1,
    "CORIOLIS": 2,
    "DOCKABLEPLANETSTATION": 3,
    "DODEC": 4,
    "FLEETCARRIER": 5,
    "MEGASHIP": 6,
    "OCELLUS": 7,
    "BERNAL": 7,
    "ORBIS": 8,
    "OUTPOST": 9,
    "PLANETARYCONSTRUCTIONDEPOT": 10,
    "CRATEROUTPOST": 11,
    "CRATERPORT": 12,
    "ONFOOTSETTLEMENT": 13,
    "SPACECONSTRUCTIONDEPOT": 14,
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

STRONGHOLDCARRIER_REGEX = re.compile(r"(\$ShipName_StrongholdCarrier|Hochburg-Carrier|Portanaves bastión|Porte-vaisseaux de forteresse|Transportadora da potência|Носитель-база)", re.IGNORECASE)
STRONGHOLDCARRIER_NAME = "Stronghold Carrier"

COLONISATIONSHIP_REGEX = re.compile(r"\$EXT_PANEL_ColonisationShip", re.IGNORECASE)
COLONISATIONSHIP_NAME = "System Colonisation Ship"

REGEX_NORMALIZE_NAME = re.compile(r"^(\$)?(?P<name>.*?)(_name;)?$", re.IGNORECASE)
