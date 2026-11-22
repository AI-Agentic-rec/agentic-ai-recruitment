import asyncio
import logging

from app.celery_app import celery_app 
from app.db.session import SessionLocal
from app.models import Candidature
from app.models.enums import StatutCandidature, TypeDocument, AvisIndicatif, NiveauConformite
from app.models.resultats_agents import (
    ResultatAnalyse, ExigencesStructurees, ProfilCandidat, VerificationDocuments
)
from backend.orchestrateur.orchestrator_langgraph import run_workflow

# Masquer les warnings de pdfminer (bruit dans les logs)
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

@celery_app.task(name="traiter_candidature")
def tache_traiter_candidature(candidature_id: int):
    logger.info(f"Début du traitement IA pour la candidature {candidature_id}")
    db = SessionLocal()
    try:
        cand = db.get(Candidature, candidature_id)
        if not cand:
            return "Candidature introuvable"

        # 1. Récupérer les chemins des fichiers
        cv_path = next((d.chemin_fichier for d in cand.documents if d.type == TypeDocument.CV), None)
        diplome_path = next((d.chemin_fichier for d in cand.documents if d.type == TypeDocument.DIPLOME), None)
        cin_path = next((d.chemin_fichier for d in cand.documents if d.type == TypeDocument.CIN), None)

        if not cv_path or not diplome_path:
            raise ValueError("Documents manquants (CV ou Diplôme)")

        # 2. Construire le texte complet de l'offre pour l'Agent 1
        offre = cand.offre
        texte_offre = f"""Titre du poste : {offre.titre}
Description : {offre.description}
Localisation : {offre.localisation or 'Non précisée'}

Diplôme demandé : {offre.diplome_demande or 'Non précisé'}
Expérience requise : {offre.experience_annees or 0} an(s)

Compétences obligatoires : {', '.join(offre.competences_obligatoires or []) if offre.competences_obligatoires else 'Aucune'}
Compétences souhaitées : {', '.join(offre.competences_souhaitees or []) if offre.competences_souhaitees else 'Aucune'}
Langues : {', '.join(offre.langues or []) if offre.langues else 'Aucune'}
"""

        # 3. Lancer l'orchestrateur
        result = asyncio.run(run_workflow(
            job_description=texte_offre,
            cv_path=cv_path,
            diplome_path=diplome_path,
            cin_path=cin_path,
            candidate_id=str(cand.id_candidat),
            job_id=str(cand.id_offre),
        ))

        # 4. Traitement des résultats
        if result.get("status") == "Analyse terminée":
            cand.statut = StatutCandidature.ANALYSE_TERMINEE
            results = result.get("results", {})
            
            # Nettoyage des anciens résultats (si relance)
            db.query(ResultatAnalyse).filter_by(id_candidature=cand.id).delete()
            db.query(VerificationDocuments).filter_by(id_candidature=cand.id).delete()
            db.query(ProfilCandidat).filter_by(id_candidature=cand.id).delete()
            db.query(ExigencesStructurees).filter_by(id_offre=cand.id_offre).delete()

            # --- Agent 1 : Exigences ---
            if "exigences" in results:
                db.add(ExigencesStructurees(
                    id_offre=cand.id_offre,
                    titre_poste=results["exigences"].get("titre_poste"),
                    diplome_demande=results["exigences"].get("diplome_demande"),
                    niveau_diplome_min=results["exigences"].get("niveau_diplome_min"),
                    experience_min_annees=results["exigences"].get("experience_min_annees", 0),
                    competences_obligatoires=results["exigences"].get("competences_obligatoires", []),
                    competences_souhaitees=results["exigences"].get("competences_souhaitees", []),
                    langues=results["exigences"].get("langues", []),
                    missions=results["exigences"].get("missions", [])
                ))

            # --- Agent 2 : Profil ---
            if "profil" in results:
                db.add(ProfilCandidat(
                    id_candidature=cand.id,
                    nom=results["profil"].get("nom"),
                    prenom=results["profil"].get("prenom"),
                    email=results["profil"].get("email"),
                    telephone=results["profil"].get("telephone"),
                    formations=results["profil"].get("formations", []),
                    experiences=results["profil"].get("experiences", []),
                    competences=results["profil"].get("competences", []),
                    langues=results["profil"].get("langues", []),
                    certifications=results["profil"].get("certifications", []),
                    experience_totale_annees=results["profil"].get("experience_totale_annees", 0)
                ))

            # --- Agent 3 : Vérification ---
            if "verification" in results:
                v = results["verification"]
                try:
                    niveau_enum = NiveauConformite(v.get("niveau_conformite", "non_conforme").upper())
                except ValueError:
                    niveau_enum = NiveauConformite.NON_CONFORME

                db.add(VerificationDocuments(
                    id_candidature=cand.id,
                    infos_diplome=v.get("infos_diplome"),
                    infos_cin=v.get("infos_cin"),
                    documents_analyses=v.get("documents_analyses", []),
                    documents_manquants=v.get("documents_manquants", []),
                    documents_illisibles=v.get("documents_illisibles", []),
                    incoherences=v.get("incoherences", []),
                    niveau_conformite=niveau_enum,
                    score_coherence=v.get("score_coherence", 0),
                    resume=v.get("resume", "")
                ))

            # --- Agents 4 & 5 : Matching & Rapport ---
            if "matching" in results:
                m = results["matching"]
                r = results.get("rapport", {})
                
                avis_str = r.get("avis_indicatif", "a_etudier").upper().replace(" ", "_")
                try:
                    avis_enum = AvisIndicatif(avis_str)
                except ValueError:
                    avis_enum = AvisIndicatif.A_ETUDIER

                db.add(ResultatAnalyse(
                    id_candidature=cand.id,
                    score_global=m.get("score_global", 0.0),
                    details=m.get("details", []),
                    competences_correspondantes=m.get("competences_correspondantes", []),
                    competences_manquantes=m.get("competences_manquantes", []),
                    diplome_conforme=m.get("diplome_conforme", False),
                    experience_candidat_annees=m.get("experience_candidat_annees", 0.0),
                    rapport=r,
                    avis_indicatif=avis_enum
                ))

        else:
            cand.statut = StatutCandidature.ERREUR_DE_TRAITEMENT
            cand.message_erreur = str(result.get("error", "Erreur lors de l'analyse"))

        db.commit()
        logger.info(f"Traitement {candidature_id} terminé avec statut : {cand.statut}")

    except Exception as e:
        logger.exception(f"Erreur fatale lors du traitement {candidature_id}")
        db.rollback()
        cand = db.get(Candidature, candidature_id)
        if cand:
            cand.statut = StatutCandidature.ERREUR_DE_TRAITEMENT
            cand.message_erreur = str(e)
            db.commit()
    finally:
        db.close()