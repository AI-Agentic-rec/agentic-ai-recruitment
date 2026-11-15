"""Agent 1 — Job Requirement Agent.
Entrée : le texte d'une offre d'emploi.  Sortie : un objet `ExigencesStructurees` (schéma de l'équipe)."""
from .llm import call_llm
from .schemas import ExigencesStructurees

SYSTEM = """Tu es le Job Requirement Agent d'une plateforme de recrutement.
Ta seule tâche : transformer une offre d'emploi en données structurées.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après, sans balises de code.
- N'invente jamais une exigence absente de l'offre. Information absente : null pour un champ simple, [] pour une liste, 0 pour l'expérience.
- "titre_poste" : le titre du poste.
- "diplome_demande" : le diplôme exigé, recopié tel quel (ex. "Licence en informatique").
- "niveau_diplome_min" : le niveau en « Bac+N » : Bac=0, Bac+2=2, Licence=3, Master=5, Doctorat=8 ; null si non précisé.
- "experience_min_annees" : nombre d'années minimum (6 mois = 0.5 ; non précisé = 0).
- "competences_obligatoires" : ce qui est indispensable (« requis », « maîtrise de », « obligatoire »).
- "competences_souhaitees" : ce qui est un plus (« souhaité », « apprécié », « idéalement », « atout »).
- Une compétence = un terme court et normalisé (ex. "Python", "SQL", "Gestion de projet").
- "langues" : objets {"langue": "Français", "niveau": null} ; niveau recopié seulement s'il est écrit dans l'offre.
- "missions" : les principales missions du poste, phrases courtes (6 maximum).

Format exact :
{"titre_poste": null, "diplome_demande": null, "niveau_diplome_min": null, "experience_min_annees": 0,
 "competences_obligatoires": [], "competences_souhaitees": [], "langues": [{"langue": "", "niveau": null}], "missions": []}"""


def construire_texte_offre(offre) -> str:
    """Assemble le texte envoyé à l'agent à partir d'une Offre (modèle SQLAlchemy de la base)."""
    return (f"Titre : {offre.titre}\nLocalisation : {offre.localisation}\n"
            f"Description :\n{offre.description}\n"
            f"Diplôme demandé : {offre.diplome_demande}\nExpérience : {offre.experience_annees} an(s)\n"
            f"Compétences obligatoires : {', '.join(offre.competences_obligatoires)}\n"
            f"Compétences souhaitées : {', '.join(offre.competences_souhaitees)}\n"
            f"Langues : {', '.join(offre.langues)}")


def _extraire_json(texte: str) -> str:
    """Tolère les réponses entourées de ```json ... ``` ou de phrases parasites."""
    debut, fin = texte.find("{"), texte.rfind("}")
    return texte[debut:fin + 1] if debut != -1 and fin > debut else texte


def job_requirement_agent(texte_offre: str, essais: int = 3) -> ExigencesStructurees:
    message, derniere_erreur = texte_offre, None
    for _ in range(essais):
        brut = call_llm(SYSTEM, message, max_tokens=1500, schema=ExigencesStructurees.model_json_schema())
        try:
            return ExigencesStructurees.model_validate_json(_extraire_json(brut))   # vérifie le schéma
        except ValueError as e:                                                      # ValidationError hérite de ValueError
            derniere_erreur = e
            message = (f"{texte_offre}\n\n[Ta réponse précédente était invalide : {e}. "
                       f"Réponds uniquement avec le JSON demandé.]")
    raise RuntimeError(f"Job Requirement Agent : sortie invalide après {essais} essais ({derniere_erreur})")
