# Passerelle - Plateforme de Recrutement Agentic AI

## Description du projet
**Passerelle** est une plateforme intelligente de recrutement basée sur une architecture **multi-agents (Agentic AI)**. Elle gère l'intégralité du processus de recrutement : de la publication d'une offre par un recruteur jusqu'à l'analyse automatisée (mais supervisée) des candidatures.

La particularité du projet réside dans l'utilisation de **5 agents IA spécialisés** orchestrés par **LangGraph**, capables de lire un CV, de vérifier des documents officiels (CIN, diplôme) via OCR, de comparer un profil aux exigences d'un poste et de générer un rapport explicatif.

>  **Règle d'or** : L'IA est une aide à la décision. Aucun traitement n'est lancé automatiquement, et **la décision finale de recrutement appartient toujours à l'humain**.

---

## Fonctionnalités Principales

### Espace Administrateur (Recruteur)
*   **Tableau de bord** : Vue d'ensemble des statistiques et Top 3 des meilleurs profils.
*   **Gestion des offres** : Création, modification, publication et clôture des annonces.
*   **Gestion des candidatures** : Consultation des dossiers, téléchargement des pièces jointes (CV, CIN, diplôme).
*   **Traitement IA** : Lancement manuel du workflow (individuel ou par lot).
*   **Analyse et Décision** : Consultation du score de matching, du rapport détaillé, export PDF du rapport, et envoi d'un email d'acceptation ou de refus au candidat.

### Espace Candidat
*   **Gestion du profil** : Modification des informations personnelles.
*   **Candidature simplifiée** : Dépôt sécurisé du CV (PDF), du diplôme (Image) et de la CIN (Image).
*   **Suivi en temps réel** : Consultation du statut d'avancement des candidatures.
*   **Transparence** : Accès aux résultats partiels (score de correspondance et compétences) une fois l'analyse terminée.

### Site Public (Visiteur)
*   Affichage des offres d'emploi publiées.
*   Système de recherche et de filtres (localisation, expérience, mots-clés).
*   Consultation détaillée des exigences du poste.

---

##  Stack Technique

| Couche | Technologies utilisées |
| :--- | :--- |
| **Frontend** | React 19, Vite, React Router, Lucide React, CSS personnalisé |
| **Backend / API** | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| **Base de données** | PostgreSQL 17 |
| **Tâches asynchrones** | Celery + Redis (gestion de la file d'attente) |
| **Orchestration IA** | LangGraph, LangChain |
| **Modèles de langage (LLM)** | Ollama (Mistral 7B) en local |
| **Lecture de documents** | pdfplumber (PDF), Tesseract OCR (Images CIN/Diplôme) |
| **Emails** | SMTP (Mailpit pour le dev, Gmail pour la prod) |
| **Déploiement** | Docker & Docker Compose |

---

## Architecture des Agents IA

Le workflow est géré par un orchestrateur central (`orchestrator_langgraph.py`) qui respecte les dépendances suivantes :
1.  **Agent 1 (Job Requirement)** & **Agent 2 (CV Extraction)** s'exécutent **en parallèle**.
2.  **Agent 3 (Document Verification)** analyse les images et compare avec le profil.
3.  **Agent 4 (Matching)** calcule un score pondéré (Compétences 40%, Expérience 20%, Diplôme 15%, etc.).
4.  **Agent 5 (Report)** rédige une synthèse explicative à partir des résultats des 4 premiers agents.

---

## Installation et Lancement

### Prérequis
*   [Docker](https://docs.docker.com/get-docker/) et Docker Compose
*   [Ollama](https://ollama.com/) installé sur la machine hôte (pour faire tourner Mistral 7B)
*   *(Optionnel)* Tesseract OCR installé localement (géré automatiquement dans Docker)

### Étapes de lancement

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-compte/agentic-ai-recruitment.git
   cd agentic-ai-recruitment