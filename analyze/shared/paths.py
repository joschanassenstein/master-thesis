import sys
import locale
from pathlib import Path

# Set locale to DE
locale.setlocale(locale.LC_ALL,'de_DE')

# Include modules from parent directory
sys.path.append(str(Path().resolve().parent))

# Paths
DATABASE_PATH = Path().resolve().parent.joinpath("database").joinpath("_db.json")
CONFIG_PATH = Path().resolve().parent.joinpath("_config").joinpath("configuration.yaml")
