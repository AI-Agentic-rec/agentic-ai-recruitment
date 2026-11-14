# Team Responsibilities
## Agentic AI Recruitment Platform

This document records the task ownership shown in the team's project board.

## Team members

| Initial / avatar | Team member |
|---|---|
| Green **A** | Abderrahmane |
| **S** | Salah |
| **O** | Oumaima |
| **Z** | Zineb |
| **F** | Fatima |
| Blue **A** | Amina |

> **Important:** Green A and blue A represent two different people: Abderrahmane and Amina.

## Responsibility rules

- **All team** means the task is shared by all six members.
- The named owner is responsible for coordinating the task and making sure it is completed.
- Shared tasks require everyone to review and agree on the result.
- The task priorities and statuses below reflect the screenshot: all tasks are currently **To do**.

## Task assignments

| # | Task | Responsible member(s) | Priority | Status |
|---:|---|---|---|---|
| 1 | Créer le dépôt Git | Abderrahmane | Urgent | To do |
| 2 | Figer les schémas JSON/Pydantic des 5 agents | **All team** | Urgent | To do |
| 3 | Figer les endpoints de l'API et le MCD | Fatima | Urgent | To do |
| 4 | Figer le MCD et UML : diagramme de classes | Amina | High | To do |
| 5 | Mocks JSON : exemple de sortie de chaque agent dans `/samples` | **All team** | Urgent | To do |
| 6 | Valider et geler les contrats : schémas JSON, endpoints API, MCD | Oumaima | Urgent | To do |
| 7 | Docker Compose et base de données | Abderrahmane | High | To do |
| 8 | Script de seed : compte admin, compte candidat, offre de test | Amina | High | To do |
| 9 | Authentification, rôles admin/candidat (JWT) | Fatima | High | To do |
| 10 | Modèle Offre et CRUD (brouillon/publier/clôturer) | Abderrahmane | High | To do |
| 11 | Modèle Candidature, statuts, emails (Mailtrap) | Amina | High | To do |
| 12 | Squelette orchestrateur avec agents mock | Fatima | High | To do |
| 13 | Pages publiques : accueil, recherche, détail offre | Zineb | High | To do |
| 14 | Squelette espace candidat | Salah | Normal | To do |
| 15 | Agent 1 : prompt et prototype | Zineb | High | To do |
| 16 | Agent 2 : prompt et prototype | Salah | High | To do |
| 17 | Agent 3 : prompt et prototype | Oumaima | High | To do |
| 18 | Agent 4 : prototype du score sur JSON d'exemple | Abderrahmane | High | To do |
| 19 | Agent 5 : prompt et prototype du rapport sur JSON d'exemple | Fatima | High | To do |
| 20 | Agent 5 : gabarit du rapport (points forts, manques, incohérences, conclusion) | Amina | High | To do |
| 21 | Cahier des charges et analyse des besoins | Zineb | Urgent | To do |
| 22 | UML : diagramme de cas d'utilisation | Salah | High | To do |
| 23 | UML : diagramme de séquence du workflow | Oumaima | High | To do |

## Member-by-member summary

### Abderrahmane
- Create the Git repository.
- Set up Docker Compose and the database.
- Implement the Job Offer model and CRUD.
- Implement Agent 4: scoring prototype using example JSON.

### Salah
- Build the candidate portal skeleton.
- Implement Agent 2: CV extraction prompt and prototype.
- Create the UML use-case diagram.

### Oumaima
- Validate and freeze the API, JSON schema, and database-model contracts.
- Implement Agent 3: document-verification prompt and prototype.
- Create the UML workflow sequence diagram.

### Zineb
- Prepare the requirements document and needs analysis.
- Build the public pages: home, job search, and job details.
- Implement Agent 1: job-requirement prompt and prototype.

### Fatima
- Define/finalize the API endpoints and MCD.
- Implement authentication and admin/candidate JWT roles.
- Build the orchestrator skeleton with mock agents.
- Implement Agent 5: report prompt and prototype using example JSON.

### Amina
- Create the UML class diagram.
- Prepare the seed script with admin, candidate, and test offer.
- Implement the Application model, statuses, and emails (Mailtrap).
- Create the Agent 5 report template.

### All six members
- Agree on and freeze the JSON/Pydantic schemas for all five agents.
- Prepare example JSON outputs for every agent in `/samples`.

## Coordination and hand-off rules

1. Agree on the shared JSON/Pydantic contracts before implementing agent integrations.
2. Keep each agent in a separate module and use the agreed input/output schemas.
3. Work on separate feature branches; avoid committing directly to `main`.
4. Open a Pull Request for each completed task and request a review.
5. Update the corresponding project-board task when work starts, enters review, or is completed.
6. For shared tasks, record the final decision and approval so every developer uses the same contract.
7. The task owner coordinates delivery; shared tasks remain a responsibility of the whole team.

## Suggested branch names

- `feature/git-repository`
- `feature/agent-contracts`
- `feature/api-mcd`
- `feature/uml-class-diagram`
- `feature/agent-samples`
- `feature/database-docker`
- `feature/seed-script`
- `feature/authentication`
- `feature/job-offer-crud`
- `feature/application-model`
- `feature/orchestrator`
- `feature/public-pages`
- `feature/candidate-portal`
- `feature/agent-1` through `feature/agent-5`
- `feature/report-template`
