# MapInterreg

Interface web minimaliste ajoutee pour lancer les scripts et consulter le dernier resultat.

## Lancer l'interface web

```bash
pip install flask
python webapp.py
```

Puis ouvrir dans le navigateur : `http://127.0.0.1:5000`

## Fonctions de l'interface

- `Generer locations.csv` lance `coordinates.py`
- `Generer la carte` lance `mapping.py`
- `Tout executer` lance les deux scripts
- le dernier fichier `result/map_*.html` est affiche dans la page
