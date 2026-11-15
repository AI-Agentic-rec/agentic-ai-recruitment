from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json

BASE = Path(__file__).parent / "candidats"
BASE.mkdir(parents=True, exist_ok=True)

candidats = [
    {"id": 1, "nom_diplome": "AMRANI", "nom_cin": "AMRANI", "prenom": "Youssef",
     "date_naissance": "12/04/2000", "diplome": "Licence Informatique",
     "etablissement": "Universite Ibn Zohr", "annee": "2023", "expiration": "15/06/2030"},
    {"id": 2, "nom_diplome": "BENALI", "nom_cin": "BENALI", "prenom": "Sara",
     "date_naissance": "20/08/2001", "diplome": "Master Data Science",
     "etablissement": "Universite Hassan II", "annee": "2025", "expiration": "10/01/2031"},
    {"id": 3, "nom_diplome": "EL FASSI", "nom_cin": "EL FASSI", "prenom": "Mohamed Amine",
     "date_naissance": "03/02/1999", "diplome": "Licence Mathematiques",
     "etablissement": "Universite Cadi Ayyad", "annee": "2022", "expiration": "11/03/2030"},
    {"id": 4, "nom_diplome": "BENSAID", "nom_cin": "BENSAID", "prenom": "Nour El Houda",
     "date_naissance": "14/11/2000", "diplome": "Master Informatique",
     "etablissement": "Universite Ibn Tofail", "annee": "2024", "expiration": "12/09/2030"},
    {"id": 5, "nom_diplome": "TAZI", "nom_cin": "TAZI", "prenom": "Imane",
     "date_naissance": "05/05/2002", "diplome": "Licence Gestion",
     "etablissement": "Universite Mohammed V", "annee": "2024", "expiration": "20/04/2031"},
    {"id": 6, "nom_diplome": "HADDAD", "nom_cin": "HADDAD", "prenom": "Adam",
     "date_naissance": "18/07/2001", "diplome": "Bachelor Computer Science",
     "etablissement": "International University", "annee": "2025", "expiration": "15/02/2031"},
    {"id": 7, "nom_diplome": "OUAZZANI ALAMI", "nom_cin": "OUAZZANI", "prenom": "Salma",
     "date_naissance": "21/09/2000", "diplome": "Master Intelligence Artificielle",
     "etablissement": "Universite Ibn Zohr", "annee": "2025", "expiration": "17/08/2030"},
    {"id": 8, "nom_diplome": "CHERKAOUI", "nom_cin": "CHERKAOUI", "prenom": "Anas",
     "date_naissance": "09/12/1998", "diplome": "Licence Economie",
     "etablissement": "Universite Hassan II", "annee": "2021", "expiration": "01/01/2023"},
    {"id": 9, "nom_diplome": "LAHLOU", "nom_cin": "LAHLOU", "prenom": "Meryem",
     "date_naissance": "16/06/2001", "diplome": "Master Big Data",
     "etablissement": "Universite Cadi Ayyad", "annee": "2025", "expiration": "14/07/2031",
     "flou": 2.5},
    {"id": 10, "nom_diplome": "EL IDRISSI", "nom_cin": "EL IDRISSI", "prenom": "Hamza",
     "date_naissance": "25/01/2000", "diplome": "Licence",
     "etablissement": "", "annee": "", "expiration": "19/10/2030"},

    # ---------------- CAS DURS ----------------
    # 11 : diplôme très flou
    {"id": 11, "nom_diplome": "ZIANI", "nom_cin": "ZIANI", "prenom": "Karim",
     "date_naissance": "07/03/2000", "diplome": "Licence Informatique",
     "etablissement": "Universite Mohammed V", "annee": "2023", "expiration": "22/05/2031",
     "flou": 7},
    # 12 : CIN absente (aucun fichier cin.jpg)
    {"id": 12, "nom_diplome": "SEBTI", "nom_cin": "SEBTI", "prenom": "Lina",
     "date_naissance": "11/10/2001", "diplome": "Master Finance",
     "etablissement": "Universite Hassan II", "annee": "2025", "expiration": "03/09/2031",
     "cin_absente": True},
    # 13 : la CIN affiche KABBAI au lieu de KABBAJ (faute de lecture / de saisie)
    {"id": 13, "nom_diplome": "KABBAJ", "nom_cin": "KABBAI", "nom_cv": "KABBAJ",
     "prenom": "Rim", "date_naissance": "30/04/2000", "diplome": "Licence Economie",
     "etablissement": "Universite Cadi Ayyad", "annee": "2023", "expiration": "18/11/2031"},
    # 14 : le CV contredit le diplome (autre etablissement, autre annee)
    {"id": 14, "nom_diplome": "NACIRI", "nom_cin": "NACIRI", "prenom": "Omar",
     "date_naissance": "02/08/1999", "diplome": "Master Informatique",
     "etablissement": "Universite Ibn Tofail", "annee": "2024", "expiration": "09/12/2030",
     "cv_formation": {"diplome": "Master Informatique",
                      "etablissement": "Universite Mohammed V", "date_fin": "2022"}},
]

TOUS_NIVEAUX = ["conforme", "partiellement_conforme", "non_conforme"]

# Résultats attendus par scénario (utilisés par run_test.py).
SCENARIOS = {
    7: {"scenario": "Nom du diplome (OUAZZANI ALAMI) different de la CIN (OUAZZANI)",
        "niveaux_acceptes": ["partiellement_conforme", "non_conforme"],
        "signal_documents": ["diplome", "cin"]},
    8: {"scenario": "CIN expiree",
        "niveaux_acceptes": ["non_conforme"],
        "signal_mots_cles": ["expir"]},
    9: {"scenario": "Diplome flou leger (pas de valeur inventee)",
        "niveaux_acceptes": ["conforme", "partiellement_conforme"],
        "flou": True},
    10: {"scenario": "Informations du diplome manquantes (etablissement et annee)",
         "niveaux_acceptes": ["partiellement_conforme", "non_conforme"],
         "signal_mots_cles": ["absente"]},
    11: {"scenario": "Diplome tres flou : null accepte, valeur inventee interdite",
         "niveaux_acceptes": TOUS_NIVEAUX,
         "flou": True},
    12: {"scenario": "CIN absente",
         "niveaux_acceptes": ["non_conforme"],
         "cin_absente": True,
         "signal_mots_cles": ["manquant"]},
    13: {"scenario": "Faute dans le nom de la CIN (KABBAI / KABBAJ) : gravite faible",
         "niveaux_acceptes": ["partiellement_conforme", "conforme"],
         "signal_gravite": "faible"},
    14: {"scenario": "CV different du diplome (etablissement et annee)",
         "niveaux_acceptes": ["partiellement_conforme", "non_conforme"],
         "signal_mots_cles": ["etablissement", "annee"]},
}
PAR_DEFAUT = {"scenario": "Documents fictifs conformes",
              "niveaux_acceptes": ["conforme"]}


def charger_police(taille):
    for chemin in (
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(chemin, taille)
        except OSError:
            continue
    return ImageFont.load_default()


title_font = charger_police(38)
text_font = charger_police(27)
small_font = charger_police(20)


def creer_document(titre, lignes, chemin, flou=0):
    img = Image.new("RGB", (1200, 800), "#F7F7F7")
    draw = ImageDraw.Draw(img)

    draw.rectangle((20, 20, 1180, 780), outline="#222222", width=4)
    draw.text((60, 50), "DOCUMENT FICTIF - SPECIMEN", fill="red", font=small_font)
    draw.text((60, 120), titre, fill="#123456", font=title_font)
    draw.line((60, 185, 1140, 185), fill="#555555", width=3)

    y = 240
    for ligne in lignes:
        draw.text((70, y), ligne, fill="#222222", font=text_font)
        y += 75

    draw.text((60, 720), "Document de test - Aucune valeur officielle",
              fill="red", font=small_font)

    if flou:
        img = img.filter(ImageFilter.GaussianBlur(radius=flou))

    img.save(chemin, quality=90)


for c in candidats:
    dossier = BASE / f"candidat_{c['id']}"
    dossier.mkdir(exist_ok=True)

    # Nettoyage si on relance (ex. cin.jpg d'une ancienne version)
    for ancien in ("cin.jpg",):
        if c.get("cin_absente") and (dossier / ancien).exists():
            (dossier / ancien).unlink()

    # --- Diplôme ---
    creer_document(
        "ATTESTATION DE DIPLOME",
        [
            f"Nom : {c['nom_diplome']}",
            f"Prenom : {c['prenom']}",
            f"Diplome : {c['diplome']}",
            f"Etablissement : {c['etablissement'] or 'NON RENSEIGNE'}",
            f"Annee : {c['annee'] or 'NON RENSEIGNE'}",
        ],
        dossier / "diplome.jpg",
        flou=c.get("flou", 0),
    )

    # --- CIN fictive (absente pour le candidat 12) ---
    if not c.get("cin_absente"):
        creer_document(
            "CARTE D'IDENTITE",
            [
                f"Nom : {c['nom_cin']}",
                f"Prenom : {c['prenom']}",
                f"Date de naissance : {c['date_naissance']}",
                f"Numero : TEST-CIN-{c['id']:03d}",
                f"Expiration : {c['expiration']}",
            ],
            dossier / "cin.jpg",
        )

    # --- Profil CV (entrée de l'agent 3) ---
    formation = {
        "diplome": c["diplome"],
        "specialite": None,
        "etablissement": c["etablissement"] or None,
        "date_fin": c["annee"] or None,
    }
    formation.update(c.get("cv_formation", {}))

    profil_cv = {
        "nom": c.get("nom_cv", c["nom_cin"]),
        "prenom": c["prenom"],
        "formations": [formation],
    }
    with open(dossier / "profil_cv.json", "w", encoding="utf-8") as f:
        json.dump(profil_cv, f, indent=4, ensure_ascii=False)

    # --- Vérité terrain (ce qui est AFFICHÉ sur les documents) ---
    attendu = SCENARIOS.get(c["id"], PAR_DEFAUT)
    ground_truth = {
        "candidat_id": c["id"],
        "nom_diplome": c["nom_diplome"],
        "nom_cin": c["nom_cin"],
        "prenom": c["prenom"],
        "date_naissance": c["date_naissance"],
        "diplome": c["diplome"],
        "etablissement": c["etablissement"] or None,
        "annee_obtention": c["annee"] or None,
        "date_expiration_cin": c["expiration"],
        **attendu,
    }
    with open(dossier / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=4, ensure_ascii=False)

print("Jeu de donnees genere avec succes !")
print(f"Nombre de candidats : {len(candidats)}")
print(f"Dossier : {BASE.resolve()}")