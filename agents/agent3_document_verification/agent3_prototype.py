
import logging
import unicodedata

from agents.agent3_document_verification.cas_test_agent3 import CAS_COHERENT, CAS_INCOHERENT
from agents.common.llm_local import executer_agent, modele_pour
from agents.agent3_document_verification.prompts_agent3 import PROMPT_EXTRACTION
from agents.common.schemas import BaseSchema, InfosCIN, InfosDiplome


class ExtractionDocuments(BaseSchema):
    infos_diplome: InfosDiplome
    infos_cin: InfosCIN


# Ce que le modèle DOIT extraire de chaque cas de test (on connaît la vérité : les documents sont fictifs)
ATTENDU = {
    "coherent": {
        "infos_diplome": {"nom": "Benali", "prenom": "Sara", "diplome": "Master", "specialite": "Informatique",
                          "etablissement": "Université Fictive de Casablanca", "date_obtention": "2021"},
        "infos_cin": {"nom": "Benali", "prenom": "Sara", "date_naissance": "1998-04-12", "numero_cin": "AB123456"},
    },
    "incoherent": {
        "infos_diplome": {"nom": "Benali", "prenom": "Sara", "diplome": "Licence", "specialite": "Informatique",
                          "etablissement": "Université Fictive de Casablanca", "date_obtention": "2019"},
        "infos_cin": {"nom": "Benali", "prenom": "Sarah", "date_naissance": "1998-04-12", "numero_cin": "AB123456"},
    },
}


def _simple(valeur) -> str:
    """minuscules, sans accents, sans espaces : « BENALI » = « Benali »."""
    t = unicodedata.normalize("NFD", str(valeur or "")).encode("ascii", "ignore").decode().lower()
    return "".join(t.split())


def evaluer(extraction: ExtractionDocuments, attendu: dict) -> tuple[int, int, list[str]]:
    """Compare champ par champ (sans tenir compte des majuscules ni des accents). Renvoie (corrects, total, lignes)."""
    lignes, corrects, total = [], 0, 0
    for doc in ("infos_diplome", "infos_cin"):
        obtenu = getattr(extraction, doc).model_dump()
        for champ, valeur_attendue in attendu[doc].items():
            total += 1
            ok = _simple(obtenu.get(champ)) == _simple(valeur_attendue)
            corrects += ok
            lignes.append(f"  {'OK ' if ok else 'KO '} {doc + '.' + champ:<28} attendu={valeur_attendue!r:<40} obtenu={obtenu.get(champ)!r}")
    return corrects, total, lignes


def executer_cas(nom: str, cas: dict, llm=None, afficher: bool = True):
    message = f"TEXTE DU DIPLÔME :\n{cas['texte_diplome']}\n\nTEXTE DE LA CIN :\n{cas['texte_cin']}"
    extraction = executer_agent(3, PROMPT_EXTRACTION, message, ExtractionDocuments, llm=llm)
    corrects, total, lignes = evaluer(extraction, ATTENDU[nom])
    if afficher:
        origine = modele_pour(3) if llm is None else "FAUX MODÈLE DE TEST, pas un vrai résultat"
        print(f"\n=== Cas {nom} ({origine}) : {corrects}/{total} champs corrects ===")
        print("\n".join(lignes))
    return corrects, total


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    resultats = [executer_cas("coherent", CAS_COHERENT), executer_cas("incoherent", CAS_INCOHERENT)]
    print(f"\nTOTAL : {sum(c for c, _ in resultats)}/{sum(t for _, t in resultats)} champs corrects")
    print("Si des champs sont KO : améliorer prompts_agent3.py, puis relancer. Garder une capture pour le rapport.")
