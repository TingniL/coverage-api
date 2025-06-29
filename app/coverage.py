"""
Rassemble la géocodification et le calcul de couverture pour un point donné.
"""
from app.datastore import is_covered
from app.config import OPERATORS

TECHS = ["2G", "3G", "4G"]

async def compute_coverage(lat: float, lon: float) -> dict:
    res: dict = {}
    for op in OPERATORS:
        res[op] = {tech: is_covered(lat, lon, op, tech) for tech in TECHS}
    return res
