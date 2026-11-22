import logging
import os
from email.message import EmailMessage
import aiosmtplib

logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EXPEDITEUR = os.getenv("SMTP_USER", "noreply@passerelle.test")

async def envoyer_email(destinataire: str, sujet: str, contenu_texte: str):
    """Envoie un vrai email via SMTP (Gmail)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("Identifiants SMTP non configurés. Email non envoyé.")
        return

    message = EmailMessage()
    message["From"] = f"Passerelle Recrutement <{EXPEDITEUR}>"
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(contenu_texte)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,  # ✅ LA CORRECTION EST ICI (start_tls au lieu de use_tls)
        )
        logger.info(f"✅ Email envoyé avec succès à {destinataire} : {sujet}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email à {destinataire} : {e}")