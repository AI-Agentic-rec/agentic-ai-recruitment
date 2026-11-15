"""Échelle des niveaux de diplôme (Bac+N), partagée par les agents 3 et 4 : un seul endroit à modifier.
L'échelle de niveau_diplome_min (schemas.py) doit rester identique à celle-ci."""
import re
import unicodedata


def normaliser(texte) -> str:
    """minuscules, sans accents ni ponctuation : « Hélène » = « helene », « BENALI » = « benali »."""
    t = unicodedata.normalize("NFD", texte or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]", " ", t).split())


NIVEAUX = (("doctorat", 8), ("master", 5), ("mastere", 5), ("ingenieur", 5), ("bac 5", 5), ("licence", 3),
           ("bachelor", 3), ("bac 3", 3), ("deug", 2), ("dut", 2), ("bts", 2), ("bac 2", 2))


def niveau_diplome(*textes):
    """Niveau Bac+N d'un intitulé (ex. « Master » -> 5), ou None s'il n'est pas reconnu."""
    n = f" {normaliser(' '.join(t for t in textes if t))} "
    return next((v for mot, v in NIVEAUX if f" {mot} " in n), None)
