"""
Script de prétraitement :
- Lecture du fichier CSV source
- Nettoyage et standardisation des données (noms d'opérateurs, etc.)
- Conversion des coordonnées Lambert93 en WGS84
- Sauvegarde au format Parquet pour un chargement plus rapide

Utilisation :
    python -m app.preprocessing
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pyproj
from app.config import RAW_CSV, PARQUET_PATH, OPERATORS

def validate_data(df: pd.DataFrame) -> None:
    """Validation de l'intégrité des données"""
    required_columns = {"Operateur", "x", "y", "2G", "3G", "4G"}
    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans le fichier CSV : {missing_cols}")

def clean_operator_names(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage et standardisation des noms d'opérateurs"""
    # Conversion en minuscules
    df['operator'] = df['operator'].str.lower()
    
    # Vérification des opérateurs
    valid_operators = [op.lower() for op in OPERATORS]
    df = df[df['operator'].isin(valid_operators)]
    
    return df

def convert_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Conversion des coordonnées en lot (Lambert93 -> WGS84)"""
    try:
        # Création du transformateur
        transformer = pyproj.Transformer.from_crs("epsg:2154", "epsg:4326")
        
        # Conversion en lot
        print("Conversion des coordonnées en cours...")
        lat, lon = transformer.transform(df["x"].values, df["y"].values)
        
        # Ajout des colonnes de latitude et longitude
        df["lat"] = lat
        df["lon"] = lon
        
        return df
    except Exception as e:
        raise RuntimeError(f"Échec de la conversion des coordonnées : {str(e)}")

def validate_coordinates(df: pd.DataFrame) -> None:
    """Validation des coordonnées converties"""
    # Limites approximatives de la France
    FRANCE_BOUNDS = {
        'lat': (41.0, 52.0),  # Latitude
        'lon': (-5.0, 10.0)   # Longitude
    }
    
    invalid_coords = (
        (df['lat'] < FRANCE_BOUNDS['lat'][0]) |
        (df['lat'] > FRANCE_BOUNDS['lat'][1]) |
        (df['lon'] < FRANCE_BOUNDS['lon'][0]) |
        (df['lon'] > FRANCE_BOUNDS['lon'][1])
    )
    
    if invalid_coords.any():
        n_invalid = invalid_coords.sum()
        print(f"Attention : {n_invalid} points hors de France métropolitaine détectés, ces données seront filtrées")
        return df[~invalid_coords]
    return df

def process_data() -> None:
    """Fonction principale de traitement"""
    try:
        # 1. Vérification du fichier d'entrée
        if not RAW_CSV.exists():
            raise FileNotFoundError(f"Fichier CSV introuvable : {RAW_CSV}")
        
        print(f"Début du traitement...")
        print(f"Fichier d'entrée : {RAW_CSV}")
        print(f"Fichier de sortie : {PARQUET_PATH}")
        
        # 2. Lecture du CSV
        print("Lecture du fichier CSV...")
        df = pd.read_csv(RAW_CSV)
        print(f"Nombre de lignes lues : {len(df)}")
        
        # 3. Validation des données
        validate_data(df)
        
        # 4. Renommage des colonnes
        print("Standardisation des noms de colonnes...")
        df.rename(columns={
            "Operateur": "operator",
            "2G": "is2g",
            "3G": "is3g",
            "4G": "is4g"
        }, inplace=True)
        
        # 5. Nettoyage des noms d'opérateurs
        print("Nettoyage des données opérateurs...")
        initial_count = len(df)
        df = clean_operator_names(df)
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            print(f"Filtrage : {filtered_count} antennes d'opérateurs non configurés ont été exclues")
        
        # 6. Conversion des coordonnées
        df = convert_coordinates(df)
        
        # 7. Sauvegarde des résultats
        print(f"Sauvegarde des données traitées...")
        df.to_parquet(PARQUET_PATH, index=False)
        
        # 8. Statistiques
        print("\nTraitement terminé !")
        print(f"Nombre total d'antennes : {len(df)}")
        print("\nStatistiques par opérateur :")
        print(df.groupby('operator').size().to_string())
        print("\nStatistiques par technologie :")
        for tech in ['is2g', 'is3g', 'is4g']:
            count = df[tech].sum()
            print(f"{tech.upper()} : {count} antennes")
            
    except Exception as e:
        print(f"Erreur : {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    process_data()
