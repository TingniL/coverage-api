import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import OPERATORS

client = TestClient(app)

# --- Scénarios de Test pour l'API ---

def test_adresse_valide_paris():
    """
    Teste une adresse valide à Paris.
    On s'attend à un code 200 et à des données de couverture pour tous les opérateurs.
    """
    nom_adresse = "Musée du Louvre"
    adresse = "Musée du Louvre, 75001 Paris"
    
    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 200
    data = response.json()["results"]
    
    assert nom_adresse in data
    couverture_adresse = data[nom_adresse]
    
    # Vérifie que tous les opérateurs configurés sont présents dans la réponse
    for op in OPERATORS:
        assert op in couverture_adresse
        assert "2G" in couverture_adresse[op]
        assert "3G" in couverture_adresse[op]
        assert "4G" in couverture_adresse[op]
        
    # À Paris, on s'attend à une couverture quasi totale
    couverture_totale = sum(val for op_cov in couverture_adresse.values() for val in op_cov.values())
    assert couverture_totale > 10  # Au moins 10/12 couvertures actives

def test_adresse_invalide():
    """
    Teste une adresse qui ne peut pas être géocodée.
    On s'attend à un code 200 et à un message d'erreur dans le JSON.
    """
    nom_adresse = "Adresse Inexistante"
    adresse = "123 Rue du Nulle Part, 99999 Inexistant"
    
    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 200
    data = response.json()["results"]
    assert nom_adresse in data
    assert "error" in data[nom_adresse]
    assert "Impossible de géocoder" in data[nom_adresse]["error"]

def test_requete_malformee_pas_de_json():
    """
    Teste l'envoi de données qui ne sont pas au format JSON.
    On s'attend à un code 422 (Unprocessable Entity).
    """
    response = client.post("/coverage", data="ceci n'est pas du json")
    assert response.status_code == 422

def test_requete_avec_plusieurs_adresses():
    """
    Teste une requête contenant plusieurs adresses valides.
    La réponse doit contenir les résultats pour chaque adresse.
    """
    adresses = {
        "Musée du Louvre": "Musée du Louvre, 75001 Paris",
        "Notre Dame": "Notre Dame, Paris"
    }
    
    response = client.post("/coverage", json=adresses)
    
    assert response.status_code == 200
    data = response.json()["results"]
    
    assert "Musée du Louvre" in data
    assert "Notre Dame" in data
    assert "orange" in data["Musée du Louvre"]
    assert "free" in data["Notre Dame"]

def test_adresse_hors_de_france():
    """
    Teste une adresse valide mais située hors de la zone de couverture (France).
    On s'attend à un code 200 et à un message d'erreur dans le JSON car le géocodage est limité à la France.
    """
    nom_adresse = "New York"
    adresse = "Statue of Liberty, New York, NY, USA"

    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 200
    data = response.json()["results"]
    
    assert nom_adresse in data
    assert "error" in data[nom_adresse]
    assert "Impossible de géocoder" in data[nom_adresse]["error"]
