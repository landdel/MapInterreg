import requests
import csv
import time


def get_coordinates(address):
    headers = {"User-Agent": "MyPythonApp/1.0"}

    # 1. Essai avec Photon
    try:
        base_url_photon = "https://photon.komoot.io/api/"
        params_photon = {
            "q": address,
            "limit": 1,
            "lang": "fr"
        }

        response = requests.get(base_url_photon, params=params_photon, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            if features:
                coordinates = features[0]["geometry"]["coordinates"]
                longitude = coordinates[0]
                latitude = coordinates[1]
                return latitude, longitude

    except requests.RequestException:
        pass

    # 2. Si Photon ne trouve pas, essai avec Nominatim
    try:
        base_url_osm = "https://nominatim.openstreetmap.org/search"
        params_osm = {
            "q": address,
            "format": "json",
            "limit": 1
        }

        response = requests.get(base_url_osm, params=params_osm, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data:
                latitude = data[0]["lat"]
                longitude = data[0]["lon"]
                return latitude, longitude
            else:
                return "Adresse introuvable", "Adresse introuvable"
        else:
            return f"Erreur {response.status_code}", f"Erreur {response.status_code}"

    except requests.RequestException as e:
        return f"Erreur réseau : {e}", f"Erreur réseau : {e}"


def parse_coordinate(value):
    if value is None:
        return None

    value = str(value).strip()
    if value == "":
        return None

    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


if __name__ == "__main__":
    input_file = "adresses.csv"
    output_file = "locations.csv"

    with open(input_file, newline='', encoding='cp1252') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        rows = list(reader)

    total_addresses = len(rows)
    processed_count = 0

    # Compteurs séparés
    existing_count = 0
    found_count = 0
    error_count = 0

    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["latitude", "longitude", "category", "type", "name", "acronym", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        print("Début de la recherche des coordonnées")

        for row in rows:
            processed_count += 1

            address_parts = [
                row.get("street", ""),
                row.get("postnumber", ""),
                row.get("zipcode", ""),
                row.get("city", ""),
                row.get("country", "")
            ]
            address = ' '.join(part for part in address_parts if part)

            existing_latitude = parse_coordinate(row.get("Latitude"))
            existing_longitude = parse_coordinate(row.get("Longitude"))

            # Cas 1 : coordonnées déjà présentes dans le CSV
            if existing_latitude is not None and existing_longitude is not None:
                latitude = existing_latitude
                longitude = existing_longitude
                existing_count += 1

                print(f"\t{processed_count}/{total_addresses} - Coordonnées déjà disponibles dans le fichier CSV pour : {address}")

            # Cas 2 : il faut lancer la recherche
            else:
                print(f"\t{processed_count}/{total_addresses} - Recherche des coordonnées pour : {address}")
                latitude, longitude = get_coordinates(address)
                time.sleep(1)

                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                    found_count += 1
                    print(f"\t\tCoordonnées trouvées via API pour : {address}")
                except (ValueError, TypeError):
                    error_count += 1
                    print(f"\t\tAdresse introuvable via Photon/Nominatim : {address}")
                    continue

            # Écriture dans le fichier de sortie
            writer.writerow({
                "latitude": latitude,
                "longitude": longitude,
                "type": row["type"],
                "category": row["category"],
                "name": row["name"],
                "acronym": row["acronym"],
                "url": row["url"]
            })

    print("\nRécapitulatif final")
    print(f"Total d'adresses traitées : {total_addresses}")
    print(f"Coordonnées déjà présentes dans le CSV : {existing_count}")
    print(f"Coordonnées trouvées via API : {found_count}")
    print(f"Adresses non trouvées : {error_count}")
    print(f"Les coordonnées GPS ont été enregistrées dans {output_file}")
