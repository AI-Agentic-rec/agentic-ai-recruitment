"""Erreurs de l'Agent 5 (Report).

Les messages d'erreur ne contiennent JAMAIS de donnée personnelle (ni valeur saisie, ni CIN) :
ils sont destinés aux logs et à l'orchestrateur ("Erreur de traitement").
"""


class Agent5Error(Exception):
    """Erreur de base de l'Agent 5."""


class EntreeInvalideError(Agent5Error, ValueError):
    """Une sortie des agents 1 à 4 est absente, de mauvais type ou ne respecte pas son schéma."""


class ErreurLLM(Agent5Error):
    """Le modèle local est indisponible, ou n'a pas renvoyé de JSON valide après les essais."""


class RedactionInvalideError(Agent5Error):
    """Le texte rédigé par le modèle viole une règle métier (score modifié, nombre inventé, CIN...)."""


class FuiteDonneesSensiblesError(Agent5Error):
    """Une donnée sensible (numéro de CIN) allait être transmise au modèle : envoi bloqué."""


class RapportInvalideError(Agent5Error):
    """Le rapport assemblé ne respecte pas le schéma `RapportCandidature`."""
