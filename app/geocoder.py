"""
Ce module fournit une interface pour le géocodage d'adresses
en utilisant le service Nominatim de OpenStreetMap.

Fonctions:
    geocode_address(address: str) -> Optional[Tuple[float, float]]:
        Convertit une adresse textuelle en coordonnées (latitude, longitude).
"""
import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Initialisation du géocodeur
# Le user_agent est important pour respecter les conditions d'utilisation d'OSM.
geolocator = Nominatim(user_agent="mobile_coverage_api/1.0")

# Ajout d'un limiteur de taux pour ne pas surcharger le service (1 requête/seconde)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Géocode une seule adresse.

    Args:
        address: L'adresse à géocoder.

    Returns:
        Un tuple (latitude, longitude) si le géocodage réussit, sinon None.
    """
    try:
        location = geocode(address, country_codes="FR", addressdetails=False) #Limiter la recherche à la France
        if location:
            logging.info(f"Géocodage réussi pour '{address}': ({location.latitude}, {location.longitude})")
            return (location.latitude, location.longitude)
        else:
            logging.warning(f"Échec du géocodage pour '{address}': aucune coordonnée trouvée.")
            return None
    except Exception as e:
        logging.error(f"Erreur lors du géocodage pour '{address}': {e}")
        return None
