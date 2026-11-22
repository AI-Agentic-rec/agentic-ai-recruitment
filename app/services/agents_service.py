import asyncio
import traceback

from app.db.session import SessionLocal
from app.models import Candidature, Document, Offre
from app.models.enums import StatutCandidature, TypeDocument
# Import de ton orchestrateur (adapte le chemin si besoin)
from backend.orchestrateur.orchestrator_langgraph import run_workflow

def _trouver_doc(candidature, type_doc: TypeDocument):
    """Retourne le chemin d'un document par son type."""
    for d in candidature.documents:
        if d.type == type_doc:
            return d.chemin_fichier
    return None

async def _run_async_traitement(candidature_id: int):
    """Fonction asynchrone qui appelle vraiment ton orchestrateur."""
    db = SessionLocal()
    try:
        cand = db.get(Candidature, candidature_id)
        if not cand: return
        
        offre = db.get(Offre, cand.id_offre)
        
        # Récupération des chemins de fichiers
        cv_path = _trouver_doc(cand, TypeDocument.CV)
        diplome_path = _trouver_doc(cand, TypeDocument.DIPLOME)
        cin_path = _trouver_doc(cand, TypeDocument.CIN)

        if not cv_path or not diplome_path:
            raise ValueError("Documents manquants (CV ou Diplôme)")

        # APPEL DE TON ORCHESTRATEUR
        # On passe la description de l'offre, les chemins des fichiers et les IDs
        result = await run_workflow(
            job_description=offre.description,
            cv_path=cv_path,
            diplome_path=diplome_path,
            cin_path=cin_path,
            candidate_id=str(cand.id_candidat),
            job_id=str(cand.id_offre),
        )

        # Mise à jour du statut selon le résultat
        if result["status"] == "Analyse terminée":
            cand.statut = StatutCandidature.ANALYSE_TERMINEE
            # ⚠️ Idéalement, ici tu insères aussi le rapport dans la table resultat_analyse
            # db.add(ResultatAnalyse(id_candidature=cand.id, score=result["results"]["matching"]["score_global"], ...))
        else:
            cand.statut = StatutCandidature.ERREUR_DE_TRAITEMENT
            cand.message_erreur = result.get("error", {}).get("message", "Erreur inconnue")
            
        db.commit()

    except Exception as e:
        traceback.print_exc()
        # En cas d'erreur fatale, on repasse le statut en erreur
        db2 = SessionLocal()
        cand = db2.get(Candidature, candidature_id)
        if cand:
            cand.statut = StatutCandidature.ERREUR_DE_TRAITEMENT
            cand.message_erreur = str(e)
            db2.commit()
        db2.close()
    finally:
        db.close()

def executer_traitement_ia(candidature_id: int):
    """Point d'entrée synchrone appelé par FastAPI BackgroundTasks."""
    # Comme FastAPI BackgroundTasks est synchrone, on crée une boucle asyncio
    # pour exécuter la fonction async de l'orchestrateur.
    asyncio.run(_run_async_traitement(candidature_id))