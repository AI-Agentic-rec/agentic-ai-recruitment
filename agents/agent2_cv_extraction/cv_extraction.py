"""Agent 2 — CV Extraction Agent.
Entrée : le texte d'un CV.
Sortie : un ProfilCandidat validé par Pydantic.
"""

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .calculs import MOIS, completer_profil
from .lecture_documents import lire_cv
from agents.common.llm_local import executer_agent
from agents.common.schemas import Experience, Formation, ProfilCandidat


SYSTEM = """Tu es le CV Extraction Agent d'une plateforme de recrutement.

Ta tâche : extraire fidèlement les informations d'un CV et les structurer selon le schéma JSON demandé.
Inclus toujours toutes les clés attendues du schéma, y compris "formations" et "experiences".

Règles générales :
- Réponds UNIQUEMENT avec un objet JSON valide.
- N'invente rien et ne déduis rien.
- Information absente = null (champ simple) ou [] (liste).
- "nom" = nom de famille ; "prenom" = prénom.
- "email" et "telephone" tels qu'écrits.

- "formations" : OBLIGATOIRE dès qu'une formation ou un diplôme figure dans le CV (même si la mise en page est sur plusieurs lignes ou utilise des séparateurs comme '|').
  Chaque élément est un objet avec :
  - "diplome" : intitulé / type de diplôme (ex. "Master en Génie Logiciel", "Licence en Informatique", "Master", "Licence", "Ingénieur d'État", "DUT", "BTS", "Bachelor", "Baccalauréat").
  - "specialite" : domaine d'études si précisé (ex. "Génie Logiciel", "Informatique", "Data Science"), sinon null.
  - "etablissement" : nom de l'école ou de l'université, sinon null.
  - "date_debut" : début si indiqué (AAAA ou AAAA-MM), sinon null.
  - "date_fin" : année ou mois/année de fin si indiqué (AAAA ou AAAA-MM), sinon null.

- "experiences" : OBLIGATOIRE dès qu'une expérience professionnelle ou un stage figure dans le CV.
  Chaque élément est un objet avec :
  - "poste" : intitulé du poste ou du stage.
  - "entreprise" : nom de l'entreprise ou de l'organisation, sinon null.
  - "description" : résumé court (1 à 2 phrases) des missions réalisées, sinon null.
  - "date_debut" : date de début (AAAA-MM ou AAAA), sinon null.
  - "date_fin" : date de fin (AAAA-MM ou AAAA). Si le poste est en cours ("Présent", "Aujourd'hui", "En cours"), mettre null.
  - "duree_annees" : null (calculé automatiquement ensuite).
  - "competences" : liste des compétences techniques liées à cette expérience (sinon []).

- DATES : format "AAAA-MM" quand le mois est connu, sinon "AAAA".
  Exemples :
  - « septembre 2023 » / « sept. 2023 » / « 09/2023 » → "2023-09"
  - « janv. 2023 » → "2023-01"
  - « févr. 2022 » → "2022-02"
  - « déc. 2022 » → "2022-12"
  - « 2020 – 2022 » → date_debut="2020", date_fin="2022"

- "competences" : extrais toutes les compétences listées dans le CV (sections dédiées et expériences), sans doublons.

- "langues" : liste d'objets {"langue": "...", "niveau": ...}. Le niveau est recopié uniquement s'il est écrit, sinon null.

- "certifications" : liste des certificats ou attestations hors diplômes académiques.
"""


class _ExtractionFormations(BaseModel):
    model_config = ConfigDict(extra="forbid")
    formations: list[Formation] = Field(default_factory=list)


class _ExtractionExperiences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experiences: list[Experience] = Field(default_factory=list)


_SYSTEM_FORMATIONS = """Extrais uniquement la liste des formations et diplômes présents dans le texte du CV.
Réponds UNIQUEMENT avec un JSON valide respectant le schéma demandé.
Pour chaque diplôme, renseigne "diplome" (ex. "Master en Génie Logiciel", "Licence en Informatique"),
"specialite", "etablissement", "date_debut" (AAAA ou AAAA-MM ou null) et "date_fin" (AAAA ou AAAA-MM ou null).
N'invente rien."""


_SYSTEM_EXPERIENCES = """Extrais uniquement la liste des expériences professionnelles et stages présents dans le texte du CV.
Réponds UNIQUEMENT avec un JSON valide respectant le schéma demandé.
Pour chaque expérience, renseigne "poste", "entreprise", "description" (courte),
"date_debut" (AAAA-MM ou AAAA ou null), "date_fin" (AAAA-MM ou AAAA ou null si poste actuel / "Présent"),
"duree_annees": null et "competences" (liste de chaînes).
N'invente rien."""


_NOMS_MOIS_PATTERN = "|".join(
    sorted((re.escape(k) for k in MOIS.keys()), key=len, reverse=True)
)
_BORNE_DATE_PATTERN = rf"(?:(?:19|20)\d{{2}}(?:[-/.]\d{{1,2}})?|\b\d{{1,2}}[-/.](?:19|20)\d{{2}}\b|\b(?:{_NOMS_MOIS_PATTERN})\.?\s+(?:19|20)\d{{2}}\b)"


def _normaliser_borne_vers_iso(borne: str) -> str | None:
    """Convertit une borne extraite du texte brut en AAAA-MM ou AAAA si possible."""
    t = borne.strip().lower()
    m = re.search(r"((?:19|20)\d{2})[-/.](\d{1,2})", t)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.search(r"\b(\d{1,2})[-/.]((?:19|20)\d{2})\b", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    a = re.search(r"(?:19|20)\d{2}", t)
    if not a:
        return None
    for nom, num in MOIS.items():
        if re.search(rf"\b{re.escape(nom)}\b", t):
            return f"{a.group(0)}-{num:02d}"
    return a.group(0)


# =============================================================================
# POST-TRAITEMENT DÉTERMINISTE (le LLM ne décide plus pour les dates)
# =============================================================================

def _corriger_dates_experiences(profil: ProfilCandidat, texte_cv: str) -> ProfilCandidat:
    """
    Corrige date_fin des expériences à partir du texte brut du CV.
    Le LLM met parfois date_fin=null quand une date explicite existe
    (ex. « 2023-09 - 2026-09 » ou « Sept. 2022 – Déc. 2022 »).
    """
    motif = re.compile(
        rf"({_BORNE_DATE_PATTERN})\s*(?:[-–—]+|\bà\b|\bau\b)\s*({_BORNE_DATE_PATTERN})",
        flags=re.IGNORECASE,
    )
    paires_norm = []
    for debut_raw, fin_raw in motif.findall(texte_cv):
        d_norm = _normaliser_borne_vers_iso(debut_raw)
        f_norm = _normaliser_borne_vers_iso(fin_raw)
        if d_norm and f_norm:
            paires_norm.append((d_norm, f_norm))

    for exp in profil.experiences:
        if exp.date_fin is not None:
            continue
        if not exp.date_debut:
            continue

        debut_exp = _normaliser_borne_vers_iso(str(exp.date_debut)) or str(exp.date_debut).strip()
        for debut, fin in paires_norm:
            if debut == debut_exp or debut.startswith(debut_exp) or debut_exp.startswith(debut):
                exp.date_fin = fin
                break

    return profil


def _completer_listes_manquantes(profil: ProfilCandidat, texte_cv: str, essais: int) -> ProfilCandidat:
    """Relance un extraction ciblée si formations ou experiences sont vides alors que le texte en mentionne."""
    texte_lower = texte_cv.lower()

    if not profil.formations and re.search(
        r"\b(formation|formations|diplôme|diplome|master|licence|ingénieur|ingenieur|bachelor|dut|bts)\b",
        texte_lower,
    ):
        res_form = executer_agent(
            numero_agent=2,
            system_prompt=_SYSTEM_FORMATIONS,
            message=f"Texte du CV :\n\n{texte_cv}",
            schema=_ExtractionFormations,
            max_essais=essais,
        )
        profil.formations = res_form.formations

    if not profil.experiences and re.search(
        r"\b(expériences?|experiences?|expérience professionnelle|experience professionnelle|poste|stage|stagiaire|développeur|developpeur)\b",
        texte_lower,
    ):
        res_exp = executer_agent(
            numero_agent=2,
            system_prompt=_SYSTEM_EXPERIENCES,
            message=f"Texte du CV :\n\n{texte_cv}",
            schema=_ExtractionExperiences,
            max_essais=essais,
        )
        profil.experiences = res_exp.experiences

    return profil


# =============================================================================
# AGENT
# =============================================================================

def cv_extraction_agent(
    texte_cv: str,
    essais: int = 3,
) -> ProfilCandidat:
    profil = executer_agent(
        numero_agent=2,
        system_prompt=SYSTEM,
        message=f"Voici le contenu du CV à analyser :\n\n{texte_cv}",
        schema=ProfilCandidat,
        max_essais=essais,
    )

    profil = _completer_listes_manquantes(profil, texte_cv, essais=essais)
    profil = _corriger_dates_experiences(profil, texte_cv)
    return completer_profil(profil)


def extraire_profil_depuis_fichier(chemin) -> ProfilCandidat:
    """Lit un CV PDF/DOCX puis lance l'Agent 2."""
    texte = lire_cv(Path(chemin))
    return cv_extraction_agent(texte)