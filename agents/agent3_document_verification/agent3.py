"""
AGENT 3 : Document Verification
OCR Tesseract + extraction structurée par document via Ollama.

Responsabilité unique :
Vérifier que le diplôme et la CIN sont lisibles, valides et cohérents
entre eux et avec le CV.

Pipeline :
1. Lecture des images avec Tesseract.
2. Extraction séparée du diplôme et de la CIN à partir du texte OCR.
3. Normalisation déterministe (dates, valeurs vides, erreurs OCR).
4. Comparaison en Python :
  - CV <-> diplôme, CV <-> CIN
  - diplôme <-> CIN
  - validité de la CIN (expiration)
  - champs manquants
5. Calcul du niveau de conformité et du score.

Sortie : VerificationDocuments, destinée aux agents 4 et 5.
Le numéro de CIN doit être retiré (sans_donnees_sensibles) avant
transmission aux agents 4 et 5.
"""

import difflib
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from agents.common.llm_local import AgentError, executer_agent
from agents.agent3_document_verification.ocr_tesseract import lire_image
from agents.common.schemas import (
    BaseSchema,
    ContexteCandidature,
    Incoherence,
    InfosCIN,
    InfosDiplome,
    ProfilCandidat,
    VerificationDocuments,
)
from agents.common.niveaux_diplome import (
    niveau_diplome as _niveau,
    normaliser as _norm,
)
from agents.agent3_document_verification.prompts_agent3 import (
    PROMPT_EXTRACTION_DOCUMENT,
)


logger = logging.getLogger("agent3")
NUMERO_AGENT = 3


class ExtractionDocuments(BaseSchema):
    """Regroupe les informations extraites du diplôme et de la CIN."""

    infos_diplome: InfosDiplome
    infos_cin: InfosCIN


class _SeulDiplome(BaseSchema):
    infos_diplome: InfosDiplome


class _SeuleCIN(BaseSchema):
    infos_cin: InfosCIN


# =============================================================================
# OUTILS
# =============================================================================

VALEURS_VIDES = {
    "NON RENSEIGNE", "NON RENSEIGNÉ", "N/A", "NA", "INCONNU", "NULL", "NONE", "-", "",
}


def _cle(texte) -> str:
    """Normalise une chaîne et supprime les espaces."""
    return _norm(texte).replace(" ", "")


def _tokens(texte) -> set:
    return set(_norm(texte).split())


def _meme_nom(a, b) -> bool:
    """
    Noms identiques après normalisation, ou mots de l'un inclus dans l'autre
    (ex. « Mohamed Amine » / « Amine »).
    """
    if _cle(a) == _cle(b):
        return True
    ta, tb = _tokens(a), _tokens(b)
    return bool(ta) and bool(tb) and (ta <= tb or tb <= ta)


def _ressemblance(a, b) -> float:
    return difflib.SequenceMatcher(None, _cle(a), _cle(b)).ratio()


def _annee(valeur) -> Optional[int]:
    m = re.search(r"(?:19|20)\d{2}", valeur or "")
    return int(m.group()) if m else None


def _libelle(diplome, specialite) -> str:
    if diplome and specialite:
        return f"{diplome} ({specialite})"
    return diplome or specialite or "?"


def _iso(date_str: Optional[str]) -> Optional[str]:
    """Convertit JJ/MM/AAAA en AAAA-MM-JJ (sinon renvoie la valeur telle quelle)."""
    if not date_str:
        return date_str
    m = re.fullmatch(
        r"\s*(\d{1,2})[/.\\-](\d{1,2})[/.\\-](\d{4})\s*", date_str
    )
    return (
        f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        if m
        else date_str
    )


def _nettoyer(valeur):
    """Transforme les placeholders (« NON RENSEIGNE »...) en None."""
    if isinstance(valeur, str) and valeur.strip().upper() in VALEURS_VIDES:
        return None
    return valeur


def _masquer(texte: str) -> str:
    """Masque les numéros de CIN dans les logs."""
    return re.sub(
        r"\b[A-Za-z]{1,2}\s?\d{5,8}\b|TEST-CIN-\d+",
        "[N° MASQUÉ]",
        texte or "",
    )


def _cin_expiree(cin: InfosCIN, aujourdhui: Optional[date] = None) -> bool:
    """True si la date d'expiration est lisible et dépassée."""
    try:
        exp = datetime.strptime(_iso(cin.date_expiration), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return False
    return exp < (aujourdhui or date.today())


# =============================================================================
# COMPARAISONS EN CODE
# =============================================================================

CHAMPS_CIN = (
    ("nom", "nom"),
    ("prenom", "prénom"),
    ("numero_cin", "numéro"),
    ("date_expiration", "date d'expiration"),
)

CHAMPS_DIPLOME = (
    ("diplome", "type de diplôme"),
    ("nom", "nom du titulaire"),
    ("prenom", "prénom du titulaire"),
    ("etablissement", "établissement"),
    ("date_obtention", "date d'obtention"),
)


def _identite(
    profil: ProfilCandidat,
    nom_doc,
    prenom_doc,
    cle_doc: str,
    texte_doc: str,
) -> list[Incoherence]:
    """Compare nom et prénom du CV à ceux d'un document."""
    incoherences = []

    for libelle, valeur_cv, valeur_doc in (
        ("nom", profil.nom, nom_doc),
        ("prénom", profil.prenom, prenom_doc),
    ):
        if valeur_cv and valeur_doc and not _meme_nom(valeur_cv, valeur_doc):
            gravite = (
                "faible"
                if _ressemblance(valeur_cv, valeur_doc) >= 0.8
                else "elevee"
            )
            incoherences.append(
                Incoherence(
                    type="identite",
                    gravite=gravite,
                    documents=["cv", cle_doc],
                    description=(
                        f"Le {libelle} est « {valeur_cv} » sur le CV "
                        f"mais « {valeur_doc} » {texte_doc}."
                    ),
                )
            )

    return incoherences


def _croiser_documents(
    diplome: Optional[InfosDiplome],
    cin: Optional[InfosCIN],
) -> list[Incoherence]:
    """
    Compare directement le diplôme et la CIN.
    Détecte les cas où les deux documents ne désignent pas la même personne.
    """
    incoherences = []
    if diplome is None or cin is None:
        return incoherences

    for attr, libelle in (("nom", "nom"), ("prenom", "prénom")):
        a, b = getattr(diplome, attr), getattr(cin, attr)
        if not (a and b) or _cle(a) == _cle(b):
            continue

        ta, tb = _tokens(a), _tokens(b)
        if ta <= tb or tb <= ta:
            gravite = "moyenne"
        elif _ressemblance(a, b) >= 0.8:
            gravite = "faible"
        else:
            gravite = "elevee"

        incoherences.append(
            Incoherence(
                type="identite",
                gravite=gravite,
                documents=["diplome", "cin"],
                description=(
                    f"Le {libelle} est « {a} » sur le diplôme "
                    f"mais « {b} » sur la CIN."
                ),
            )
        )

    return incoherences


def comparer_en_code(
    profil: ProfilCandidat,
    diplome: Optional[InfosDiplome],
    cin: Optional[InfosCIN],
    aujourdhui: Optional[date] = None,
) -> list[Incoherence]:
    """
    Compare le CV au diplôme et à la CIN, puis le diplôme à la CIN.
    Un document None (manquant ou illisible) est traité par l'appelant.
    """
    incoherences = []

    if cin is not None:
        manque = [
            lib for attr, lib in CHAMPS_CIN
            if not getattr(cin, attr, None)
        ]
        if manque:
            incoherences.append(
                Incoherence(
                    type="autre",
                    gravite="moyenne",
                    documents=["cin"],
                    description=(
                        "Information illisible ou absente sur la CIN : "
                        f"{', '.join(manque)}. "
                        "Vérification manuelle recommandée."
                    ),
                )
            )

        if _cin_expiree(cin, aujourdhui):
            incoherences.append(
                Incoherence(
                    type="autre",
                    gravite="elevee",
                    documents=["cin"],
                    description=(
                        f"CIN expirée (date d'expiration : {cin.date_expiration})."
                    ),
                )
            )

        incoherences += _identite(
            profil, cin.nom, cin.prenom, "cin", "sur la CIN"
        )

    if diplome is not None:
        manque = [
            lib for attr, lib in CHAMPS_DIPLOME
            if not getattr(diplome, attr, None)
        ]
        if manque:
            incoherences.append(
                Incoherence(
                    type="autre",
                    gravite="moyenne",
                    documents=["diplome"],
                    description=(
                        "Information illisible ou absente sur le diplôme : "
                        f"{', '.join(manque)}. "
                        "Vérification manuelle recommandée."
                    ),
                )
            )

        incoherences += _identite(
            profil, diplome.nom, diplome.prenom, "diplome", "sur le diplôme"
        )

        niv_dip = (
            _niveau(diplome.diplome)
            or _niveau(diplome.diplome, diplome.specialite)
        )

        if profil.formations and niv_dip is not None:
            niveau_f = lambda f: (
                _niveau(f.diplome) or _niveau(f.diplome, f.specialite)
            )

            meme_niveau = [
                f for f in profil.formations if niveau_f(f) == niv_dip
            ]

            if not meme_niveau:
                f = max(profil.formations, key=lambda f: niveau_f(f) or -1)
                incoherences.append(
                    Incoherence(
                        type="diplome",
                        gravite="elevee",
                        documents=["cv", "diplome"],
                        description=(
                            f"Le CV indique « {_libelle(f.diplome, f.specialite)} » "
                            f"mais le diplôme fourni est "
                            f"« {_libelle(diplome.diplome, diplome.specialite)} »."
                        ),
                    )
                )
            else:
                f = meme_niveau[0]
                a_cv = _annee(f.date_fin)
                a_dip = _annee(diplome.date_obtention)

                if a_cv and a_dip and a_cv != a_dip:
                    incoherences.append(
                        Incoherence(
                            type="date",
                            gravite="moyenne",
                            documents=["cv", "diplome"],
                            description=(
                                f"Année d'obtention : {a_cv} sur le CV, "
                                f"{a_dip} sur le diplôme."
                            ),
                        )
                    )

                if (
                    f.etablissement
                    and diplome.etablissement
                    and _ressemblance(f.etablissement, diplome.etablissement) < 0.8
                ):
                    incoherences.append(
                        Incoherence(
                            type="diplome",
                            gravite="moyenne",
                            documents=["cv", "diplome"],
                            description=(
                                f"Établissement : « {f.etablissement} » "
                                f"sur le CV, « {diplome.etablissement} » "
                                "sur le diplôme."
                            ),
                        )
                    )

                if (
                    f.specialite
                    and diplome.specialite
                    and not _meme_nom(f.specialite, diplome.specialite)
                    and _ressemblance(f.specialite, diplome.specialite) < 0.6
                ):
                    incoherences.append(
                        Incoherence(
                            type="diplome",
                            gravite="moyenne",
                            documents=["cv", "diplome"],
                            description=(
                                f"Spécialité : « {f.specialite} » sur le CV, "
                                f"« {diplome.specialite} » sur le diplôme."
                            ),
                        )
                    )

    incoherences += _croiser_documents(diplome, cin)

    return incoherences


# =============================================================================
# CALCUL DE LA CONFORMITÉ
# =============================================================================

PENALITES = {
    "elevee": 40,
    "moyenne": 20,
    "faible": 10,
}


def calculer_conformite(
    incoherences: list[Incoherence],
) -> tuple[str, int]:
    """
    Score = 100 - pénalités (40 / 20 / 10), minimum 0.

    conforme : aucune incohérence ;
    non_conforme : au moins une incohérence élevée ou score < 50 ;
    partiellement_conforme : autres cas.
    """
    score = max(0, 100 - sum(PENALITES[i.gravite] for i in incoherences))

    if not incoherences:
        return "conforme", score

    if any(i.gravite == "elevee" for i in incoherences) or score < 50:
        return "non_conforme", score

    return "partiellement_conforme", score


# =============================================================================
# EXTRACTION ET NORMALISATION
# =============================================================================

def _normaliser(extraction: ExtractionDocuments) -> ExtractionDocuments:
    """Normalisations déterministes après l'extraction."""
    cin, dip = extraction.infos_cin, extraction.infos_diplome

    for infos in (cin, dip):
        for champ in type(infos).model_fields:
            valeur = getattr(infos, champ)
            if isinstance(valeur, str):
                setattr(infos, champ, _nettoyer(valeur.strip()))

    cin.date_naissance = _iso(cin.date_naissance)
    cin.date_expiration = _iso(cin.date_expiration)
    dip.date_obtention = _iso(dip.date_obtention)

    if cin.numero_cin:
        cin.numero_cin = re.sub(r"\s", "", cin.numero_cin).upper()

    if dip.etablissement:
        dip.etablissement = re.sub(
            r"(?i)(hassan\s)[Il|][Il|]\b", r"\1II", dip.etablissement
        )

    return extraction


def _extraire_document_seul(
    type_doc: str,
    texte_ocr: Optional[str],
    schema_cls: type[BaseSchema],
    llm=None,
    max_essais: int = 3,
) -> BaseSchema:
    """Extrait un seul document (diplôme ou CIN) avec un prompt dédié."""
    if not texte_ocr or not texte_ocr.strip():
        cle = "infos_diplome" if schema_cls is _SeulDiplome else "infos_cin"
        return schema_cls.model_validate({cle: {}})

    message = (
        f"Type de document : {type_doc}\n\n"
        f"Texte OCR :\n{texte_ocr}"
    )

    return executer_agent(
        NUMERO_AGENT,
        PROMPT_EXTRACTION_DOCUMENT,
        message,
        schema_cls,
        llm=llm,
        max_essais=max_essais,
        images=None,
    )


def _texte_du_document(nom: str, texte, image, ocr, ref: str) -> Optional[str]:
    """Retourne le texte du document ; None si le document n'est pas fourni."""
    if texte is not None and texte.strip():
        return texte

    if image:
        if not Path(image).is_file():
            raise AgentError(
                f"Agent 3 : fichier introuvable pour {nom} : {image}"
            )
        lu = (ocr or lire_image)(image)
        logger.info("%s Agent 3, texte lu sur %s :\n%s", ref, nom, _masquer(lu))
        return lu

    return None


def _vide(objet: BaseSchema) -> bool:
    return not any(objet.model_dump().values())


def verifier_documents(
    profil_cv,
    texte_diplome: Optional[str] = None,
    texte_cin: Optional[str] = None,
    image_diplome: Optional[str] = None,
    image_cin: Optional[str] = None,
    contexte: Optional[ContexteCandidature] = None,
    llm=None,
    ocr=None,
    max_essais: int = 3,
    aujourdhui: Optional[date] = None,
) -> VerificationDocuments:

    profil = (
        profil_cv
        if isinstance(profil_cv, ProfilCandidat)
        else ProfilCandidat.model_validate(profil_cv)
    )

    ref = (
        f"[candidature {contexte.candidate_id} / offre {contexte.job_id}]"
        if contexte
        else "[candidature ?]"
    )

    # Étape 1 : lecture OCR.
    textes = {
        "diplome": _texte_du_document(
            "le diplôme", texte_diplome, image_diplome, ocr, ref
        ),
        "cin": _texte_du_document(
            "la CIN", texte_cin, image_cin, ocr, ref
        ),
    }

    manquants = [d for d, t in textes.items() if t is None]
    illisibles = [
        d for d, t in textes.items()
        if t is not None and not t.strip()
    ]

    extraction = ExtractionDocuments(
        infos_diplome=InfosDiplome(),
        infos_cin=InfosCIN(),
    )

    # Étape 2 : extraction séparée diplôme et CIN.
    if len(manquants) + len(illisibles) < 2:
        res_dip = _extraire_document_seul(
            "diplôme",
            textes["diplome"],
            _SeulDiplome,
            llm=llm,
            max_essais=max_essais,
        )
        res_cin = _extraire_document_seul(
            "CIN",
            textes["cin"],
            _SeuleCIN,
            llm=llm,
            max_essais=max_essais,
        )

        # Étape 3 : normalisation déterministe.
        extraction = _normaliser(
            ExtractionDocuments(
                infos_diplome=res_dip.infos_diplome,
                infos_cin=res_cin.infos_cin,
            )
        )

    infos = {
        "diplome": extraction.infos_diplome,
        "cin": extraction.infos_cin,
    }

    for d in ("diplome", "cin"):
        if d in manquants or d in illisibles:
            infos[d] = None
        elif _vide(infos[d]):
            illisibles.append(d)
            infos[d] = None

    # Étape 4 : incohérences.
    incoherences = []

    for d in manquants:
        incoherences.append(
            Incoherence(
                type="autre",
                gravite="elevee",
                documents=[d],
                description=(
                    f"Document manquant : {d.upper() if d == 'cin' else d}. "
                    "Vérification impossible."
                ),
            )
        )

    for d in illisibles:
        incoherences.append(
            Incoherence(
                type="autre",
                gravite="moyenne",
                documents=[d],
                description=(
                    f"Document illisible : {d.upper() if d == 'cin' else d}. "
                    "Vérification manuelle recommandée."
                ),
            )
        )

    incoherences += comparer_en_code(
        profil, infos["diplome"], infos["cin"], aujourdhui
    )

    # Étape 5 : score et niveau.
    niveau, score = calculer_conformite(incoherences)

    resume = (
        "Aucune incohérence détectée entre le CV, le diplôme et la CIN."
        if not incoherences
        else (
            f"{len(incoherences)} point(s) à vérifier : "
            + " ; ".join(i.description for i in incoherences)
        )
    )

    logger.info(
        "%s Agent 3 terminé : %s, score de cohérence %d", ref, niveau, score
    )

    return VerificationDocuments(
        infos_diplome=infos["diplome"],
        infos_cin=infos["cin"],
        documents_analyses=(
            ["cv"] + [d for d in ("diplome", "cin") if infos[d] is not None]
        ),
        documents_manquants=manquants,
        documents_illisibles=illisibles,
        incoherences=incoherences,
        niveau_conformite=niveau,
        score_coherence=score,
        resume=resume,
    )


def sans_donnees_sensibles(
    verification: VerificationDocuments,
) -> VerificationDocuments:
    """
    Retourne une copie sans le numéro de CIN.
    À appeler avant de transmettre le résultat aux agents 4 et 5.
    """
    if verification.infos_cin is None:
        return verification

    return verification.model_copy(
        update={
            "infos_cin": verification.infos_cin.model_copy(
                update={"numero_cin": None}
            )
        }
    )


# =============================================================================
# EXÉCUTION DIRECTE / TESTS MANUELS
# =============================================================================

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    ap = argparse.ArgumentParser(description="Agent 3 : vérification des documents")
    ap.add_argument("--diplome")
    ap.add_argument("--cin")
    ap.add_argument("--profil")
    args = ap.parse_args()

    if args.diplome or args.cin:
        from agents.agent3_document_verification.cas_test_agent3 import PROFIL_CV

        profil = (
            json.loads(Path(args.profil).read_text(encoding="utf-8"))
            if args.profil
            else PROFIL_CV
        )

        resultat = verifier_documents(
            profil, image_diplome=args.diplome, image_cin=args.cin
        )
        print(resultat.model_dump_json(indent=2))

    else:
        from agents.agent3_document_verification.cas_test_agent3 import (
            CAS_COHERENT,
            CAS_INCOHERENT,
        )

        for nom, cas in [("COHÉRENT", CAS_COHERENT), ("INCOHÉRENT", CAS_INCOHERENT)]:
            print(f"\n=== Cas {nom} ===")
            print(verifier_documents(**cas).model_dump_json(indent=2))