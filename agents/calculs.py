"""Calculs faits par le CODE (pas par le modèle) : un petit modèle de 7 milliards de paramètres se trompe sur les dates.

Convention :
- « AAAA-MM » (ou « mars 2021 », « 03/2021 ») : mois précis, comptés en entier (juillet → décembre = 6 mois).
- « AAAA » seul : milieu d'année (« 2021 - 2023 » = 24 mois).
- date_fin absente (None) : poste actuel, compté jusqu'au mois courant.
"""
import re
from datetime import date

MOIS = {"janvier": 1, "janv": 1, "février": 2, "fevrier": 2, "févr": 2, "fevr": 2, "mars": 3, "avril": 4, "avr": 4,
        "mai": 5, "juin": 6, "juillet": 7, "juil": 7, "août": 8, "aout": 8, "septembre": 9, "sept": 9,
        "octobre": 10, "oct": 10, "novembre": 11, "nov": 11, "décembre": 12, "decembre": 12, "déc": 12, "dec": 12}


def parse_date(texte):
    """Renvoie (année, mois) ou (année, None) si seule l'année est connue, ou None."""
    if not texte:
        return None
    t = str(texte).strip().lower()
    m = re.search(r"((?:19|20)\d{2})[-/.](\d{1,2})", t)           # 2021-03
    if m and 1 <= int(m.group(2)) <= 12:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"\b(\d{1,2})[-/.]((?:19|20)\d{2})", t)         # 03/2021
    if m and 1 <= int(m.group(1)) <= 12:
        return int(m.group(2)), int(m.group(1))
    a = re.search(r"(?:19|20)\d{2}", t)
    if not a:
        return None
    for nom, num in MOIS.items():                                  # « mars 2021 »
        if re.search(rf"\b{nom}\b", t):
            return int(a.group(0)), num
    return int(a.group(0)), None


def intervalle_mois(date_debut, date_fin, aujourdhui: date | None = None):
    """Intervalle [début, fin[ en numéro de mois, ou None si les dates sont inutilisables."""
    aujourdhui = aujourdhui or date.today()
    d = parse_date(date_debut)
    if d is None:
        return None
    debut = d[0] * 12 + ((d[1] - 1) if d[1] else 6)
    if date_fin in (None, ""):
        fin = aujourdhui.year * 12 + aujourdhui.month               # poste actuel : mois courant inclus
    else:
        f = parse_date(date_fin)
        if f is None:
            return None
        fin = f[0] * 12 + (f[1] if f[1] else 6)
    return (debut, fin) if fin > debut else None


def union_mois(intervalles) -> int:
    """Total de mois couverts, sans compter deux fois les périodes qui se chevauchent."""
    total, fin_courante = 0, None
    for debut, fin in sorted(intervalles):
        if fin_courante is None or debut > fin_courante:
            total += fin - debut
            fin_courante = fin
        elif fin > fin_courante:
            total += fin - fin_courante
            fin_courante = fin
    return total


def completer_profil(profil, aujourdhui: date | None = None):
    """Remplit duree_annees de chaque expérience et experience_totale_annees (écrase toute valeur du modèle)."""
    intervalles = []
    for exp in profil.experiences:
        iv = intervalle_mois(exp.date_debut, exp.date_fin, aujourdhui)
        exp.duree_annees = round((iv[1] - iv[0]) / 12, 2) if iv else None
        if iv:
            intervalles.append(iv)
    profil.experience_totale_annees = round(union_mois(intervalles) / 12, 2)
    return profil
