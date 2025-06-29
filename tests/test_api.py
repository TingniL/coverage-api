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
    nom_adresse = "Champs-Élysées"
    adresse = "133 Av. des Champs-Élysées, 75008 Paris"
    
    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 200
    data = response.json()
    
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
    On s'attend à un code 404 (Not Found) avec un message d'erreur.
    """
    nom_adresse = "Adresse Inexistante"
    adresse = "123 Rue du Nulle Part, 99999 Inexistant"
    
    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert f"Impossible de géocoder l'adresse : {adresse}" in data["detail"]

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
        "Tour Eiffel": "Champ de Mars, 5 Av. Anatole France, 75007 Paris",
        "Notre Dame": "6 Parvis Notre-Dame - Pl. Jean-Paul II, 75004 Paris"
    }
    
    response = client.post("/coverage", json=adresses)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "Tour Eiffel" in data
    assert "Notre Dame" in data
    assert "orange" in data["Tour Eiffel"]
    assert "free" in data["Notre Dame"]

def test_adresse_hors_de_france():
    """
    Teste une adresse valide mais située hors de la zone de couverture (France).
    On s'attend à un code 200, mais avec une couverture nulle pour tous les opérateurs.
    """
    nom_adresse = "New York"
    adresse = "Statue of Liberty, New York, NY, USA"

    response = client.post("/coverage", json={nom_adresse: adresse})
    
    assert response.status_code == 200
    data = response.json()
    
    assert nom_adresse in data
    couverture_adresse = data[nom_adresse]
    
    # Vérifie que la couverture est fausse pour toutes les technologies de tous les opérateurs
    for op in OPERATORS:
        assert op in couverture_adresse
        assert not couverture_adresse[op]["2G"]
        assert not couverture_adresse[op]["3G"]
        assert not couverture_adresse[op]["4G"]
