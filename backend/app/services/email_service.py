import logging
from email.message import EmailMessage
import aiosmtplib

logger = logging.getLogger(__name__)

# Configuration (Mailpit tourne sur le port 1025 en local)
SMTP_SERVER = "mailpit"
SMTP_PORT = 1025
EXPEDITEUR = "Passerelle Recrutement <noreply@passerelle.test>"

async def envoyer_email(destinataire: str, sujet: str, contenu_texte: str):
    """Envoie un email de manière asynchrone."""
    message = EmailMessage()
    message["From"] = EXPEDITEUR
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(contenu_texte)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            use_tls=False, # Mailpit n'utilise pas de TLS en local
        )
        logger.info(f"Email envoyé à {destinataire} : {sujet}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email à {destinataire} : {e}")