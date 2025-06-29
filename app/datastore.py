"""
Charge les données des antennes et construit des BallTree pour la recherche géospatiale rapide.
Expose la fonction is_covered(lat, lon, operator, tech).
"""
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from functools import lru_cache
from app.config import PARQUET_PATH, RADII

EARTH_RADIUS_KM = 6371.0  # Rayon terrestre utilisé dans la distance haversine

@lru_cache
def _load_trees():
    df = pd.read_parquet(PARQUET_PATH)
    trees = {}

    # Pour chaque opérateur et technologie, on construit un BallTree
    for op in df["operator"].unique():
        sub = df[df["operator"] == op]

        for tech, col in [("2G", "is2g"), ("3G", "is3g"), ("4G", "is4g")]:
            rows = sub[sub[col] == 1][["lat", "lon"]].to_numpy()
            if len(rows):
                trees[(op, tech)] = BallTree(np.radians(rows), metric="haversine")
    return trees

def is_covered(lat: float, lon: float, operator: str, tech: str) -> bool:
    trees = _load_trees()
    tree = trees.get((operator, tech))
    if tree is None:
        return False

    # Convert query point to radians
    query_point_rad = np.radians([[lat, lon]])

    # Convert coverage radius from km to radians
    radius_rad = RADII[tech] / EARTH_RADIUS_KM

    # Find all points within radius
    idx = tree.query_radius(query_point_rad, r=radius_rad)
    
    return bool(idx[0].size)
