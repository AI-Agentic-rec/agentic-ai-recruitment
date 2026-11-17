"""Agent 2 — CV Extraction Agent.
Entrée : le texte d'un CV (voir lecture_documents.lire_cv).  Sortie : un `ProfilCandidat` (schéma de l'équipe)."""
from pathlib import Path
from .calculs import completer_profil
from .job_requirement import _extraire_json
from .lecture_documents import lire_cv
from .llm import call_llm
from .schemas import ProfilCandidat

SYSTEM = """Tu es le CV Extraction Agent d'une plateforme de recrutement.
Ta seule tâche : extraire fidèlement les informations d'un CV et les structurer.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises de code.
- Recopie ce qui est écrit dans le CV. N'invente rien, ne déduis rien : information absente = null (champ simple) ou [] (liste).
- "nom" = nom de famille ; "prenom" = prénom ; "email" et "telephone" tels qu'écrits.
- "formations" : une entrée par diplôme (diplome, specialite, etablissement, date_debut, date_fin).
- "experiences" : une entrée par poste ou stage : poste, entreprise, description (UNE phrase courte), date_debut, date_fin,
  competences (celles citées pour ce poste).
- DATES : format "AAAA-MM" (ex. "2021-03") ; si seule l'année est écrite : "AAAA". Poste actuel (« présent », « en cours ») : date_fin = null.
- "duree_annees" de chaque expérience = null et "experience_totale_annees" = 0 : le programme les calcule lui-même, NE LES CALCULE PAS.
- "competences" : termes courts et normalisés (ex. "Python", "SQL"), sans phrases, sans doublons.
- "langues" : objets {"langue": "Français", "niveau": null} ; niveau recopié seulement s'il est écrit.
- "certifications" : certificats et attestations (hors diplômes universitaires).

Format exact :
{"nom": null, "prenom": null, "email": null, "telephone": null,
 "formations": [{"diplome": "", "specialite": null, "etablissement": null, "date_debut": null, "date_fin": null}],
 "experiences": [{"poste": "", "entreprise": null, "description": null, "date_debut": null, "date_fin": null, "duree_annees": null, "competences": []}],
 "competences": [], "langues": [{"langue": "", "niveau": null}], "certifications": [], "experience_totale_annees": 0}"""


def cv_extraction_agent(texte_cv: str, essais: int = 3) -> ProfilCandidat:
    message, derniere_erreur = texte_cv, None
    for _ in range(essais):
        brut = call_llm(SYSTEM, message, max_tokens=2500, schema=ProfilCandidat.model_json_schema())
        try:
            profil = ProfilCandidat.model_validate_json(_extraire_json(brut))
            return completer_profil(profil)          # durées calculées par le code
        except ValueError as e:
            derniere_erreur = e
            message = (f"{texte_cv}\n\n[Ta réponse précédente était invalide : {e}. "
                       f"Réponds uniquement avec le JSON demandé.]")
    raise RuntimeError(f"CV Extraction Agent : sortie invalide après {essais} essais ({derniere_erreur})")


def extraire_profil_depuis_fichier(chemin) -> ProfilCandidat:
    """Raccourci : lit le fichier (PDF/DOCX) puis lance l'agent."""
    return cv_extraction_agent(lire_cv(Path(chemin)))
