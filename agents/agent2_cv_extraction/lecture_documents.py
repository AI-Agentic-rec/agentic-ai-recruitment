"""Lecture du texte d'un CV (PDF ou DOCX). Les CV scannés (images) demanderont l'OCR, prévu pour l'agent 3."""
from pathlib import Path

MAX_CARACTERES = 12000          # un CV normal en fait 3 000 à 6 000


def _lire_pdf(p: Path) -> str:
    import pdfplumber
    with pdfplumber.open(p) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _lire_docx(p: Path) -> str:
    from docx import Document
    doc = Document(str(p))
    lignes = [para.text for para in doc.paragraphs]
    for table in doc.tables:                       # beaucoup de CV sont mis en page avec des tableaux
        for ligne in table.rows:
            lignes.append(" | ".join(c.text.strip() for c in ligne.cells))
    return "\n".join(lignes)


def lire_cv(chemin) -> str:
    p = Path(chemin)
    if not p.exists():
        raise FileNotFoundError(f"Fichier introuvable : {p}")
    ext = p.suffix.lower()
    if ext == ".pdf":
        texte = _lire_pdf(p)
    elif ext == ".docx":
        texte = _lire_docx(p)
    else:
        raise ValueError(f"Format « {ext} » non pris en charge : utilisez PDF ou DOCX")
    texte = "\n".join(l.rstrip() for l in texte.splitlines() if l.strip())
    if len(texte) < 30:
        raise ValueError("Aucun texte extractible : le CV est peut-être un scan (image). L'OCR sera nécessaire.")
    return texte[:MAX_CARACTERES]
