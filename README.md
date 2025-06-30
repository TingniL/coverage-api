# API de Couverture Mobile en France

Ce projet fournit une API web simple mais puissante pour vérifier la couverture des réseaux mobiles (2G, 3G, 4G) pour n'importe quelle adresse en France métropolitaine.

Il utilise les données ouvertes sur les infrastructures de téléphonie mobile publiées par l'ARCEP et les expose via une API FastAPI performante.

## Fonctionnalités

- **API RESTful** : Un point d'accès unique (`/coverage`) pour toutes les requêtes.
- **Géocodage d'adresses** : Convertit automatiquement les adresses postales en coordonnées géographiques (latitude, longitude).
- **Calcul de couverture optimisé** : Utilise des arbres spatiaux (`BallTree` de scikit-learn) pour des recherches de proximité ultra-rapides.
- **Gestion par lot** : Permet de soumettre plusieurs adresses en une seule requête pour plus d'efficacité.
- **Gestion des erreurs robuste** : Traite les adresses invalides sans interrompre la requête entière.
- **Prêt pour la conteneurisation** : Inclut un `Dockerfile` pour un déploiement facile.

## Architecture

Le projet est divisé en deux phases principales :

1.  **Prétraitement (Hors ligne)** : Un script (`app/preprocessing.py`) lit les données brutes des antennes au format CSV, nettoie les informations, convertit les coordonnées du système Lambert 93 vers WGS84, et sauvegarde le résultat dans un fichier Parquet optimisé (`towers.parquet`). Cette étape n'est à exécuter qu'une seule fois ou lors de la mise à jour des données sources.

2.  **Service API (En ligne)** : Une application FastAPI qui :
    -   Reçoit des requêtes POST avec des adresses.
    -   Géocode chaque adresse pour obtenir des coordonnées.
    -   Pour chaque coordonnée, interroge les arbres spatiaux pré-calculés pour déterminer si une antenne (par opérateur et par technologie) se trouve dans le rayon de couverture défini.
    -   Retourne un rapport de couverture détaillé au format JSON.

## Installation

### Prérequis

-   Python 3.9+
-   Git

### Étapes

1.  **Clonez le dépôt :**
    ```bash
    git clone <URL_DU_DEPOT>
    cd coverage-api
    ```

2.  **Créez un environnement virtuel et activez-le :**
    ```bash
    python -m venv venv
    # Sur Windows
    venv\Scripts\activate
    # Sur macOS/Linux
    source venv/bin/activate
    ```

3.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Téléchargez les données brutes :**
    Assurez-vous que le fichier `2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv` est présent dans le dossier `data/`. S'il n'est pas là, vous devrez le télécharger depuis une source de données ouvertes comme data.gouv.fr.

5.  **Exécutez le script de prétraitement :**
    Cette commande va générer le fichier `data/towers.parquet` nécessaire à l'API.
    ```bash
    python -m app.preprocessing
    ```

## Utilisation

### Lancer le serveur de développement

Pour démarrer l'API localement, utilisez `uvicorn` :

```bash
uvicorn app.main:app --reload
```

Le serveur sera accessible à l'adresse `http://127.0.0.1:8000`.

### Documentation de l'API

Une fois le serveur lancé, la documentation interactive (Swagger UI) est disponible à l'adresse :
`http://127.0.0.1:8000/docs`

### Exemples de requêtes

Vous pouvez utiliser `curl` ou tout autre client HTTP pour interroger l'API.

**Requête :**
```bash
curl -X POST "http://127.0.0.1:8000/coverage" \
-H "Content-Type: application/json" \
-d '{
  "id1": "157 boulevard MacDonald 75019 Paris",
  "id2": "5 avenue Anatole France 75007 Paris"
}'
```

**Réponse attendue :**
```json
{
  "results": {
    "id1": {
      "orange": { "2G": true, "3G": true, "4G": true },
      "sfr": { "2G": true, "3G": true, "4G": true },
      "bouygues": { "2G": true, "3G": true, "4G": true },
      "free": { "2G": false, "3G": true, "4G": true }
    },
    "id2": {
      "orange": { "2G": true, "3G": true, "4G": true },
      "sfr": { "2G": true, "3G": true, "4G": true },
      "bouygues": { "2G": true, "3G": true, "4G": true },
      "free": { "2G": false, "3G": true, "4G": true }
    }
  }
}
```

## Tests

Pour exécuter la suite de tests automatisés, utilisez `pytest` :

```bash
pytest
```

Pour un débogage plus ciblé de la logique de couverture, vous pouvez exécuter :

```bash
python debug_coverage.py
```

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
