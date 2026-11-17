"""La base doit correspondre EXACTEMENT au diagramme de classes (v2) : mêmes tables, mêmes attributs."""
import app.models  # noqa: F401
from app.db.base import Base
from app.models import enums

UML = {
    "utilisateur": ["id", "nom", "prenom", "email", "mot_de_passe_hash", "role", "telephone"],
    "offre": ["id", "id_admin", "titre", "description", "diplome_demande", "experience_annees",
              "competences_obligatoires", "competences_souhaitees", "langues", "localisation", "statut",
              "date_creation", "date_publication", "date_cloture"],
    "candidature": ["id", "id_candidat", "id_offre", "date_candidature", "statut", "message_erreur"],
    "document": ["id", "id_candidature", "type", "chemin_fichier", "date_import"],
    "exigences_structurees": ["id_offre", "titre_poste", "diplome_demande", "niveau_diplome_min",
                              "experience_min_annees", "competences_obligatoires", "competences_souhaitees",
                              "langues", "missions"],
    "profil_candidat": ["id_candidature", "nom", "prenom", "email", "telephone", "formations", "experiences",
                        "competences", "langues", "certifications", "experience_totale_annees"],
    "verification_documents": ["id_candidature", "infos_diplome", "infos_cin", "documents_analyses",
                               "documents_manquants", "documents_illisibles", "incoherences",
                               "niveau_conformite", "score_coherence", "resume"],
    # `details` (et non `details_score`) : seule modification demandée par rapport au diagramme.
    "resultat_analyse": ["id_candidature", "score_global", "details", "competences_correspondantes",
                         "competences_manquantes", "diplome_conforme", "experience_candidat_annees", "rapport",
                         "avis_indicatif", "date_analyse"],
}

ENUMS = {
    "RoleUtilisateur": ["ADMIN", "CANDIDAT"],
    "StatutOffre": ["BROUILLON", "PUBLIEE", "CLOTUREE"],
    "StatutCandidature": ["ENVOYEE", "EN_ATTENTE_DE_TRAITEMENT", "EN_COURS_DE_TRAITEMENT", "ANALYSE_TERMINEE",
                          "ERREUR_DE_TRAITEMENT"],
    "TypeDocument": ["CV", "DIPLOME", "CIN"],
    "NiveauConformite": ["CONFORME", "PARTIELLEMENT_CONFORME", "NON_CONFORME"],
    "AvisIndicatif": ["FAVORABLE", "DEFAVORABLE", "A_ETUDIER"],
    "Critere": ["COMPETENCES_OBLIGATOIRES", "EXPERIENCE", "DIPLOME_FORMATION", "COMPETENCES_SOUHAITEES",
                "LANGUES", "COHERENCE_DOCUMENTS"],
}


def test_les_8_tables_du_diagramme():
    assert sorted(Base.metadata.tables) == sorted(UML)


def test_attributs_identiques_au_diagramme():
    for table, colonnes in UML.items():
        assert [c.name for c in Base.metadata.tables[table].columns] == colonnes, table


def test_enumerations_identiques_au_diagramme():
    for nom, valeurs in ENUMS.items():
        assert [m.value for m in getattr(enums, nom)] == valeurs, nom


def test_cles_primaires_et_etrangeres():
    t = Base.metadata.tables
    for table in ("exigences_structurees",):
        assert [c.name for c in t[table].primary_key] == ["id_offre"]
    for table in ("profil_candidat", "verification_documents", "resultat_analyse"):
        assert [c.name for c in t[table].primary_key] == ["id_candidature"]
    assert {fk.target_fullname for fk in t["offre"].foreign_keys} == {"utilisateur.id"}
    assert {fk.target_fullname for fk in t["candidature"].foreign_keys} == {"utilisateur.id", "offre.id"}
    assert {fk.target_fullname for fk in t["document"].foreign_keys} == {"candidature.id"}
