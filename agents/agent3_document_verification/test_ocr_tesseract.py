import json, os, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from agents.agent3_document_verification.agent3 import verifier_documents
from agents.agent3_document_verification.cas_test_agent3 import PROFIL_CV
from agents.common.llm_local import AgentError
from agents.common.niveaux_diplome import normaliser
from agents.agent3_document_verification.ocr_tesseract import lire_image

DIPLOME = ["UNIVERSITÉ FICTIVE DE CASABLANCA", "DIPLÔME DE MASTER EN INFORMATIQUE", "Délivré à : Mme Sara BENALI", "Année d'obtention : 2021"]
CIN = ["ROYAUME DU MAROC", "CARTE NATIONALE D'IDENTITÉ", "Nom : BENALI", "Prénom : Sara", "Né(e) le : 12/04/1998", "N° : AB123456"]


POLICES = ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def _police(taille):
    """Une vraie police est nécessaire : la police par défaut de Pillow ne sait pas dessiner les accents."""
    for nom in POLICES:
        try:
            return ImageFont.truetype(nom, taille), True
        except OSError:
            continue
    return ImageFont.load_default(size=taille), False


def ecrire_image(chemin, lignes, taille=38):
    police, _ = _police(taille)
    image = Image.new("RGB", (1300, 90 * len(lignes) + 80), "white")
    dessin = ImageDraw.Draw(image)
    for i, ligne in enumerate(lignes):
        dessin.text((60, 50 + 90 * i), ligne, fill="black", font=police)
    image.save(chemin)


def tesseract_disponible(dossier) -> bool:
    ecrire_image(Path(dossier, "essai.png"), ["Test OCR"])
    try:
        lire_image(str(Path(dossier, "essai.png")))
        return True
    except AgentError:
        return False


def test_lecture_d_un_diplome_et_d_une_cin():
    with tempfile.TemporaryDirectory() as d:
        if not tesseract_disponible(d):
            print("SKIP (Tesseract ou pack français absent)"); return
        ecrire_image(Path(d, "diplome.png"), DIPLOME); ecrire_image(Path(d, "cin.png"), CIN)
        t_dip, t_cin = normaliser(lire_image(str(Path(d, "diplome.png")))), normaliser(lire_image(str(Path(d, "cin.png"))))
    for mot in ("casablanca", "master", "informatique", "benali", "sara", "2021"):
        assert mot in t_dip, f"« {mot} » non lu sur le diplôme : {t_dip}"
    for mot in ("benali", "sara", "12 04 1998", "ab123456"):
        assert mot in t_cin, f"« {mot} » non lu sur la CIN : {t_cin}"
    if _police(38)[1]:                                   # avec une vraie police, les accents doivent aussi être lus
        assert "delivre" in t_dip and "prenom" in t_cin, f"accents mal lus : {t_dip} / {t_cin}"


def test_de_l_image_au_message_envoye_au_modele():
    with tempfile.TemporaryDirectory() as d:
        if not tesseract_disponible(d):
            print("SKIP (Tesseract ou pack français absent)"); return
        ecrire_image(Path(d, "diplome.png"), DIPLOME); ecrire_image(Path(d, "cin.png"), CIN)
        recus = []
        def modele(nom, system, messages, schema):
            recus.append(messages[0]["content"])
            return json.dumps({"infos_diplome": {"nom": "BENALI", "prenom": "Sara", "diplome": "Master", "specialite": "Informatique",
                                                 "etablissement": "Université Fictive de Casablanca", "date_obtention": "2021"},
                               "infos_cin": {"nom": "BENALI", "prenom": "Sara", "date_naissance": "1998-04-12", "numero_cin": "AB123456"}})
        r = verifier_documents(PROFIL_CV, image_diplome=str(Path(d, "diplome.png")), image_cin=str(Path(d, "cin.png")), llm=modele)
    message = normaliser(recus[0])
    assert "casablanca" in message and "ab123456" in message          # le texte lu par l'OCR est bien transmis au modèle
    assert r.niveau_conformite == "conforme" and r.documents_analyses == ["cv", "diplome", "cin"]


def test_erreurs_claires():
    try:
        lire_image("n_existe_pas.png"); assert False
    except AgentError as e:
        assert "illisible" in str(e) or "introuvable" in str(e)
    ancien = os.environ.get("TESSERACT_CMD")
    os.environ["TESSERACT_CMD"] = "/chemin/inexistant/tesseract"
    try:
        with tempfile.TemporaryDirectory() as d:
            ecrire_image(Path(d, "a.png"), ["x"])
            try:
                lire_image(str(Path(d, "a.png"))); assert False
            except AgentError as e:
                assert "Tesseract" in str(e)
    finally:
        os.environ.pop("TESSERACT_CMD") if ancien is None else os.environ.__setitem__("TESSERACT_CMD", ancien)


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
