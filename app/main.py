"""
Entrée FastAPI :
- /coverage POST {id: adresse, ...}
- Swagger généré automatiquement avec tags et description en français
"""
import asyncio
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.geocoder import geocode_address
from app.coverage import compute_coverage
from app.config import OPERATORS, RADII

app = FastAPI(
    title="API de Couverture Mobile",
    description="Fournit la couverture mobile 2G/3G/4G pour des adresses en France.",
    version="1.0.0",
)

class CoverageRequest(BaseModel):
    locations: Dict[str, str] = Field(
        ...,
        example={
            "Tour Eiffel": "Champ de Mars, 5 Av. Anatole France, 75007 Paris",
            "Adresse Invalide": "123 Rue du Nulle Part",
        },
        description="Un dictionnaire où les clés sont des noms de lieux et les valeurs sont les adresses à géocoder."
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
async def get_coverage(request: CoverageRequest):
    """
    Accepte une ou plusieurs adresses et retourne leur couverture réseau mobile.
    """
    addresses_to_process = request.locations.items()
    
    # Étape 1: Géocoder toutes les adresses en parallèle
    async def geocode_task(name, address):
        try:
            # Exécute la fonction synchrone de géocodage dans un thread séparé
            # pour ne pas bloquer la boucle d'événements asyncio.
            coords = await run_in_threadpool(geocode_address, address)
            if coords is None:
                return name, {"error": f"Impossible de géocoder l'adresse : {address}"}
            return name, {"coords": coords}
        except Exception as e:
            return name, {"error": str(e)}

    geocoding_tasks = [geocode_task(name, addr) for name, addr in addresses_to_process]
    geocoding_results = await asyncio.gather(*geocoding_tasks)

    # Étape 2: Calculer la couverture pour les adresses géocodées avec succès
    coverage_tasks = []
    final_results = {}

    for name, result in geocoding_results:
        if "coords" in result:
            lat, lon = result["coords"]
            # La fonction compute_coverage est déjà asynchrone
            coverage_tasks.append(compute_coverage(lat, lon))
            final_results[name] = None # Placeholder
        else:
            final_results[name] = result # Stocker l'erreur

    coverage_results = await asyncio.gather(*coverage_tasks)

    # Étape 3: Assembler les résultats finaux
    coverage_idx = 0
    for name in final_results:
        if final_results[name] is None:
            final_results[name] = coverage_results[coverage_idx]
            coverage_idx += 1
            
    return {"results": final_results}
