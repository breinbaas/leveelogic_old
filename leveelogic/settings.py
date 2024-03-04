DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT = 0.1
DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO = 1e9

# this will be the name for soil codes that cannot be translated
# using the _params_from_name function in borehole_collection
# only used for Dutch soilnames in boreholes
UNHANDLED_SOILCODE_NAME = "unknown"

# Unit weight for water
UNIT_WEIGHT_WATER = 9.81

# Max Qc and FR for plots
CPT_QC_MAX = 20.0
CPT_FR_MAX = 10.0

# URLs
BRO_CPT_DOWNLOAD_URL = "https://publiek.broservices.nl/sr/cpt/v1/objects"
BRO_CPT_CHARACTERISTICS_URL = (
    f"https://publiek.broservices.nl/sr/cpt/v1/characteristics/searches"
)

# soil code translation dictionaries
nen5104_main_soilname_dict = {
    "G": "grind",
    "Z": "zand",
    "L": "leem",
    "K": "klei",
    "V": "veen",
}

nen5104_addition_names_dict = {
    "g": "grindig",
    "s": "siltig",
    "k": "kleiig",
    "h": "humeus",
    "z": "zandig",
}

nen5104_addition_amount_dict = {"1": "zwak", "2": "matig", "3": "sterk", "4": "uiterst"}

nen5104_sand_dict = {
    "ZUF": "uiterst fijn",
    "ZZF": "zeer fijn",
    "ZMF": "matig fijn",
    "ZMG": "matig grof",
    "ZZG": "zeer grof",
    "ZUG": "uiterst grof",
}

nen5104_main_soilcolor_dict = {
    "G": "#9198a3",
    "Z": "#f2fc2d",
    "K": "#25c435",
    "V": "#d3a328",
    "L": "#5b440b",
}

nen5104_sand_color_dict = {
    "ZZF": "#f9f984",
    "ZUF": "#f9f984",
    "ZF": "#f2f26d",
    "ZMF": "#f9f954",
    "ZM": "#f9f954",
    "ZMG": "#fcfc3c",
    "ZG": "#fcfc1e",
    "ZZG": "#fcfc1e",
    "ZUG": "#fcfc1e",
}

nen5104_addition_color_dict = {
    "h": "#ef9b13",
    "s": "#b7d142",
    "z": "#f7ff26",
    "k": "#3be23d",
    "g": "#acc1bf",
}
