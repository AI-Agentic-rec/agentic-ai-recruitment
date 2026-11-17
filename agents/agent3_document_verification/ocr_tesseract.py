import os
from pathlib import Path

from agents.common.llm_local import AgentError

CHEMINS_WINDOWS = (r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe")


def preparer_image(image):
    """Niveaux de gris, contraste automatique, agrandissement des petites images : améliore la lecture."""
    from PIL import Image, ImageOps
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    if min(gris.size) < 1000:
        gris = gris.resize((gris.width * 2, gris.height * 2), Image.LANCZOS)
    return gris


def lire_image(chemin: str, langue: str | None = None, psm: str | None = None) -> str:
    """Renvoie le texte lu sur l'image (chaîne vide si rien n'est lu). Lève AgentError avec un message clair en cas de problème."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise AgentError("OCR : bibliothèques manquantes. Installez-les avec : pip install pytesseract pillow")
    commande = os.getenv("TESSERACT_CMD") or next((c for c in CHEMINS_WINDOWS if Path(c).is_file()), None)
    if commande:
        pytesseract.pytesseract.tesseract_cmd = commande
    langue = langue or os.getenv("TESSERACT_LANG", "fra")
    psm = psm or os.getenv("TESSERACT_PSM", "6")
    try:
        with Image.open(chemin) as original:
            image = preparer_image(original)
        return pytesseract.image_to_string(image, lang=langue, config=f"--psm {psm}").strip()
    except pytesseract.TesseractNotFoundError:
        raise AgentError("OCR : Tesseract est introuvable. Installez-le (voir ocr_tesseract.py) ou définissez TESSERACT_CMD.")
    except pytesseract.TesseractError as erreur:
        raise AgentError(f"OCR : Tesseract a échoué ({erreur}). Le pack de langue « {langue} » est-il installé ?")
    except OSError as erreur:           # fichier absent, illisible ou format d'image inconnu
        raise AgentError(f"OCR : image illisible : {chemin} ({erreur})")
