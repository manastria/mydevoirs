#!/usr/bin/env python3
"""Vérifie le site avant publication (lancé par .github/workflows/publier-site.yml).

Cinq contrôles :
  1. tous les fichiers liés par les pages existent bien dans site/ ;
  2. toutes les ancres internes (#...) correspondent à un identifiant de la page ;
  3. les pages ne chargent aucune ressource extérieure (polices comprises) : le site
     doit rester consultable sans dépendre d'un autre serveur ;
  4. les fichiers de preuve de propriété (Google Search Console) sont bien formés ;
  5. sitemap.xml est valide et ne liste que des pages réellement publiées.

Aucune dépendance : bibliothèque standard Python uniquement.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SITE = pathlib.Path(__file__).resolve().parent
SITE_URL = "https://mydevoirs.manastria.fr/"
erreurs = []

# Les pages du site : tous les .html, sauf les fichiers de preuve de propriété (googleXXXX.html).
PAGES = sorted(f for f in SITE.glob("*.html") if not f.name.startswith("google"))
css = (SITE / "assets" / "site.css").read_text(encoding="utf-8")
polices = [f"assets/{u}" for u in re.findall(r"url\(([^)]+)\)", css)]
if re.search(r"url\(\s*['\"]?https?://", css):
    erreurs.append("la feuille de style charge une ressource extérieure")

nb_liens = nb_apercu = 0
for page in PAGES:
    html = page.read_text(encoding="utf-8")
    nom = page.name

    # Les ressources chargées par la page : href des feuilles de style et des icônes, src des images.
    liens = re.findall(r'(?:href|src)="([^"]+)"', html)
    nb_liens += len(liens)

    # L'image d'aperçu de partage (og:image) est donnée en URL absolue : on vérifie quand même
    # que le fichier correspondant est bien présent dans le site.
    apercu = [u[len(SITE_URL):] for u in re.findall(r'content="(https?://[^"]+)"', html)
              if u.startswith(SITE_URL) and not u.endswith("/") and not u.endswith(".html")]
    nb_apercu += len(apercu)

    # 1. Les fichiers locaux existent (une ancre éventuelle, page.html#id, est ignorée ici).
    for cible in liens + apercu:
        if cible.startswith(("http://", "https://", "#", "mailto:", "data:")):
            continue
        if not (SITE / cible.split("#")[0]).exists():
            erreurs.append(f"{nom} : fichier manquant, {cible}")

    # 2. Les ancres internes pointent vers un identifiant existant.
    ids = set(re.findall(r'id="([^"]+)"', html))
    for cible in liens:
        if cible.startswith("#") and cible[1:] not in ids:
            erreurs.append(f"{nom} : ancre introuvable, {cible}")

    # 3. Rien n'est chargé depuis l'extérieur. Sont exclus les liens de navigation (<a href>) et
    # les métadonnées (URL canonique, aperçu de partage), qui doivent justement être absolues.
    for balise in re.findall(r"<(?:link|script|img|iframe)\b[^>]*>", html):
        if re.search(r'rel="canonical"', balise):
            continue
        for url in re.findall(r'(?:href|src)="(https?://[^"]+)"', balise):
            erreurs.append(f"{nom} : ressource extérieure chargée, {url}")

for cible in polices:
    if not (SITE / cible).exists():
        erreurs.append(f"fichier manquant : {cible}")

# 4. Preuve de propriété (Google Search Console) : le fichier googleXXXX.html doit contenir
# exactement « google-site-verification: <son propre nom> », sans quoi Google refuse la validation.
preuves = sorted(SITE.glob("google*.html"))
for f in preuves:
    attendu = f"google-site-verification: {f.name}"
    if f.read_text(encoding="utf-8").strip() != attendu:
        erreurs.append(f"preuve de propriété mal formée : {f.name} devrait contenir « {attendu} »")

# 5. Plan du site : XML valide, URL absolues sous SITE_URL, et chaque page listée existe.
# Une URL terminée par « / » désigne le index.html du dossier correspondant.
SM = SITE / "sitemap.xml"
pages = []
if not SM.exists():
    erreurs.append("sitemap.xml est absent")
else:
    try:
        racine = ET.fromstring(SM.read_text(encoding="utf-8"))
    except ET.ParseError as e:
        erreurs.append(f"sitemap.xml illisible : {e}")
    else:
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        if racine.tag != ns + "urlset":
            erreurs.append("sitemap.xml : la balise racine devrait être <urlset>")
        pages = [(loc.text or "").strip() for loc in racine.iter(ns + "loc")]
        if not pages:
            erreurs.append("sitemap.xml ne liste aucune page")
        for url in pages:
            if not url.startswith(SITE_URL):
                erreurs.append(f"sitemap.xml : URL hors du site, {url}")
                continue
            fichier = url[len(SITE_URL):] or "index.html"
            if fichier.endswith("/"):
                fichier += "index.html"
            if not (SITE / fichier).exists():
                erreurs.append(f"sitemap.xml : page listée mais absente, {url}")
        if SITE_URL not in pages:
            erreurs.append(f"sitemap.xml : la page d'accueil {SITE_URL} devrait y figurer")

if erreurs:
    print("\n".join(f"ERREUR : {e}" for e in erreurs))
    sys.exit(1)
print(f"Site vérifié : {len(PAGES)} page(s), {nb_liens} liens, {len(polices)} polices, {nb_apercu} image(s) d'aperçu, "
      f"{len(preuves)} preuve(s) de propriété, {len(pages)} page(s) au sitemap, "
      "aucune ressource extérieure.")
