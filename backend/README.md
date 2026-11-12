# Backend

API, base de données applicative et orchestrateur.

```
backend/
├── app/                 l'API (voir app/README.md)
├── orchestrateur/       enchaîne les 5 agents
└── tests/               tests du backend
```

| Partie | Responsable |
|---|---|
| Authentification (JWT), rôles, API | Fatima |
| Orchestrateur : agents, logs, erreurs, relance | Fatima |
| Offres, candidatures, statuts, emails, résultats | Amina |
| Base de données, upload sécurisé des documents | Abderrahmane |

## À respecter
- Les routes de l'API sont décrites dans `docs/api/` **avant** d'être codées (Fatima).
- Le traitement est **asynchrone** et déclenché **uniquement** par l'administrateur.
- Contrôle d'accès par rôle (admin, candidat) ; mots de passe hachés ; documents accessibles seulement à leur propriétaire et à l'administrateur.
- Les agents s'importent avec `from agents.<dossier>.<module> import ...`.
