Reconstruction du .venv fourni
==============================

Le fichier .venv.zip envoyé contient un environnement virtuel Python Windows,
pas un fichier .env / .env.example.

Informations détectées :
- Python : 3.13.2
- Implémentation : CPython
- virtualenv : 20.24.5
- include-system-site-packages : false

Pour recréer un environnement similaire :

Windows (PowerShell)
--------------------
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Windows (cmd)
-------------
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
