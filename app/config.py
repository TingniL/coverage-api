"""
Fichier de configuration centrale : chemins, opérateurs et rayons.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_CSV      = BASE_DIR / "data" / "2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv"
PARQUET_PATH = BASE_DIR / "data" / "towers.parquet"

OPERATORS = ["orange", "sfr", "bouygues", "free"]
RADII = {"2G": 30, "3G": 5, "4G": 10}  # Rayon de couverture en kilomètres
