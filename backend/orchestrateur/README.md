# Orchestrateur

**Responsable : Fatima**

Il enchaîne les agents d'une candidature : agents 1 et 2 en parallèle, puis 3, 4 et 5.

## Ce qu'il doit faire
- Lancer 1 et 2 en parallèle, puis respecter les dépendances (3 après 2 ; 4 après 1, 2 et 3 ; 5 après tous).
- **Valider** chaque sortie avec le schéma de l'agent.
- **Tracer** chaque étape (logs).
- Enregistrer chaque sortie en base au fur et à mesure.
- En cas d'erreur : statut « Erreur de traitement » avec le message, et possibilité de relancer.
- Passer l'Agent 3 par `sans_donnees_sensibles(...)` avant de transmettre aux agents 4 et 5.

Fichier attendu : `orchestrateur.py` et ses tests `test_orchestrateur.py`.
