import uuid
from pathlib import Path
from pydantic import BaseModel
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Candidature, Document, Offre, Utilisateur
from app.models.enums import StatutCandidature, TypeDocument
from app.models.resultats_agents import ResultatAnalyse, ExigencesStructurees, ProfilCandidat, VerificationDocuments
from app.schemas.candidature import CandidatureListeResponse, CandidatureOut, DocumentOut
from app.tasks import tache_traiter_candidature
from app.services.email_service import envoyer_email

router = APIRouter(prefix="/candidatures", tags=["candidatures"])

STORAGE = Path("/app/storage/candidatures")
STORAGE.mkdir(parents=True, exist_ok=True)

TYPES = {
    "cv": TypeDocument.CV,
    "diplome": TypeDocument.DIPLOME,
    "cin": TypeDocument.CIN,
}

EXTENSIONS_AUTORISEES = {
    "cv": {".pdf", ".docx"},
    "diplome": {".jpg", ".jpeg", ".png"},
    "cin": {".jpg", ".jpeg", ".png"},
}

class DecisionIn(BaseModel):
    decision: str # "accepte" ou "refuse"

def _enrichir(c: Candidature, db: Session) -> CandidatureOut:
    offre = db.get(Offre, c.id_offre)
    candidat = db.get(Utilisateur, c.id_candidat)
    statut_str = c.statut.value.lower() if hasattr(c.statut, "value") else str(c.statut).lower()

    return CandidatureOut(
        id=c.id, id_offre=c.id_offre, id_candidat=c.id_candidat, statut=statut_str,
        message_erreur=c.message_erreur,
        date_candidature=c.date_candidature.isoformat() if c.date_candidature else None,
        offre_titre=offre.titre if offre else None,
        candidat_nom=candidat.nom if candidat else None,
        candidat_prenom=candidat.prenom if candidat else None,
        documents=[
            DocumentOut(
                id=d.id,
                type=d.type.value.lower() if hasattr(d.type, "value") else str(d.type).lower(),
                chemin_fichier=d.chemin_fichier,
            )
            for d in c.documents
        ],
    )

async def _sauver_fichier(fichier: UploadFile, dossier: Path, type_doc: str) -> str:
    ext = Path(fichier.filename).suffix.lower()
    autorisees = EXTENSIONS_AUTORISEES[type_doc]
    if ext not in autorisees:
        raise HTTPException(400, f"Format non autorisé pour le {type_doc} : {ext}.")
    nom = f"{uuid.uuid4().hex}{ext}"
    chemin = dossier / nom
    contenu = await fichier.read()
    if len(contenu) > 5 * 1024 * 1024:
        raise HTTPException(400, "Fichier trop lourd (max 5 Mo)")
    chemin.write_bytes(contenu)
    return str(chemin)

@router.post("", response_model=CandidatureOut, status_code=status.HTTP_201_CREATED)
async def creer_candidature(
    background_tasks: BackgroundTasks,
    id_offre: int = Form(...), id_candidat: int = Form(...),
    cv: UploadFile = File(...), diplome: UploadFile = File(...), cin: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CandidatureOut:
    candidat = db.get(Utilisateur, id_candidat)
    if not candidat: raise HTTPException(404, "Candidat introuvable")
    offre = db.get(Offre, id_offre)
    if not offre: raise HTTPException(404, "Offre introuvable")
    if hasattr(offre.statut, "value") and offre.statut.value != "PUBLIEE":
        raise HTTPException(400, "Offre non ouverte aux candidatures")
    deja = db.scalar(select(Candidature).where(Candidature.id_offre == id_offre, Candidature.id_candidat == id_candidat))
    if deja: raise HTTPException(409, "Vous avez déjà postulé à cette offre")

    cand = Candidature(id_offre=id_offre, id_candidat=id_candidat, statut=StatutCandidature.EN_ATTENTE_DE_TRAITEMENT)
    db.add(cand)
    db.flush()

    dossier = STORAGE / str(cand.id)
    dossier.mkdir(parents=True, exist_ok=True)
    for cle, upload in [("cv", cv), ("diplome", diplome), ("cin", cin)]:
        chemin = await _sauver_fichier(upload, dossier, cle)
        db.add(Document(id_candidature=cand.id, type=TYPES[cle], chemin_fichier=chemin))

    db.commit()
    db.refresh(cand)

    # Emails
    background_tasks.add_task(
        envoyer_email,
        destinataire=candidat.email,
        sujet=f"Candidature reçue : {offre.titre}",
        contenu_texte=f"Bonjour {candidat.prenom},\n\nNous confirmons la réception de votre candidature pour '{offre.titre}'."
    )
    admin = db.get(Utilisateur, offre.id_admin)
    if admin:
        background_tasks.add_task(
            envoyer_email,
            destinataire=admin.email,
            sujet=f"Nouvelle candidature : {offre.titre}",
            contenu_texte=f"Bonjour {admin.prenom},\n\nUne nouvelle candidature a été reçue pour '{offre.titre}'."
        )

    return _enrichir(cand, db)

@router.get("", response_model=CandidatureListeResponse)
def lister_candidatures(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)) -> CandidatureListeResponse:
    user = db.get(Utilisateur, x_user_id) if x_user_id else None
    q = select(Candidature).order_by(Candidature.date_candidature.desc())
    if user and user.role.value == "CANDIDAT":
        q = q.where(Candidature.id_candidat == user.id)
    toutes = list(db.scalars(q).all())
    return CandidatureListeResponse(candidatures=[_enrichir(c, db) for c in toutes], total=len(toutes))

@router.post("/{candidature_id}/lancer-traitement")
def lancer_traitement(candidature_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidature, candidature_id)
    if not cand: raise HTTPException(404, "Candidature introuvable")
    if cand.statut not in [StatutCandidature.EN_ATTENTE_DE_TRAITEMENT, StatutCandidature.ERREUR_DE_TRAITEMENT]:
        raise HTTPException(400, "Cette candidature a déjà été traitée ou est en cours.")
    cand.statut = StatutCandidature.EN_COURS_DE_TRAITEMENT
    db.commit()
    tache_traiter_candidature.delay(candidature_id)
    return {"message": "Traitement envoyé aux agents IA (worker)."}

@router.get("/{candidature_id}/resultat")
def lire_resultat(candidature_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidature, candidature_id)
    if not cand: raise HTTPException(404, "Candidature introuvable")
    res = db.get(ResultatAnalyse, candidature_id)
    if not res: raise HTTPException(404, "Résultat non disponible")
    verif = db.get(VerificationDocuments, candidature_id)
    profil = db.get(ProfilCandidat, candidature_id)

    return {
        "candidature": _enrichir(cand, db),
        "score_global": res.score_global,
        "details": res.details,
        "competences_correspondantes": res.competences_correspondantes,
        "competences_manquantes": res.competences_manquantes,
        "diplome_conforme": res.diplome_conforme,
        "experience_candidat_annees": res.experience_candidat_annees,
        "rapport": res.rapport,
        "avis_indicatif": res.avis_indicatif.value if res.avis_indicatif else None,
        "verification": {
            "niveau_conformite": verif.niveau_conformite.value if verif else None,
            "score_coherence": verif.score_coherence if verif else None,
            "incoherences": verif.incoherences if verif else [],
            "resume": verif.resume if verif else None,
        } if verif else None,
        "profil": {
            "nom": profil.nom, "prenom": profil.prenom,
            "competences": profil.competences, "experience_totale_annees": profil.experience_totale_annees
        } if profil else None
    }

@router.get("/{candidature_id}/resultat-candidat")
def lire_resultat_candidat(candidature_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidature, candidature_id)
    if not cand: raise HTTPException(404, "Candidature introuvable")
    res = db.get(ResultatAnalyse, candidature_id)
    if not res: raise HTTPException(404, "Résultat non disponible (analyse non terminée)")
    verif = db.get(VerificationDocuments, candidature_id)

    return {
        "score_global": res.score_global,
        "competences_correspondantes": res.competences_correspondantes,
        "competences_manquantes": res.competences_manquantes,
        "diplome_conforme": res.diplome_conforme,
        "experience_candidat_annees": res.experience_candidat_annees,
        "niveau_conformite": verif.niveau_conformite.value if verif else None,
        "score_coherence": verif.score_coherence if verif else None,
    }

# ✅ NOUVELLE ROUTE : Télécharger un document
@router.get("/documents/{document_id}")
def telecharger_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document introuvable")
    
    chemin = Path(doc.chemin_fichier)
    if not chemin.exists():
        raise HTTPException(404, "Fichier physique introuvable")
        
    return FileResponse(chemin, filename=chemin.name)

# ✅ NOUVELLE ROUTE : Prendre une décision (Accepter/Refuser)
@router.post("/{candidature_id}/decision")
async def decider_candidature(candidature_id: int, payload: DecisionIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    cand = db.get(Candidature, candidature_id)
    if not cand: raise HTTPException(404, "Candidature introuvable")
    candidat = db.get(Utilisateur, cand.id_candidat)
    offre = db.get(Offre, cand.id_offre)
    
    sujet = "Votre candidature a été acceptée !" if payload.decision == "accepte" else "Suite à votre candidature"
    texte = f"Bonjour {candidat.prenom},\n\nNous avons le plaisir de vous informer que votre candidature pour le poste '{offre.titre}' a été retenue. Félicitations !" if payload.decision == "accepte" else f"Bonjour {candidat.prenom},\n\nNous vous remercions pour votre candidature pour le poste '{offre.titre}'. Malheureusement, nous ne donnerons pas suite..."
    
    background_tasks.add_task(envoyer_email, candidat.email, sujet, texte)
    return {"message": "Décision enregistrée et email envoyé."}



class TraitementLotIn(BaseModel):
    candidature_ids: List[int]

# ✅ NOUVELLE ROUTE : Traitement par lot
@router.post("/lancer-traitement-lot")
def lancer_traitement_lot(payload: TraitementLotIn, db: Session = Depends(get_db)):
    resultats = []
    for cand_id in payload.candidature_ids:
        cand = db.get(Candidature, cand_id)
        if cand and cand.statut in [StatutCandidature.EN_ATTENTE_DE_TRAITEMENT, StatutCandidature.ERREUR_DE_TRAITEMENT]:
            cand.statut = StatutCandidature.EN_COURS_DE_TRAITEMENT
            db.commit()
            tache_traiter_candidature.delay(cand_id)
            resultats.append(cand_id)
            
    return {"message": f"{len(resultats)} traitement(s) envoyé(s) au worker.", "ids": resultats}