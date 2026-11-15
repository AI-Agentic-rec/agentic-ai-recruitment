"""Tests de l'agent 3 SANS Ollama (faux LLM).  Lancer : python -m pytest agents/agent3_document_verification/test_agent3.py"""
import json, logging, tempfile
from pathlib import Path
from agents.agent3_document_verification.agent3 import (_masquer, calculer_conformite, comparer_en_code, sans_donnees_sensibles, verifier_documents)
from agents.agent3_document_verification.cas_test_agent3 import CAS_COHERENT, CAS_INCOHERENT, PROFIL_CV
from agents.common.llm_local import AgentError
from agents.common.schemas import ContexteCandidature, Incoherence, InfosCIN, InfosDiplome, ProfilCandidat

DIP = {"nom": "Benali", "prenom": "Sara", "diplome": "Master", "specialite": "Informatique",
       "etablissement": "Université Fictive de Casablanca", "date_obtention": "2021"}
CIN = {"nom": "Benali", "prenom": "Sara", "date_naissance": "1998-04-12", "numero_cin": "AB123456"}
VIDE_D = {k: None for k in DIP}
VIDE_C = {k: None for k in CIN}
logging.disable(logging.CRITICAL)      # les tests simulent des erreurs : pas de messages d'avertissement à l'écran
profil = lambda **ch: ProfilCandidat.model_validate({**PROFIL_CV, **ch})
ext = lambda d=DIP, c=CIN: json.dumps({"infos_diplome": d, "infos_cin": c})
types = lambda inc: sorted((i.type, i.gravite) for i in inc)


def faux(*reponses):
    it = iter(reponses)
    return lambda modele, system, messages, schema: next(it)


def interdit(*a):
    raise AssertionError("le modèle ne devait pas être appelé")


def test_cas_coherent():
    r = verifier_documents(**CAS_COHERENT, llm=faux(ext()))
    assert (r.niveau_conformite, r.score_coherence, r.incoherences) == ("conforme", 100, []), \
        f"obtenu : {r.niveau_conformite}, {r.score_coherence}, {[i.description for i in r.incoherences]}"
    assert r.documents_analyses == ["cv", "diplome", "cin"] and not r.documents_manquants and not r.documents_illisibles


def test_cas_incoherent():
    r = verifier_documents(**CAS_INCOHERENT, llm=faux(ext({**DIP, "diplome": "Licence", "date_obtention": "2019"}, {**CIN, "prenom": "Sarah"})))
    assert types(r.incoherences) == [("diplome", "elevee"), ("identite", "faible")], f"obtenu : {types(r.incoherences)}"
    assert (r.niveau_conformite, r.score_coherence) == ("non_conforme", 50)
    assert r.incoherences[0].description == "Le prénom est « Sara » sur le CV mais « Sarah » sur la CIN."


def test_majuscules_et_accents_ignores():
    p = profil(nom="Hélène", prenom="Zoé", formations=[])
    assert comparer_en_code(p, InfosDiplome(**{**DIP, "nom": "HELENE", "prenom": "ZOE"}), InfosCIN(**{**CIN, "nom": "HELENE", "prenom": "ZOE"})) == []


def test_noms_composes_ne_sont_pas_des_incoherences():
    p = profil(nom="El Amrani", prenom="Mohamed-Amine")
    assert comparer_en_code(p, InfosDiplome(**{**DIP, "nom": "ELAMRANI", "prenom": "Mohamed Amine"}), InfosCIN(**{**CIN, "nom": "ELAMRANI", "prenom": "Amine"})) == []


def test_nom_different_sur_la_cin_et_sur_le_diplome():
    assert types(comparer_en_code(profil(), InfosDiplome(**DIP), InfosCIN(**{**CIN, "nom": "Alaoui"}))) == [("identite", "elevee")]
    inc = comparer_en_code(profil(), InfosDiplome(**{**DIP, "nom": "Alaoui"}), InfosCIN(**CIN))
    assert types(inc) == [("identite", "elevee")] and inc[0].documents == ["cv", "diplome"]


def test_prenom_proche_faible_prenom_different_eleve():
    assert types(comparer_en_code(profil(), InfosDiplome(**DIP), InfosCIN(**{**CIN, "prenom": "Sarah"}))) == [("identite", "faible")]
    assert types(comparer_en_code(profil(), InfosDiplome(**DIP), InfosCIN(**{**CIN, "prenom": "Amal"}))) == [("identite", "elevee")]


def test_annee_et_specialite_differentes_meme_niveau():
    assert types(comparer_en_code(profil(), InfosDiplome(**{**DIP, "date_obtention": "2020-06-30"}), InfosCIN(**CIN))) == [("date", "moyenne")]
    assert types(comparer_en_code(profil(), InfosDiplome(**{**DIP, "specialite": "Gestion"}), InfosCIN(**CIN))) == [("diplome", "moyenne")]
    assert comparer_en_code(profil(), InfosDiplome(**{**DIP, "specialite": "Génie Informatique", "date_obtention": "2021-06-15"}), InfosCIN(**CIN)) == []


def test_champs_illisibles_partiels():
    r = verifier_documents(**CAS_COHERENT, llm=faux(ext(c={**CIN, "nom": None, "numero_cin": None})))
    assert r.niveau_conformite == "partiellement_conforme" and r.incoherences[0].type == "autre" and not r.documents_illisibles


def test_cin_entierement_illisible():
    r = verifier_documents(**CAS_COHERENT, llm=faux(ext(c=VIDE_C)))
    assert r.documents_illisibles == ["cin"] and r.infos_cin is None and r.documents_analyses == ["cv", "diplome"]
    assert r.niveau_conformite == "partiellement_conforme"


def test_document_manquant_le_modele_ne_peut_pas_inventer():
    r = verifier_documents(profil(), texte_diplome="diplome", llm=faux(ext()))   # le faux modèle « invente » une CIN complète
    assert r.documents_manquants == ["cin"] and r.infos_cin is None and (r.score_coherence, r.niveau_conformite) == (60, "non_conforme")


def test_aucun_document_exploitable_pas_d_appel_au_modele():
    r = verifier_documents(profil(), llm=interdit)
    assert r.documents_manquants == ["diplome", "cin"] and r.niveau_conformite == "non_conforme" and r.score_coherence == 20


def test_normalisation_dates_et_numero_cin():
    r = verifier_documents(**CAS_COHERENT, llm=faux(ext({**DIP, "date_obtention": "30/06/2021"}, {**CIN, "date_naissance": "12/04/1998", "numero_cin": "ab 123456"})))
    assert (r.infos_cin.date_naissance, r.infos_cin.numero_cin, r.infos_diplome.date_obtention) == ("1998-04-12", "AB123456", "2021-06-30")
    assert r.incoherences == []     # 2021-06-30 et date_fin du CV 2021-06 : même année


def test_une_lettre_mal_lue_par_l_ocr_est_faible_pas_grave():
    assert types(comparer_en_code(profil(), InfosDiplome(**DIP), InfosCIN(**{**CIN, "nom": "Benalj"}))) == [("identite", "faible")]
    assert types(comparer_en_code(profil(), InfosDiplome(**{**DIP, "nom": "BENAL1"}), InfosCIN(**CIN))) == [("identite", "faible")]


def test_champ_inconnu_refuse_puis_relance():
    r = verifier_documents(**CAS_COHERENT, llm=faux(json.dumps({"infos_diplome": DIP, "infos_cin": CIN, "commentaire": "extra"}), ext()))
    assert r.score_coherence == 100          # extra="forbid" : la 1re réponse est refusée, la 2e acceptée


def test_relance_si_json_invalide_puis_erreur():
    assert verifier_documents(**CAS_COHERENT, llm=faux("pas du json", ext())).score_coherence == 100
    try:
        verifier_documents(**CAS_COHERENT, llm=faux("x", "y", "z")); assert False
    except AgentError:
        pass


def test_images_lues_par_ocr_puis_extraites():
    with tempfile.TemporaryDirectory() as d:
        dip, cin = Path(d, "diplome.png"), Path(d, "cin.png"); dip.write_bytes(b"x"); cin.write_bytes(b"x")
        lus = []
        ocr = lambda chemin: (lus.append(chemin), "texte lu")[1]
        r = verifier_documents(PROFIL_CV, image_diplome=str(dip), image_cin=str(cin), llm=faux(ext()), ocr=ocr,
                               contexte=ContexteCandidature(candidate_id="c1", job_id="j1"))
    assert lus == [str(dip), str(cin)] and r.niveau_conformite == "conforme"


def test_ocr_vide_est_un_document_illisible():
    with tempfile.TemporaryDirectory() as d:
        cin = Path(d, "cin.png"); cin.write_bytes(b"x")
        r = verifier_documents(PROFIL_CV, texte_diplome="diplome", image_cin=str(cin), llm=faux(ext()), ocr=lambda chemin: "  ")
    assert r.documents_illisibles == ["cin"] and r.documents_manquants == []


def test_image_introuvable():
    try:
        verifier_documents(PROFIL_CV, image_diplome="n_existe_pas.png", texte_cin="x", llm=faux(ext())); assert False
    except AgentError:
        pass


def test_regle_de_conformite():
    inc = lambda g: Incoherence(type="autre", description="x", gravite=g, documents=["cv"])
    assert calculer_conformite([]) == ("conforme", 100)
    assert calculer_conformite([inc("faible")]) == ("partiellement_conforme", 90)
    assert calculer_conformite([inc("moyenne")] * 3)[0] == "non_conforme"
    assert calculer_conformite([inc("elevee")]) == ("non_conforme", 60)


def test_numero_cin_retire_pour_les_agents_suivants_et_masque_dans_les_logs():
    r = verifier_documents(**CAS_COHERENT, llm=faux(ext()))
    propre = sans_donnees_sensibles(r)
    assert propre.infos_cin.numero_cin is None and r.infos_cin.numero_cin == "AB123456"
    assert "AB123456" not in _masquer("Nom : BENALI\nN° : AB 123456\nPrénom : Sara") and "AB123456" not in _masquer("N° : AB123456")
    assert "BENALI" in _masquer("Nom : BENALI")


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
