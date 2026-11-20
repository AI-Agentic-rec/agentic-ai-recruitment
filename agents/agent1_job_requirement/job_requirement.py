"""Agent 1 — Job Requirement Agent.
Entrée : le texte d'une offre d'emploi.
Sortie : un objet ExigencesStructurees validé par Pydantic.
"""

from agents.common.llm_local import executer_agent
from agents.common.schemas import ExigencesStructurees


SYSTEM = """Tu es le Job Requirement Agent d'une plateforme de recrutement.

Ta seule tâche : transformer une offre d'emploi en données structurées.

Règles :
- Réponds UNIQUEMENT avec un objet JSON valide.
- N'invente jamais une exigence absente de l'offre.
- Information absente : null pour un champ simple,
  [] pour une liste, 0 pour l'expérience.

- "titre_poste" : le titre du poste, recopié tel quel.
- "diplome_demande" : le diplôme exigé, recopié tel quel.
  null si aucun diplôme n'est mentionné.
- "niveau_diplome_min" : niveau en Bac+N :
  Bac=0, Bac+2=2, Licence=3, Master=5, Doctorat=8.
  null si non précisé ou si aucun diplôme n'est exigé.
  N'écris JAMAIS "Bac+None", "Bac+" ou "Bac" sans chiffre
  dans ce champ : utilise null.

- "experience_min_annees" : nombre d'années minimum
  (6 mois = 0.5 ; non précisé = 0).

- "competences_obligatoires" : compétences indispensables
  EXPLICITEMENT listées dans l'offre
  (mots-clés : requis, requise, obligatoire, maîtrise de, exigé).
  Si l'offre ne contient AUCUNE section « compétences requises »
  ou « compétences obligatoires », retourne [].

- "competences_souhaitees" : compétences appréciées
  EXPLICITEMENT listées dans l'offre
  (mots-clés : souhaité, apprécié, idéalement, atout, plus).
  Si l'offre ne contient AUCUNE section « compétences appréciées »
  ou « compétences souhaitées », retourne [].

- Ne déduis JAMAIS une compétence à partir du titre du poste,
  des missions, de la localisation ou du contexte.
  Copie uniquement ce qui est écrit dans une section
  dédiée aux compétences. Si tu hésites, retourne [].

- Une compétence = un terme court et normalisé
  (ex. « Python », « SQL », « Gestion de projet »).
  Ne recopie pas les phrases entières ni les qualificatifs
  (« apprécié », « maîtrise de », « souhaité »).

- "langues" : objets {"langue": "...", "niveau": null}.
  Le niveau est recopié seulement s'il est écrit dans l'offre
  (ex. « B2 », « C1 », « courant »).

- "missions" : principales missions du poste,
  phrases courtes (6 maximum). Si aucune mission n'est
  listée, retourne [].

Respecte exactement le schéma Pydantic fourni.
"""


def construire_texte_offre(offre) -> str:
    """Assemble le texte envoyé à l'agent depuis une Offre SQLAlchemy."""

    return (
        f"Titre : {offre.titre}\n"
        f"Localisation : {offre.localisation}\n"
        f"Description :\n{offre.description}\n"
        f"Diplôme demandé : {offre.diplome_demande}\n"
        f"Expérience : {offre.experience_annees} an(s)\n"
        f"Compétences obligatoires : "
        f"{', '.join(offre.competences_obligatoires)}\n"
        f"Compétences souhaitées : "
        f"{', '.join(offre.competences_souhaitees)}\n"
        f"Langues : {', '.join(offre.langues)}"
    )


def job_requirement_agent(
    texte_offre: str,
    essais: int = 3
) -> ExigencesStructurees:
    """Extrait et valide les exigences d'une offre avec l'Agent 1."""

    return executer_agent(
        numero_agent=1,
        system_prompt=SYSTEM,
        message=f"Voici le contenu de l'offre d'emploi :\n\n{texte_offre}",
        schema=ExigencesStructurees,
        max_essais=essais
    )
