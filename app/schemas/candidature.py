from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    type: str
    chemin_fichier: str

    class Config:
        from_attributes = True


class CandidatureOut(BaseModel):
    id: int
    id_offre: int
    id_candidat: int
    statut: str
    message_erreur: str | None = None
    date_candidature: str | None = None
    # Champs joints pour l'affichage
    offre_titre: str | None = None
    candidat_nom: str | None = None
    candidat_prenom: str | None = None
    documents: list[DocumentOut] = []


class CandidatureListeResponse(BaseModel):
    candidatures: list[CandidatureOut]
    total: int