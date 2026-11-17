"""Tests de app/services/enregistrement_resultats.py (4 tables de résultats des agents)."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.common import schemas as ag
from app.models import (Candidature, ExigencesStructurees, NiveauConformite, ProfilCandidat, ResultatAnalyse,
                        StatutCandidature, VerificationDocuments, AvisIndicatif)
from app.services import (CandidatureIntrouvableError, OffreIntrouvableError, enregistrer_erreur_traitement,
                          enregistrer_exigences_structurees, enregistrer_profil_candidat,
                          enregistrer_resultat_analyse, enregistrer_resultats_candidature,
                          enregistrer_verification_documents)

MOCKS = Path(__file__).resolve().parents[2] / "data" / "mocks"


def mock(nom):
    return json.loads((MOCKS / nom).read_text(encoding="utf-8-sig"))


def test_agent1_exigences_ecrites_puis_remplacees(db, candidature):
    enregistrer_exigences_structurees(db, candidature.id_offre, mock("agent1_exemple.json"))
    attendu = ag.ExigencesStructurees.model_validate(mock("agent1_exemple.json"))
    ligne = db.get(ExigencesStructurees, candidature.id_offre)
    assert ligne.titre_poste == attendu.titre_poste
    assert ligne.competences_obligatoires == attendu.competences_obligatoires
    assert ligne.langues == [l.model_dump(mode="json") for l in attendu.langues]

    enregistrer_exigences_structurees(db, candidature.id_offre, ag.ExigencesStructurees(titre_poste="Autre"))
    assert db.query(ExigencesStructurees).count() == 1
    assert db.get(ExigencesStructurees, candidature.id_offre).titre_poste == "Autre"


def test_agent1_offre_inconnue(db):
    with pytest.raises(OffreIntrouvableError):
        enregistrer_exigences_structurees(db, 999, mock("agent1_exemple.json"))


def test_agent2_profil(db, candidature):
    attendu = ag.ProfilCandidat.model_validate(mock("agent2_exemple.json"))
    ligne = enregistrer_profil_candidat(db, candidature.id, mock("agent2_exemple.json"))
    assert (ligne.nom, ligne.prenom, ligne.email) == (attendu.nom, attendu.prenom, attendu.email)
    assert ligne.competences == attendu.competences
    assert ligne.experience_totale_annees == attendu.experience_totale_annees
    assert len(ligne.formations) == len(attendu.formations)
    assert len(ligne.experiences) == len(attendu.experiences)


def test_agent3_verification_incoherente(db, candidature):
    donnees = mock("agent3_exemple_incoherent.json")
    attendu = ag.VerificationDocuments.model_validate(donnees)
    ligne = enregistrer_verification_documents(db, candidature.id, donnees)
    assert ligne.niveau_conformite is NiveauConformite(attendu.niveau_conformite.upper())
    assert ligne.score_coherence == attendu.score_coherence
    assert ligne.resume == attendu.resume
    assert len(ligne.incoherences) == len(attendu.incoherences) > 0
    assert {"type", "description", "gravite", "documents"} <= set(ligne.incoherences[0])


def test_agent3_masque_le_numero_cin(db, candidature):
    donnees = mock("agent3_exemple_conforme.json")
    donnees["infos_cin"]["numero_cin"] = "AB123456"
    ligne = enregistrer_verification_documents(db, candidature.id, donnees)
    assert ligne.infos_cin["numero_cin"] == "*****456"
    assert "AB123456" not in json.dumps(ligne.infos_cin)


def test_agent3_sans_documents(db, candidature):
    donnees = mock("agent3_exemple_conforme.json") | {"infos_diplome": None, "infos_cin": None}
    ligne = enregistrer_verification_documents(db, candidature.id, donnees)
    assert ligne.infos_diplome is None and ligne.infos_cin is None


@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_agents_4_et_5(db, candidature, cas):
    a4 = ag.ResultatMatching.model_validate(mock(f"agent4_exemple_{cas}.json"))
    a5 = ag.RapportCandidature.model_validate(mock(f"agent5_exemple_{cas}.json"))
    ligne = enregistrer_resultat_analyse(db, candidature.id, a4, a5)
    assert ligne.score_global == a4.score_global
    assert [d["critere"] for d in ligne.details] == [d.critere for d in a4.details]
    assert len(ligne.details) == 6
    assert ligne.competences_correspondantes == a4.competences_correspondantes
    assert ligne.competences_manquantes == a4.competences_manquantes
    assert ligne.diplome_conforme == a4.diplome_conforme
    assert ligne.experience_candidat_annees == a4.experience_candidat_annees
    assert ligne.avis_indicatif is AvisIndicatif(a5.avis_indicatif.upper())
    assert ligne.rapport["conclusion"] == a5.conclusion
    assert ligne.date_analyse is not None


def test_rapport_ajoute_apres_puis_conserve(db, candidature):
    a4 = mock("agent4_exemple_conforme.json")
    enregistrer_resultat_analyse(db, candidature.id, a4)
    assert db.get(ResultatAnalyse, candidature.id).rapport is None
    enregistrer_resultat_analyse(db, candidature.id, a4, mock("agent5_exemple_conforme.json"))
    enregistrer_resultat_analyse(db, candidature.id, a4)  # sans rapport : l'ancien reste
    ligne = db.get(ResultatAnalyse, candidature.id)
    assert ligne.rapport is not None and ligne.avis_indicatif is not None
    assert db.query(ResultatAnalyse).count() == 1


def test_sortie_invalide_rien_n_est_ecrit(db, candidature):
    mauvais = mock("agent4_exemple_conforme.json") | {"score_global": 5}  # incohérent avec les détails
    with pytest.raises(ValidationError):
        enregistrer_resultat_analyse(db, candidature.id, mauvais)
    assert db.query(ResultatAnalyse).count() == 0


def test_candidature_inconnue(db):
    with pytest.raises(CandidatureIntrouvableError):
        enregistrer_profil_candidat(db, 999, mock("agent2_exemple.json"))


def _sorties(cas="conforme"):
    return dict(profil=mock("agent2_exemple.json"), verification=mock(f"agent3_exemple_{cas}.json"),
                matching=mock(f"agent4_exemple_{cas}.json"), rapport=mock(f"agent5_exemple_{cas}.json"))


def test_pipeline_complet_puis_relance(db, candidature):
    enregistrer_erreur_traitement(db, candidature.id, "échec précédent")
    assert db.get(Candidature, candidature.id).statut is StatutCandidature.ERREUR_DE_TRAITEMENT
    enregistrer_resultats_candidature(db, candidature.id, **_sorties())
    enregistrer_resultats_candidature(db, candidature.id, **_sorties())  # relance : pas de doublon
    for table in (ProfilCandidat, VerificationDocuments, ResultatAnalyse):
        assert db.query(table).count() == 1
    c = db.get(Candidature, candidature.id)
    assert c.statut is StatutCandidature.ANALYSE_TERMINEE and c.message_erreur is None


def test_pipeline_tout_ou_rien(db, candidature):
    sorties = _sorties() | {"matching": mock("agent4_exemple_conforme.json") | {"score_global": 5}}
    with pytest.raises(ValidationError):
        enregistrer_resultats_candidature(db, candidature.id, **sorties)
    assert db.query(ProfilCandidat).count() == 0
    assert db.query(VerificationDocuments).count() == 0
    assert db.get(Candidature, candidature.id).statut is StatutCandidature.ENVOYEE


def test_erreur_de_traitement_enregistree(db, candidature):
    enregistrer_erreur_traitement(db, candidature.id, "Ollama indisponible")
    c = db.get(Candidature, candidature.id)
    assert (c.statut, c.message_erreur) == (StatutCandidature.ERREUR_DE_TRAITEMENT, "Ollama indisponible")
