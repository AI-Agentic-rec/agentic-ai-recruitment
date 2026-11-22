from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models import RoleUtilisateur, Utilisateur

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Schémas ---
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    nom: str
    prenom: str
    telephone: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    telephone: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    nom: str
    prenom: str
    telephone: str | None = None
    role: str

    @field_validator("role", mode="before")
    @classmethod
    def lowercase_role(cls, v):
        if hasattr(v, "value"): return v.value.lower()
        if isinstance(v, str): return v.lower()
        return v

    class Config:
        from_attributes = True

# --- Routes ---
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> Utilisateur:
    deja = db.scalar(select(Utilisateur).where(Utilisateur.email == payload.email))
    if deja is not None:
        raise HTTPException(409, "Email déjà utilisé")

    user = Utilisateur(
        email=payload.email, nom=payload.nom, prenom=payload.prenom,
        telephone=payload.telephone, mot_de_passe_hash=hash_password(payload.password),
        role=RoleUtilisateur.CANDIDAT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == payload.email))
    if user is None or not verify_password(payload.password, user.mot_de_passe_hash):
        raise HTTPException(401, "Identifiants invalides")

    return {
        "access_token": f"dev-token-{user.id}",
        "token_type": "bearer",
        "user": UserOut.model_validate(user).model_dump(mode="json"),
    }

@router.get("/me", response_model=UserOut)
def me(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)) -> Utilisateur:
    if x_user_id is None:
        raise HTTPException(401, "Non connecté")
    user = db.get(Utilisateur, x_user_id)
    if user is None:
        raise HTTPException(401, "Utilisateur inconnu")
    return user

# ✅ NOUVELLE ROUTE : Modifier son profil
@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db)
) -> Utilisateur:
    if x_user_id is None:
        raise HTTPException(401, "Non connecté")
    user = db.get(Utilisateur, x_user_id)
    if user is None:
        raise HTTPException(404, "Utilisateur introuvable")

    if payload.nom is not None: user.nom = payload.nom
    if payload.prenom is not None: user.prenom = payload.prenom
    if payload.telephone is not None: user.telephone = payload.telephone

    db.commit()
    db.refresh(user)
    return user