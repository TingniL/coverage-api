"""
Entrée FastAPI :
- /coverage POST {id: adresse, ...}
- Swagger généré automatiquement avec tags et description en français
"""
import asyncio
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.geocoder import geocode_address
from app.coverage import compute_coverage
from app.config import OPERATORS, RADII

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="API de Couverture Mobile",
    description="Fournit la couverture mobile 2G/3G/4G pour des adresses en France.",
    version="1.0.0",
)

class CoverageResponse(BaseModel):
    results: Dict = Field(
        ...,
        example={
            "Tour Eiffel": {
                "orange": {"2G": True, "3G": True, "4G": True},
                "sfr": {"2G": True, "3G": True, "4G": True},
            },
            "Adresse Invalide": {
                "error": "Impossible de géocoder l'adresse : 123 Rue du Nulle Part"
            }
        }
    )

@app.post("/coverage", response_model=CoverageResponse, tags=["Couverture"])
async def get_coverage(
    locations: Dict[str, str] = Body(
        ...,
        example={
            "id1": "157 boulevard MacDonald 75019 Paris",
            "id2": "5 avenue Anatole France 75007 Paris",
        },
    )
):
    """
    Accepte une ou plusieurs adresses et retourne leur couverture réseau mobile.
    """
    logging.info(f"Requête de couverture reçue pour {len(locations)} adresses.")
    addresses_to_process = locations.items()
    
    async def geocode_task(name, address):
        try:
            # Exécute la fonction synchrone de géocodage dans un thread séparé
            # pour ne pas bloquer la boucle d'événements asyncio.
            coords = await run_in_threadpool(geocode_address, address)
            if coords is None:

                return name, {"error": f"Impossible de géocoder l'adresse : {address}"}
            return name, {"coords": coords}
        except Exception as e:
            logging.error(f"Erreur inattendue lors du géocodage pour '{address}': {e}", exc_info=True)
            return name, {"error": "Erreur serveur lors du géocodage"}

    geocoding_tasks = [geocode_task(name, addr) for name, addr in addresses_to_process]
    geocoding_results = await asyncio.gather(*geocoding_tasks)

    coverage_tasks = []
    final_results = {}
    successful_geocodes = 0
    failed_geocodes = 0

    for name, result in geocoding_results:
        if "coords" in result:
            lat, lon = result["coords"]
            coverage_tasks.append(compute_coverage(lat, lon))
            final_results[name] = None
            successful_geocodes += 1
        else:
            final_results[name] = result
            failed_geocodes += 1
            
    logging.info(f"Géocodage terminé : {successful_geocodes} réussites, {failed_geocodes} échecs.")

    if coverage_tasks:
        try:
            coverage_results = await asyncio.gather(*coverage_tasks)
            
            coverage_idx = 0
            for name in final_results:
                if final_results[name] is None:
                    final_results[name] = coverage_results[coverage_idx]
                    coverage_idx += 1
        except Exception as e:
            logging.error(f"Erreur lors du calcul de la couverture : {e}", exc_info=True)
            # En cas d'erreur ici, on ne peut pas continuer.
            raise HTTPException(status_code=500, detail="Erreur interne du serveur lors du calcul de la couverture.")

    logging.info("Requête de couverture traitée avec succès.")
    return {"results": final_results}
