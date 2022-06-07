# Font
FONT = {
    "family": "Latin Modern Sans, Helvetica, Arial",
    "weight": "normal",
    "size": 8
}

# Latex format helpers (converted from cm to inches)
# Actual text-width: 15.55493cm
# Actual text-height: 22.33209cm
TEXTWIDTH = 1/2.54 * 15.55493 * .97
TEXTHEIGHT = 1/2.54 * 22.33209 * 0.93
TEXTHEIGHT_SMALL = 1/2.54 * 22.33209 * 0.86

# Colors (derived from the MaterialDesign color palette)
# https://material.io/design/color/the-color-system.html
ERROR_COLOR_RED = "#b00020"
ERROR_COLLOR_YELLOW = "#ffde03"
GRID_GRAY = "#f2f2f2"
FRAME_GRAY = "#d6d6d6"
BACKGROUND_GRAY = "#eeeeee"

MATERIAL_COLORS = {
    "red": "#f44336",
    "pink": "#e91e63",
    "purple": "#9c27b0",
    "deeppurple": "#673ab7",
    "indigo": "#3f51b5",
    "blue": "#2196f3",
    "lightblue": "#03a9f4",
    "cyan": "#00bcd4",
    "teal": "#009688",
    "green": "#4caf50",
    "lightgreen": "#8bc34a",
    "lime": "#cddc39",
    "yellow": "#ffeb3b",
    "amber": "#ffc107",
    "orange": "#ff9800",
    "deeporange": "#ff5722",
    "brown": "#795548",
    "gray": "#9e9e9e",
    "bluegray": "#607d8b"
}

COLORS = list(MATERIAL_COLORS.values())


# Specific formats
PROJECTS = {
    11488: {"id": 1, "color":MATERIAL_COLORS["red"]},
    9710: {"id": 2, "color": MATERIAL_COLORS["pink"]},
    9196: {"id": 3, "color": MATERIAL_COLORS["purple"]},
    9105: {"id": 4, "color": MATERIAL_COLORS["deeppurple"]},
    8926: {"id": 5, "color": MATERIAL_COLORS["indigo"]},
    8286: {"id": 6, "color": MATERIAL_COLORS["blue"]},
    7822: {"id": 7, "color": MATERIAL_COLORS["lightblue"]},
    7449: {"id": 8, "color": MATERIAL_COLORS["cyan"]},
    7396: {"id": 9, "color": MATERIAL_COLORS["teal"]},
    7292: {"id": 10, "color": MATERIAL_COLORS["green"]},
    6996: {"id": 11, "color": MATERIAL_COLORS["lightgreen"]},
    6758: {"id": 12, "color": MATERIAL_COLORS["lime"]},
    6474: {"id": 13, "color": MATERIAL_COLORS["yellow"]},
    5922: {"id": 14, "color": MATERIAL_COLORS["amber"]},
    5646: {"id": 15, "color": MATERIAL_COLORS["orange"]},
    5585: {"id": 16, "color": MATERIAL_COLORS["deeporange"]},
    5584: {"id": 17, "color": MATERIAL_COLORS["brown"]},
    5527: {"id": 18, "color": MATERIAL_COLORS["gray"]},
    5444: {"id": 19, "color": MATERIAL_COLORS["bluegray"]}
}

TECHNOLOGIES = {
    "python": {"id": "Python", "short": "Python", "color": MATERIAL_COLORS["lightblue"]},
    "terraform": {"id": "Terraform", "short": "Terraform", "color": MATERIAL_COLORS["deeppurple"]},
    "cloudformation": {"id": "CloudFormation", "short": "Cloud\nFormation", "color": MATERIAL_COLORS["pink"]},
    "arm": {"id": "ARM", "short": "ARM", "color": MATERIAL_COLORS["indigo"]},
    "docker": {"id": "Docker", "short": "Docker", "color": MATERIAL_COLORS["bluegray"]},
    "vue.js": {"id": "Vue.js", "short": "Vue.js", "color": MATERIAL_COLORS["green"]},
    "typescript": {"id": "TypeScript", "short": "Type\nScript", "color": MATERIAL_COLORS["amber"]},
    "dynamodb": {"id": "DynamoDB", "short": "Dynamo\nDB", "color": MATERIAL_COLORS["deeporange"]}
}

USERS = {
    "e01e4ef9": {"id": 1, "color":  MATERIAL_COLORS["red"]},
    "2207de84": {"id": 2, "color":  MATERIAL_COLORS["indigo"]},
    "da64b86a": {"id": 3, "color":  MATERIAL_COLORS["pink"]},
    "2387bb0e": {"id": 4, "color":  MATERIAL_COLORS["blue"]},
    "b37a8a77": {"id": 5, "color":  MATERIAL_COLORS["lightgreen"]},
    "ea58e5b8": {"id": 6, "color":  MATERIAL_COLORS["orange"]},
    "626b4ab1": {"id": 7, "color":  MATERIAL_COLORS["yellow"]},
    "3880863a": {"id": 8, "color":  MATERIAL_COLORS["lightblue"]},
    "e3efa80f": {"id": 9, "color":  MATERIAL_COLORS["deeppurple"]},
    "792bed70": {"id": 10, "color": MATERIAL_COLORS["green"]},
    "78877e27": {"id": 11, "color": MATERIAL_COLORS["cyan"]},
    "2bca1cc8": {"id": 12, "color": MATERIAL_COLORS["lime"]},
    "64686e7b": {"id": 13, "color": MATERIAL_COLORS["purple"]},
    "e123e885": {"id": 14, "color": MATERIAL_COLORS["amber"]},
    "4d39fcbe": {"id": 15, "color": MATERIAL_COLORS["deeporange"]},
    "eec55d30": {"id": 16, "color": MATERIAL_COLORS["teal"]},
}
