"""Agent 2 — CV Extraction Agent.
Entrée : le texte d'un CV.
Sortie : un ProfilCandidat validé par Pydantic.
"""

import re
from pathlib import Path

from .calculs import completer_profil
from .lecture_documents import lire_cv
from agents.common.llm_local import executer_agent
from agents.common.schemas import ProfilCandidat


SYSTEM = """Tu es le CV Extraction Agent d'une plateforme de recrutement.

Ta seule tâche : extraire fidèlement les informations d'un CV et les structurer.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide.
- N'invente rien et ne déduis rien.
- Information absente = null (champ simple) ou [] (liste).
- "nom" = nom de famille ; "prenom" = prénom.
- "email" et "telephone" tels qu'écrits.

- "formations" : une entrée par diplôme.
  « diplome » = TYPE de diplôme seulement, parmi :
    Licence, Master, Doctorat, Ingénieur d'État, DUT, BTS,
    Bachelor, Baccalauréat, DEUG.
  « specialite » = le domaine d'études
    (Informatique, Gestion, Mathématiques, Data Science,
    Finance, Économie, Physique, etc.).
  « etablissement » = l'université ou l'école.

  ATTENTION aux dates de FORMATION :
  « date_fin » = année d'obtention du diplôme
    (c'est la date qui est écrite sur le CV, souvent
    entre parenthèses après le nom du diplôme).
  « date_debut » = début des études, RAREMENT écrit
    sur un CV. Dans 95% des cas, date_debut = null.

  Exemples :
    « Licence en Informatique, Université Ibn Zohr (2023) »
      → diplome="Licence", specialite="Informatique",
        etablissement="Université Ibn Zohr",
        date_debut=null, date_fin="2023"
    « Master Data Science, Université Hassan II (2025) »
      → diplome="Master", specialite="Data Science",
        etablissement="Université Hassan II",
        date_debut=null, date_fin="2025"
    « Licence » (seul)
      → diplome="Licence", specialite=null,
        date_debut=null, date_fin=null

- "experiences" : une entrée par poste ou stage :
  poste, entreprise, description (UNE phrase courte),
  date_debut, date_fin, competences.

  ATTENTION aux dates d'EXPÉRIENCE :
  « date_debut » = date de début du poste (la première).
  « date_fin » = date de fin du poste (la deuxième).
  Si le CV écrit « 2023-09 - 2026-09 », alors
    date_debut="2023-09" ET date_fin="2026-09".
  Si le CV écrit « 2023-09 - présent » ou
    « 2023-09 - aujourd'hui », alors date_fin=null.
  Ne renvoie JAMAIS date_fin=null si une date de fin
    explicite est écrite dans le CV.

- DATES : format AAAA-MM obligatoire.
  « septembre 2023 » → "2023-09"
  « sept. 2023 » → "2023-09"
  « 09/2023 » → "2023-09"
  « mars 2021 » → "2021-03"
  « 03/2021 » → "2021-03"
  Si seule l'année est écrite : "AAAA" (ex. "2023").

- "duree_annees" de chaque expérience = null.
- "experience_totale_annees" = 0.
  Le programme calcule ces valeurs lui-même.

- "competences" : EXTRAIS OBLIGATOIREMENT toutes les
  compétences listées dans le CV, y compris :
  * celles de la section « Compétences » du CV
    (liste dédiée, souvent en fin de CV)
  * celles mentionnées dans les expériences
  Si le CV contient une section « Compétences » (ou
  « COMPÉTENCES », « Skills », « Technical Skills »),
  tu DOIS la lire et l'extraire. Ne renvoie JAMAIS []
  quand cette section existe et contient au moins un terme.
  Termes courts et normalisés, sans doublons.

- "langues" : objets {"langue": "...", "niveau": null}.
  Le niveau est recopié uniquement s'il est écrit.

- "certifications" : certificats et attestations hors diplômes
  universitaires.

Respecte exactement le schéma Pydantic fourni.
"""


# =============================================================================
# POST-TRAITEMENT DÉTERMINISTE (le LLM ne décide plus pour les dates)
# =============================================================================

def _corriger_dates_experiences(profil: ProfilCandidat, texte_cv: str) -> ProfilCandidat:
    """
    Corrige date_fin des expériences à partir du texte brut du CV.
    Le LLM met parfois date_fin=null quand une date explicite existe
    (ex. « 2023-09 - 2026-09 »). On relit le texte pour la retrouver.
    """
    # Motif : "AAAA-MM - AAAA-MM" ou "AAAA - AAAA" ou "AAAA-MM à AAAA-MM"
    motif = re.compile(
        r"((?:19|20)\d{2}(?:-\d{2})?)\s*[-–à]+\s*((?:19|20)\d{2}(?:-\d{2})?)"
    )
    paires = motif.findall(texte_cv)

    for exp in profil.experiences:
        if exp.date_fin is not None:
            continue  # déjà rempli, on ne touche pas
        if not exp.date_debut:
            continue

        # Cherche la paire qui correspond au date_debut de l'expérience
        debut_exp = str(exp.date_debut).strip()
        for debut, fin in paires:
            if debut.strip() == debut_exp:
                exp.date_fin = fin.strip()
                break

    return profil


# =============================================================================
# AGENT
# =============================================================================

def cv_extraction_agent(
    texte_cv: str,
    essais: int = 3
) -> ProfilCandidat:

    profil = executer_agent(
        numero_agent=2,
        system_prompt=SYSTEM,
        message=f"Voici le contenu du CV à analyser :\n\n{texte_cv}",
        schema=ProfilCandidat,
        max_essais=essais
    )

    # Post-traitement : le code corrige ce que le LLM n'a pas su faire
    profil = _corriger_dates_experiences(profil, texte_cv)

    return completer_profil(profil)


def extraire_profil_depuis_fichier(chemin) -> ProfilCandidat:
    """Lit un CV PDF/DOCX puis lance l'Agent 2."""

    texte = lire_cv(Path(chemin))

    return cv_extraction_agent(texte)