# Frontend React de Passerelle

Le dossier `dist/` contient la version **déjà construite** : `4_lancer_site.bat` suffit, sans Node.js.

## Si vous voulez modifier le design ou les pages
1. Installez **Node.js (version LTS)** : https://nodejs.org
2. Double-cliquez `6_frontend_dev.bat` (à la racine) : le frontend s'ouvre sur http://localhost:5173 et se met à jour à chaque sauvegarde.
   Lancez en parallèle `4_lancer_site.bat` : c'est l'API (port 8000) que le frontend appelle.
3. Quand vous avez fini, double-cliquez `7_reconstruire_frontend.bat` pour régénérer `dist/`.

## Où est quoi (src/) : un dossier par espace
- `visiteur/`   site public : `LayoutVisiteur`, `Home`, `OffreDetail`, `Comment`, `NotFound`
- `candidat/`   espace candidat : `GardeCandidat`, `LayoutCandidat`, `MonEspace` (adresse /candidat)
- `admin/`      espace recruteur : `GardeAdmin`, `LayoutAdmin`, `AdminOffres`, `OffreForm`, `AgentsLab` (adresse /admin)
- `commun/`     partagé : `Auth` (connexion / inscription), `Dock` (menu vertical), `Fond` (fond + retour en haut)
- `App.jsx`     toutes les routes, regroupées par espace
- `styles.css`  tout le design ; `scene.jsx` illustrations ; `ui.jsx` composants ; `api.js` client API ; `auth.jsx` connexion ; `toast.jsx` notifications
