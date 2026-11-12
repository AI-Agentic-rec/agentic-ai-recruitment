# backend/app : l'API

| Dossier | Contenu | Responsable |
|---|---|---|
| `api/routes/` | Une route par ressource : `auth`, `offres`, `candidatures`, `traitement`, `resultats` | Fatima, Amina |
| `api/dependencies/` | Contrôles d'accès : administrateur, candidat | Fatima |
| `core/` | Configuration (variables `.env`) et sécurité (JWT, hachage) | Fatima |
| `db/` | Connexion, modèles des tables (selon le MCD de `database/schema/`) | Abdo |
| `schemas/` | Formats d'entrée et de sortie de l'API (différents des schémas des agents) | Fatima, Amina |
| `services/` | Logique métier : emails, upload des documents, gestion des candidatures et des statuts | Amina, Abdo |

Point d'entrée de l'application : `main.py` (à créer par Fatima).
