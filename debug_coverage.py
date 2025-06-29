import asyncio
import pandas as pd
from app.coverage import compute_coverage
from app.datastore import is_covered
from app.config import RADII, OPERATORS

# --- Configuration des Scénarios de Test ---

# Scénario 1: Coordonnées exactes d'une antenne existante
# Nous sélectionnons une antenne "free" au hasard depuis notre jeu de données.
# Ce test doit toujours réussir car nous sommes au point exact de l'antenne.
df = pd.read_parquet("data/towers.parquet")
tour_free_existante = df[(df["operator"] == "free") & (df["is3g"] == 1) & (df["is4g"] == 1)].iloc[0]
LAT_TEST_EXACT = tour_free_existante["lat"]
LON_TEST_EXACT = tour_free_existante["lon"]

# Scénario 2: Un point connu à Paris (devrait avoir une excellente couverture)
LAT_TEST_PARIS = 48.8566
LON_TEST_PARIS = 2.3522

# Scénario 3: Un point dans une zone rurale (couverture potentiellement partielle)
# Quelque part dans le parc naturel régional du Morvan
LAT_TEST_RURAL = 47.0769
LON_TEST_RURAL = 4.0203

# Scénario 4: Un point au milieu de l'océan Atlantique (aucune couverture attendue)
LAT_TEST_OCEAN = 46.2276
LON_TEST_OCEAN = -10.0

async def run_test_scenario(nom_scenario: str, lat: float, lon: float):
    """
    Exécute un scénario de test pour un point géographique donné et affiche les résultats.
    """
    print(f"--- Lancement du Scénario : {nom_scenario} ---")
    print(f"Coordonnées de test : (lat={lat:.4f}, lon={lon:.4f})")
    print(f"Rayons de couverture configurés : {RADII} km")
    print("-" * 20)

    # Test direct de la fonction de bas niveau is_covered
    print("Étape 1: Test direct de la fonction is_covered (pour free)")
    free_3g_covered = is_covered(lat, lon, "free", "3G")
    free_4g_covered = is_covered(lat, lon, "free", "4G")
    print(f"Couverture Free 3G ? -> {free_3g_covered}")
    print(f"Couverture Free 4G ? -> {free_4g_covered}")
    print("-" * 20)

    # Test de la fonction de haut niveau compute_coverage
    print("Étape 2: Test de la fonction compute_coverage (pour tous les opérateurs)")
    all_coverage = await compute_coverage(lat, lon)

    print("Résultats complets de la couverture :")
    import json
    print(json.dumps(all_coverage, indent=2, ensure_ascii=False))
    print("-" * 20)

    # Analyse des résultats
    print("Analyse des résultats :")
    total_couverture = sum(tech for op_cov in all_coverage.values() for tech in op_cov.values())
    if total_couverture > 0:
        print(f"✅ Succès : {total_couverture} couvertures actives trouvées.")
    else:
        print("✅ Succès (attendu pour les zones sans service) : Aucune couverture détectée.")
    print("\n")


async def main():
    """
    Fonction principale pour exécuter tous les scénarios de test.
    """
    # Exécution séquentielle de chaque scénario
    await run_test_scenario(
        "Point Exact d'une Antenne Free",
        LAT_TEST_EXACT,
        LON_TEST_EXACT
    )
    await run_test_scenario(
        "Centre de Paris",
        LAT_TEST_PARIS,
        LON_TEST_PARIS
    )
    await run_test_scenario(
        "Zone Rurale (Morvan)",
        LAT_TEST_RURAL,
        LON_TEST_RURAL
    )
    await run_test_scenario(
        "Océan Atlantique",
        LAT_TEST_OCEAN,
        LON_TEST_OCEAN
    )


if __name__ == "__main__":
    # La fonction compute_coverage étant asynchrone, nous utilisons asyncio.run
    # Réinitialise le cache LRU avant de commencer pour garantir un chargement propre des données
    is_covered.cache_clear()
    asyncio.run(main()) 