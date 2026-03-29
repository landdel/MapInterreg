import folium
from folium_jsbutton import JsButton
import pandas as pd
import json
from folium.plugins import MarkerCluster
import datetime
import numpy as np
from sklearn.cluster import DBSCAN
from html import escape  # Permet d'échapper correctement les caractères spéciaux
import branca


# Charger les données depuis le fichier CSV
file_path = "locations.csv"  # Chemin du fichier CSV
data = pd.read_csv(file_path, delimiter=';', skipinitialspace=True, dtype=str, engine='python',encoding="utf-8")
data["latitude"] = pd.to_numeric(data["latitude"], errors='coerce')
data["longitude"] = pd.to_numeric(data["longitude"], errors='coerce')


# Supprimer les entrées avec des valeurs non numériques dans les colonnes latitude et longitude
data = data[pd.to_numeric(data["latitude"], errors='coerce').notna() & pd.to_numeric(data["longitude"], errors='coerce').notna()]
config_file_path = "CONFIG.txt"

# Charger les fichiers GeoJSON pour les départements français et provinces belges
with open('zone\FR_Departements.geojson', 'r', encoding='utf-8') as f:
    france_geojson = json.load(f)
with open('zone\BE_Arrondissements.geojson', 'r', encoding='utf-8') as f:
    belgium_geojson = json.load(f)

# Calculer la position centrale
#XOrigin = data["latitude"].mean()
#YOrigin = data["longitude"].mean()

XOrigin =50.1851
YOrigin = 3.4973

# Initialisation des listes et
area_name ="Zone"
highlight_area_france = []
highlight_area_wallonie = []
highlight_area_vlaanderen = []

color_area_france = "blue"
color_area_wallonie = "blue"
color_area_vlaanderen = "blue"

point_name ="Points"
cluster_name="Clusters"
color_point ="blue"

threshold_km1 = 10  # Remplacez par la valeur souhaitée
threshold_km1_name = "Zone 10 Km"
color_group1 = "blue"
impactFactor1 = 500

threshold_km2 = 20  # Remplacez par la valeur souhaitée
threshold_km2_name = "Zone 20 Km"
color_group2 = "blue"
impactFactor2 = 500

# Lecture et traitement ligne par ligne
with open(config_file_path, "r",encoding="utf-8") as file:
    data_pt = []
    for line in file:
        line = line.strip()  # Supprime les espaces inutiles autour de la ligne

        if line.startswith("AREA NAME"):
            area_name = line.split(" : ")[1].strip()

        if line.startswith("CATEGORY"):
                parts = line.split(" : ")[1].split(",")
                category, name_cat, color, shape = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
                color_hex =  "#{:02x}{:02x}{:02x}".format(*tuple(map(int, color.strip("()").replace(";", ",").split(","))))
                data_pt.append([category, name_cat, shape, color_hex])

        elif line.startswith("CLUSTER NAME"):
            cluster_name = line.split(" : ")[1].strip()

        elif line.startswith("AREA FRANCE"):
            areas = line.split(" : ")[1].split(",")
            highlight_area_france = [area.strip() for area in areas]

        elif line.startswith("AREA WALLONIE"):
            areas = line.split(" : ")[1].split(",")
            highlight_area_wallonie = [area.strip() for area in areas]

        elif line.startswith("AREA VLAANDEREN"):
            areas = line.split(" : ")[1].split(",")
            highlight_area_vlaanderen = [area.strip() for area in areas]

        elif line.startswith("COLOR FRANCE"):
            color_area_france = "#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))

        elif line.startswith("COLOR WALLONIE"):
            color_area_wallonie = "#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))

        elif line.startswith("COLOR VLAANDEREN"):
            color_area_vlaanderen = "#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))

        elif line.startswith("POINT COLOR"):
            color_point ="#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))

        elif line.startswith("THRESHHOLD KM ONE"):

            threshold_km1 = int(line.split(" : ")[1].strip())
            threshold_km1_name = "Zone de "+str(threshold_km1)+" kilomètres"
        elif line.startswith("COLOR GROUPE ONE"):

            color_group1 = "#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))
        elif line.startswith("IMPACT FACTOR ONE"):

            impactFactor1 = int(line.split(" : ")[1].strip())

        elif line.startswith("THRESHHOLD KM TWO"):
            threshold_km2 = int(line.split(" : ")[1].strip())
            threshold_km2_name = "Zone de " + str(threshold_km2) + " kilomètres"
        elif line.startswith("COLOR GROUPE TWO"):
            color_group2 = "#{:02x}{:02x}{:02x}".format(*tuple(map(int, line.split(" : ", 1)[1].strip("()").split(","))))
        elif line.startswith("IMPACT FACTOR TWO"):

            impactFactor2 = int(line.split(" : ")[1].strip())

    df_points = pd.DataFrame(data_pt, columns=["category", "name_Cat", "shape", "color"])

threshold_radians1 = threshold_km1 / 6371.0
threshold_radians2 = threshold_km2 / 6371.0

# Créer une carte centrée
m = folium.Map(location=[XOrigin, YOrigin], zoom_start=8)

folium.TileLayer(
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
         'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    name='CartoDB Dark Matter',
    show=False # Désactive la couche au démarrage
).add_to(m)

JsButton(
    title='<i class="fas fa-crosshairs"></i>',
    function="""
    function(btn, map) {
        var xOrigin = %f;
        var yOrigin = %f;
        map.setView([xOrigin, yOrigin], 8);
        btn.state('zoom-to-forest');
    }
    """ % (XOrigin, YOrigin)
).add_to(m)

# Ajouter une couche pour la légende
legend_layer = folium.FeatureGroup(name="Légende", show=True)

# Générer dynamiquement la légende à partir de df_points
legend_html = """
    <div style="
        position: absolute; 
        bottom: 10px; left: 10px; 
        background-color: white; 
        border: 2px solid grey; 
        padding: 10px; 
        font-size: 14px; 
        z-index: 9999; 
        width: 220px;
    ">
    <b>Légende :</b><br>
"""

# Ajouter chaque catégorie avec sa couleur et forme spécifique
for _, row in df_points.iterrows():
    shape = row["shape"]
    color = row["color"]
    name_cat = escape(row["name_Cat"])  # Échapper les caractères spéciaux pour l'affichage HTML

    if shape == "circle":
        shape_html = f'<i style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:{color};"></i>'
    elif shape == "square":
        shape_html = f'<i style="display:inline-block; width:12px; height:12px; background-color:{color}; border: 2px solid black;"></i>'
    elif shape == "triangle":
        shape_html = f'<i style="display:inline-block; width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-bottom:12px solid {color};"></i>'
    else:
        shape_html = f'<i style="display:inline-block; width:12px; height:12px; background-color:{color};"></i>'  # Par défaut

    legend_html += f"{shape_html} {name_cat}<br>"

# Ajouter les autres éléments de la légende (zones géographiques)
legend_html += f"""
    <i style="display:inline-block; width:12px; height:12px; background-color:{color_area_wallonie};"></i> {escape("Wallonie")}<br>
    <i style="display:inline-block; width:12px; height:12px; background-color:{color_area_vlaanderen};"></i> {escape("Flandre")}<br>
    <i style="display:inline-block; width:12px; height:12px; background-color:{color_area_france};"></i> {escape("France")}<br>
    </div>
"""

# Ajouter la légende sur la carte
m.get_root().html.add_child(folium.Element(legend_html))

# Ajouter une couche pour les régions INTERREG (départements français et provinces belges)
interreg_layer = folium.FeatureGroup(name=area_name, show=True)
for feature in france_geojson['features']:
    if feature['properties']['nom'] in highlight_area_france:  # Modifier la clé selon votre GeoJSON
        folium.GeoJson(
            feature,
            style_function=lambda x: {'fillColor': color_area_france, 'color': color_area_france, 'weight': 1, 'fillOpacity': 0.4},
            control=True
        ).add_to(interreg_layer)


for feature in belgium_geojson['features']:
    if feature['properties']['name'] in highlight_area_wallonie:  # Modifier la clé selon votre GeoJSON
        folium.GeoJson(
            feature,
            style_function=lambda x: {'fillColor': color_area_wallonie, 'color': color_area_wallonie, 'weight': 1, 'fillOpacity': 0.4},
            control=True
        ).add_to(interreg_layer)
interreg_layer.add_to(m)

for feature in belgium_geojson['features']:
    if feature['properties']['name'] in highlight_area_vlaanderen:  # Modifier la clé selon votre GeoJSON
        folium.GeoJson(
            feature,
            style_function=lambda x: {'fillColor': color_area_vlaanderen, 'color': color_area_vlaanderen, 'weight': 1, 'fillOpacity': 0.4},
            control=True
        ).add_to(interreg_layer)
interreg_layer.add_to(m)

# Ajouter une couche pour les points d'intérêt
points_layer = folium.FeatureGroup(name=point_name, show=True)

for _, row in data.iterrows():
    # Récupérer la couleur et la forme en fonction de la catégorie
    category = row["category"]
    point_info = df_points[df_points["category"] == category].iloc[0]
    color_point = point_info["color"]
    shape = point_info["shape"]

    # Définition du popup avec la structure demandée
    popup_text = f"[{escape(category)}] {escape(row['name'])}<br>{escape(row['url'])}"

    # Ajout du point en fonction de la forme
    if shape == "circle":
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,  # Ajuster la taille en fonction de l'importance
            color=color_point,  # Couleur de bordure
            fill=True,
            fill_color=color_point,  # Couleur de remplissage
            fill_opacity=1,
            popup=popup_text
        ).add_to(points_layer)

    elif shape == "square":
        folium.RegularPolygonMarker(
            location=[row["latitude"], row["longitude"]],
            number_of_sides=4,  # Carré
            radius=6,  # Ajuster la taille
            color=color_point,
            fill=True,
            fill_color=color_point,
            fill_opacity=1,
            popup=popup_text
        ).add_to(points_layer)

    elif shape == "triangle":
        folium.RegularPolygonMarker(
            location=[row["latitude"], row["longitude"]],
            number_of_sides=3,  # Triangle
            radius=6,  # Ajuster la taille
            color=color_point,
            fill=True,
            fill_color=color_point,
            fill_opacity=1,
            popup=popup_text
        ).add_to(points_layer)

points_layer.add_to(m)

# Ajouter une couche pour les clusters
cluster_layer = MarkerCluster(name=cluster_name, show=False)
for _, row in data.iterrows():
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=row["name"]
    ).add_to(cluster_layer)
cluster_layer.add_to(m)




# Préparer les coordonnées des points
coords = data[['latitude', 'longitude']].to_numpy()


# Appliquer DBSCAN pour regrouper les points proches

db = DBSCAN(eps=threshold_radians1/2, min_samples=1, metric='haversine').fit(np.radians(coords))
db2 = DBSCAN(eps=threshold_radians2 / 2, min_samples=1, metric='haversine').fit(np.radians(coords))


# Ajouter une colonne avec les labels des clusters au dataframe
data['cluster'] = db.labels_
data['cluster_2'] = db2.labels_

grouped_points_layer = folium.FeatureGroup(name=threshold_km1_name, show=False)
grouped_points = set()

# Regrouper les points par cluster
for cluster_label in set(data['cluster']):
    cluster_points = data[data['cluster'] == cluster_label]

    if len(cluster_points) > 1:
        # Calculer le centre du cluster
        center_lat = cluster_points['latitude'].mean()
        center_lon = cluster_points['longitude'].mean()

        # Ajouter un grand point pour le cluster
        folium.Circle(
            location=[center_lat, center_lon],
            radius=(len(cluster_points)*impactFactor1*threshold_km1)/2,  # Taille du point regroupé
            color=color_group1,  # Couleur du point regroupé
            fill=True,
            fill_color=color_group1,
            fill_opacity=0.7,
            popup=f"Cluster avec {len(cluster_points)} points"
        ).add_to(grouped_points_layer)

    else:
        # Ajouter les points isolés s'ils ne sont pas dans un cluster
        single_point = cluster_points.iloc[0]
        folium.Circle(
            location=[single_point['latitude'], single_point['longitude']],
            radius=(40)/2,
            color=color_point,
            fill=True,
            fill_color=color_point,
            fill_opacity=0.6,
            popup=f"Point isolé : {single_point['name']}"
        ).add_to(grouped_points_layer)

grouped_points_layer.add_to(m)

# Ajouter une nouvelle couche pour les points regroupés selon le deuxième seuil
grouped_points_layer_2 = folium.FeatureGroup(name=threshold_km2_name, show=False)

# Regrouper les points par cluster pour le deuxième seuil
for cluster_label in set(data['cluster_2']):
    cluster_points = data[data['cluster_2'] == cluster_label]

    if len(cluster_points) > 1:
        # Calculer le centre du cluster
        center_lat = cluster_points['latitude'].mean()
        center_lon = cluster_points['longitude'].mean()

        # Ajouter un grand point pour le cluster
        folium.Circle(
            location=[center_lat, center_lon],
            radius=(len(cluster_points) * impactFactor2*threshold_km2) / 2,  # Taille du point regroupé
            color=color_group2,  # Couleur du point regroupé
            fill=True,
            fill_color=color_group2,
            fill_opacity=0.7,
            popup=f"Cluster avec {len(cluster_points)} points"
        ).add_to(grouped_points_layer_2)
    else:
        # Ajouter les points isolés s'ils ne sont pas dans un cluster
        single_point = cluster_points.iloc[0]
        folium.Circle(
            location=[single_point['latitude'], single_point['longitude']],
            radius=(40) / 2,
            color=color_point,
            fill=True,
            fill_color=color_point,
            fill_opacity=0.6,
            popup=f"Point isolé : {single_point['name']}"
        ).add_to(grouped_points_layer_2)

# Ajouter la couche à la carte
grouped_points_layer_2.add_to(m)

# Ajouter le contrôle des couches
folium.LayerControl().add_to(m)

original_filename = 'result/map'

# Générer le timecode au format désiré
timecode = datetime.datetime.now().strftime("%Y%m%d_%H%M")

# Ajouter le timecode au nom du fichier
filename_with_timecode = original_filename+"_"+timecode+".html"

# Sauvegarder la carte dans un fichier HTML
m.save(filename_with_timecode)

print("Fichier enregistré avec le nom :", filename_with_timecode)
