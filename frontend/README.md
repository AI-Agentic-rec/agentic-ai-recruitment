# Frontend

Les trois espaces. **La technologie :React** 

```
frontend/
├── static/                 images, styles communs
└── src/
    ├── espace_public/      offres, recherche, détail, parcours « Postuler »     (Zineb)
    ├── espace_candidat/    candidatures, statuts, résultats partiels            (Salah)
    ├── espace_admin/       offres, candidatures, lancer le traitement, résultats (Amina)
    ├── composants/         éléments d'interface réutilisables
    └── services/           appels à l'API du backend
```

> Si l'équipe choisit des **templates** (Jinja2 avec FastAPI) plutôt qu'une application séparée, ce dossier sera déplacé dans `backend/app/templates/` et `backend/app/static/` : décider **avant** de commencer à coder.

## Règles
- Le candidat ne voit **jamais** le rapport détaillé ni les incohérences (réservés à l'administrateur, sauf décision contraire de l'enseignant).
- Interfaces claires, responsives et cohérentes entre les trois espaces.
