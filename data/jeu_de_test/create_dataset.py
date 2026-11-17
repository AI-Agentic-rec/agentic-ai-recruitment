from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json
import re
import unicodedata

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
    # 12 : CIN absente
    {"id": 12, "nom_diplome": "SEBTI", "nom_cin": "SEBTI", "prenom": "Lina",
     "date_naissance": "11/10/2001", "diplome": "Master Finance",
     "etablissement": "Universite Hassan II", "annee": "2025", "expiration": "03/09/2031",
     "cin_absente": True},
    # 13 : CIN affiche KABBAI au lieu de KABBAJ
    {"id": 13, "nom_diplome": "KABBAJ", "nom_cin": "KABBAI", "nom_cv": "KABBAJ",
     "prenom": "Rim", "date_naissance": "30/04/2000", "diplome": "Licence Economie",
     "etablissement": "Universite Cadi Ayyad", "annee": "2023", "expiration": "18/11/2031"},
    # 14 : CV contredit le diplôme
    {"id": 14, "nom_diplome": "NACIRI", "nom_cin": "NACIRI", "prenom": "Omar",
     "date_naissance": "02/08/1999", "diplome": "Master Informatique",
     "etablissement": "Universite Ibn Tofail", "annee": "2024", "expiration": "09/12/2030",
     "cv_formation": {"diplome": "Master Informatique",
                      "etablissement": "Universite Mohammed V", "date_fin": "2022"}},
]

TOUS_NIVEAUX = ["conforme", "partiellement_conforme", "non_conforme"]

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


# =============================================================================
# GÉNÉRATION DES IMAGES (diplôme et CIN)
# =============================================================================

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


# =============================================================================
# GÉNÉRATION DU CV EN PDF (pour l'agent 2 qui lit PDF/DOCX)
# =============================================================================

def creer_cv_pdf(chemin, texte):
    """Génère un CV PDF simple à partir d'un texte multi-lignes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    doc = SimpleDocTemplate(
        str(chemin), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        "CVNormal", parent=styles["Normal"], fontSize=11, leading=16,
    )
    style_titre = ParagraphStyle(
        "CVTitre", parent=styles["Heading1"], fontSize=16, spaceAfter=8,
    )
    style_section = ParagraphStyle(
        "CVSection", parent=styles["Heading2"], fontSize=12,
        spaceBefore=12, spaceAfter=6,
    )

    story = []
    premiere_ligne = True
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne:
            story.append(Spacer(1, 6))
            continue
        # Titre = première ligne
        if premiere_ligne:
            story.append(Paragraph(ligne, style_titre))
            premiere_ligne = False
        # Sections en MAJUSCULES courtes
        elif ligne.isupper() and len(ligne) < 40:
            story.append(Paragraph(ligne, style_section))
        else:
            story.append(Paragraph(ligne, style_normal))

    doc.build(story)


# =============================================================================
# CV TEXTE ET ATTENDU (pour tester l'agent 2)
# =============================================================================

EXPERIENCE = {
    "poste": "Développeur Python", "entreprise": "TechFictive",
    "description": "Développement d'API REST et de scripts d'automatisation",
    "date_debut": "2023-09", "date_fin": "2026-09", "duree_annees": 3.0,
    "competences": ["Python", "SQL"],
}
COMPETENCES = ["Python", "SQL", "Git"]
LANGUES = [{"langue": "Français", "niveau": "C1"}, {"langue": "Anglais", "niveau": "B2"}]


def _ascii(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def ecrire_cv(dossier, c):
    """cv.pdf (entrée de l'agent 2) et cv_attendu.json (sortie attendue de l'agent 2)."""
    nom = c.get("nom_cv", c["nom_cin"])
    prenom = c["prenom"]
    formation = {"diplome": c["diplome"], "etablissement": c["etablissement"] or None,
                 "date_fin": c["annee"] or None}
    formation.update(c.get("cv_formation", {}))

    mots = formation["diplome"].split(" ", 1)
    type_diplome = mots[0]
    specialite = mots[1] if len(mots) > 1 else None

    email = f"{_ascii(prenom).replace(' ', '-')}.{_ascii(nom).replace(' ', '-')}@exemple-fictif.test"
    telephone = f"06000000{c['id']:02d}"

    libelle = f"{type_diplome} en {specialite}" if specialite else type_diplome
    ligne_formation = libelle
    if formation["etablissement"]:
        ligne_formation += f", {formation['etablissement']}"
    if formation["date_fin"]:
        ligne_formation += f" ({formation['date_fin']})"

    texte = f"""{prenom} {nom.upper()}
Développeur Python
Email : {email} | Tél : {telephone}

FORMATION
{ligne_formation}

EXPÉRIENCE PROFESSIONNELLE
{EXPERIENCE['poste']}, {EXPERIENCE['entreprise']} (2023-09 - 2026-09), soit 3 ans
{EXPERIENCE['description']}
Technologies : {", ".join(EXPERIENCE['competences'])}

COMPÉTENCES
{", ".join(COMPETENCES)}

LANGUES
Français : C1
Anglais : B2
"""
    attendu = {
        "nom": nom, "prenom": prenom, "email": email, "telephone": telephone,
        "formations": [{"diplome": type_diplome, "specialite": specialite,
                        "etablissement": formation["etablissement"],
                        "date_debut": None, "date_fin": formation["date_fin"]}],
        "experiences": [EXPERIENCE],
        "competences": COMPETENCES, "langues": LANGUES, "certifications": [],
        "experience_totale_annees": 3.0,
    }

    # CV en PDF (lu par lire_cv)
    creer_cv_pdf(dossier / "cv.pdf", texte)

    with open(dossier / "cv_attendu.json", "w", encoding="utf-8") as f:
        json.dump(attendu, f, indent=4, ensure_ascii=False)


# =============================================================================
# OFFRES (5 offres en .txt pour tester l'agent 1)
# =============================================================================

def ecrire_offres():
    """Génère 5 offres variées en .txt pour tester l'agent 1."""
    dossier = BASE / "offres"
    dossier.mkdir(exist_ok=True)

    offres = [
        # --- Offre 1 : nominale ---
        {
            "id": 1,
            "texte": """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Développeur Python

Missions
- Développer des API REST
- Maintenir les scripts d'automatisation

Profil recherché
- Licence en informatique ou équivalent
- Minimum 2 ans d'expérience

Compétences requises
Python, SQL, Docker

Compétences appréciées
Git

Langues
Anglais niveau B2
""",
            "attendu": {
                "titre_poste": "Développeur Python",
                "diplome_demande": "Licence",
                "niveau_diplome_min": 3,
                "experience_min_annees": 2,
                "competences_obligatoires": ["Python", "SQL", "Docker"],
                "competences_souhaitees": ["Git"],
                "langues": [{"langue": "Anglais", "niveau": "B2"}],
                "missions": ["Développer des API REST",
                             "Maintenir les scripts d'automatisation"],
            },
        },
        # --- Offre 2 : Bac+5 exigé ---
        {
            "id": 2,
            "texte": """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Data Scientist Senior

Missions
- Concevoir des modèles de machine learning
- Analyser de grands volumes de données

Profil recherché
- Master en data science ou équivalent
- Minimum 3 ans d'expérience

Compétences requises
Python, Machine Learning, SQL

Compétences appréciées
TensorFlow, Spark

Langues
Anglais niveau C1
Français courant
""",
            "attendu": {
                "titre_poste": "Data Scientist Senior",
                "diplome_demande": "Master",
                "niveau_diplome_min": 5,
                "experience_min_annees": 3,
                "competences_obligatoires": ["Python", "Machine Learning", "SQL"],
                "competences_souhaitees": ["TensorFlow", "Spark"],
                "langues": [{"langue": "Anglais", "niveau": "C1"},
                            {"langue": "Français", "niveau": "courant"}],
                "missions": ["Concevoir des modèles de machine learning",
                             "Analyser de grands volumes de données"],
            },
        },
        # --- Offre 3 : sans diplôme ni expérience ---
        {
            "id": 3,
            "texte": """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Stagiaire Développeur Web

Missions
- Participer au développement front-end

Compétences requises
HTML, CSS, JavaScript

Compétences appréciées
React

Langues
Français
""",
            "attendu": {
                "titre_poste": "Stagiaire Développeur Web",
                "diplome_demande": None,
                "niveau_diplome_min": None,
                "experience_min_annees": 0,
                "competences_obligatoires": ["HTML", "CSS", "JavaScript"],
                "competences_souhaitees": ["React"],
                "langues": [{"langue": "Français", "niveau": None}],
                "missions": ["Participer au développement front-end"],
            },
        },
        # --- Offre 4 : souhaitées seulement, Bac+5, 5 ans ---
        {
            "id": 4,
            "texte": """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Ingénieur DevOps

Missions
- Automatiser les déploiements
- Gérer l'infrastructure cloud

Profil recherché
- Bac+5 en informatique
- 5 ans d'expérience minimum

Compétences appréciées
Docker, Kubernetes, Terraform, AWS

Langues
Anglais courant
""",
            "attendu": {
                "titre_poste": "Ingénieur DevOps",
                "diplome_demande": "Bac+5",
                "niveau_diplome_min": 5,
                "experience_min_annees": 5,
                "competences_obligatoires": [],
                "competences_souhaitees": ["Docker", "Kubernetes", "Terraform", "AWS"],
                "langues": [{"langue": "Anglais", "niveau": "courant"}],
                "missions": ["Automatiser les déploiements",
                             "Gérer l'infrastructure cloud"],
            },
        },
        # --- Offre 5 : minimaliste ---
        {
            "id": 5,
            "texte": """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Assistant Administratif

Missions
- Gérer les dossiers
""",
            "attendu": {
                "titre_poste": "Assistant Administratif",
                "diplome_demande": None,
                "niveau_diplome_min": None,
                "experience_min_annees": 0,
                "competences_obligatoires": [],
                "competences_souhaitees": [],
                "langues": [],
                "missions": ["Gérer les dossiers"],
            },
        },
    ]

    for o in offres:
        (dossier / f"offre_{o['id']}.txt").write_text(o["texte"], encoding="utf-8")
        with open(dossier / f"offre_{o['id']}_attendue.json", "w", encoding="utf-8") as f:
            json.dump(o["attendu"], f, indent=4, ensure_ascii=False)

    # Compatibilité avec run_test_agents_3_4.py existant
    (BASE / "offre.txt").write_text(offres[0]["texte"], encoding="utf-8")
    with open(BASE / "offre_attendue.json", "w", encoding="utf-8") as f:
        json.dump(offres[0]["attendu"], f, indent=4, ensure_ascii=False)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

for c in candidats:
    dossier = BASE / f"candidat_{c['id']}"
    dossier.mkdir(exist_ok=True)

    # Nettoyage des anciens fichiers (ancien cv.txt, cin.jpg orpheline)
    for ancien in ("cv.txt", "cin.jpg"):
        if ancien == "cin.jpg" and not c.get("cin_absente"):
            continue
        if (dossier / ancien).exists():
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

    # --- CIN (absente pour le candidat 12) ---
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

    # --- Profil CV simplifié (entrée de l'agent 3) ---
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

    # --- Vérité terrain ---
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

    # --- CV PDF + CV attendu ---
    ecrire_cv(dossier, c)

# --- Offres en .txt ---
ecrire_offres()

print("Jeu de donnees genere avec succes !")
print(f"Nombre de candidats : {len(candidats)}")
print(f"Nombre d'offres : 5 (dans candidats/offres/)")
print(f"Dossier : {BASE.resolve()}")