"""Teste le prototype SANS Ollama.  Lancer : python -m pytest agents/agent3_document_verification/test_agent3_prototype.py"""
import json
from agents.agent3_document_verification.agent3_prototype import ATTENDU, ExtractionDocuments, evaluer, executer_cas
from agents.agent3_document_verification.cas_test_agent3 import CAS_COHERENT, CAS_INCOHERENT


def parfait(nom):
    return lambda modele, system, messages, schema: json.dumps(ATTENDU[nom])


def test_extraction_parfaite_donne_tous_les_champs_corrects():
    assert executer_cas("coherent", CAS_COHERENT, llm=parfait("coherent"), afficher=False) == (10, 10)
    assert executer_cas("incoherent", CAS_INCOHERENT, llm=parfait("incoherent"), afficher=False) == (10, 10)


def test_evaluation_ignore_majuscules_accents_et_repere_les_erreurs():
    faux = json.loads(json.dumps(ATTENDU["coherent"]))
    faux["infos_cin"]["nom"] = "BENALI"                  # majuscules : accepté
    faux["infos_diplome"]["diplome"] = "Licence"         # erreur
    faux["infos_cin"]["numero_cin"] = "AB123466"         # chiffre mal lu : erreur
    corrects, total, lignes = evaluer(ExtractionDocuments.model_validate(faux), ATTENDU["coherent"])
    assert (corrects, total) == (8, 10) and sum(l.startswith("  KO") for l in lignes) == 2


if __name__ == "__main__":
    echecs = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            try:
                f(); print("OK ", nom)
            except Exception as erreur:          # on continue : on voit tous les tests en échec, pas seulement le premier
                echecs += 1; print(f"KO  {nom} : {type(erreur).__name__} {erreur}")
    print("\nTous les tests passent." if not echecs else f"\n{echecs} test(s) en échec.")
    raise SystemExit(1 if echecs else 0)      # code d'erreur pour la vérification automatique (GitHub Actions)
