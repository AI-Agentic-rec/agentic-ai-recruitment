from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = RACINE / "data" / "jeu_de_test" / "candidats" / "candidat_1"

# CV texte (repris du script de génération original pour le candidat 1)
TEXTE_CV = """Youssef AMRANI
Développeur Python
Email : youssef.amrani@exemple-fictif.test | Tél : 0600000001

FORMATION
Licence en Informatique, Universite Ibn Zohr (2023)

EXPÉRIENCE PROFESSIONNELLE
Développeur Python, TechFictive (2023-09 - 2026-09), soit 3 ans
Développement d'API REST et de scripts d'automatisation
Technologies : Python, SQL

COMPÉTENCES
Python, SQL, Git

LANGUES
Français : C1
Anglais : B2
"""


def creer_cv_pdf(chemin, texte):
    doc = SimpleDocTemplate(
        str(chemin), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle("CVNormal", parent=styles["Normal"], fontSize=11, leading=16)
    style_titre = ParagraphStyle("CVTitre", parent=styles["Heading1"], fontSize=16, spaceAfter=8)
    style_section = ParagraphStyle("CVSection", parent=styles["Heading2"], fontSize=12,
                                   spaceBefore=12, spaceAfter=6)

    story = []
    premiere_ligne = True
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne:
            story.append(Spacer(1, 6))
            continue
        if premiere_ligne:
            story.append(Paragraph(ligne, style_titre))
            premiere_ligne = False
        elif ligne.isupper() and len(ligne) < 40:
            story.append(Paragraph(ligne, style_section))
        else:
            story.append(Paragraph(ligne, style_normal))

    doc.build(story)


if __name__ == "__main__":
    chemin_cv = DOSSIER / "cv.pdf"
    creer_cv_pdf(chemin_cv, TEXTE_CV)
    print(f"✅ CV généré : {chemin_cv}")
    print(f"   Taille : {chemin_cv.stat().st_size} octets")