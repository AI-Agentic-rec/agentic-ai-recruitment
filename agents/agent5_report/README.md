# Agent 5 : Report

**Responsable : Fatima (prompt, rapport) et Amina (assemblage des entrées, validation)**

| | |
|---|---|
| **Entrée** | Sorties des agents 1 à 4 (sans le numéro de CIN) |
| **Sortie** | `RapportCandidature` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Résumé, points forts, points manquants, incohérences, justification du score, conclusion, avis indicatif. |
| **Modèle** | `mistral:7b` par défaut, voir `agents/common/llm_local.py` et `.env.example` |

## Règles propres à cet agent
- Le **code** assemble la partie factuelle (points, incohérences, justification du score) ; le modèle rédige le résumé et la conclusion.
- Le rapport reprend exactement le score et le détail de l'agent 4.
- Le rapport rappelle que la décision finale appartient au recruteur.

## Fichiers de ce dossier
| Fichier | Rôle |
|---|---|
| `prompts_agent5.py` | Le prompt système (et seulement lui), avec un exemple fictif |
| `agent5_prototype.py` | Semaine 1 : assemblage des faits, message expurgé, appel du modèle, contrôle de sa réponse, démonstration sur les mocks |
| `agent5.py` | Semaine 2 : agent complet (validation des entrées, repli, point d'entrée `executer_agent5`) |
| `llm_adapter_agent5.py` | **Seul** point de contact avec le moteur Ollama commun (voir « Raccordement au moteur LLM ») |
| `erreurs_agent5.py` | Exceptions de l'agent (messages sans donnée personnelle) |
| `test_agent5_prototype.py`, `test_agent5.py` | Tests sans Ollama (faux modèle) + test d'intégration avec le vrai modèle, ignoré s'il est absent |

## Architecture et flux de données

```
 Agent 1 ExigencesStructurees ─┐
 Agent 2 ProfilCandidat ───────┤
 Agent 3 VerificationDocuments ┼─► valider_entree ─► retirer_donnees_sensibles (CIN) ─► ASSEMBLAGE PAR LE CODE
 Agent 4 ResultatMatching ─────┘                                                        points forts / manquants /
                                                                                         incohérences / justification /
                                                                                         avis indicatif
                                                                                              │ message JSON (liste blanche)
                                                                                              ▼
                                                              LLM local : « resume » et « conclusion » uniquement
                                                                                              │
                                                       contrôle (score, nombres, termes, CIN, décision) ─ échec ─► repli par gabarit
                                                                                              │
                                                                                              ▼
                                                              RapportCandidature (validé par Pydantic)
```

**Ce que fait le code** (jamais le modèle) : points forts, points manquants, incohérences (copie de l'agent 3), justification
du score (copie de l'agent 4), `score_global` (copie), `avis_indicatif`, `decision_finale`.

**Ce que fait le modèle** : `resume` et `conclusion`, à partir des faits ci-dessus.

### Avis indicatif (déterministe)
- `defavorable` : score < 50
- `favorable` : score ≥ 75, **sans** incohérence de gravité élevée et **sans** critère « compétences obligatoires » à 0
- `a_etudier` : tous les autres cas

### Contrôles appliqués au texte du modèle (sinon 1 nouvelle tentative, puis repli)
longueur raisonnable · aucun motif de CIN · aucune décision de recrutement (« embaucher », « candidat retenu »...) ·
tout score cité sous la forme `x/100` égal au score de l'agent 4 · aucun nombre absent des faits fournis ·
aucun terme capitalisé en milieu de phrase (compétence, outil, employeur, lieu) absent des faits fournis.
La conclusion contient toujours le rappel de la décision du recruteur (ajouté par le code s'il manque).

### Confidentialité
- Le message envoyé au modèle est construit par **liste blanche** : prénom/nom, intitulé du poste, score, avis, faits assemblés,
  poids et scores des critères. **Jamais** `infos_cin`, date de naissance, email ni téléphone.
- Le numéro de CIN est masqué (`[CIN masqué]`) partout où il pourrait figurer dans un texte, puis un dernier contrôle
  (`verifier_absence_cin`) bloque l'envoi (`FuiteDonneesSensiblesError`) si un CIN subsiste. Cette erreur n'est jamais
  masquée par le repli.
- Les logs ne contiennent que `candidate_id` / `job_id`, le score, l'avis et le mode de rédaction.
- Le nom du candidat est transmis au modèle (nécessaire au résumé) : si l'équipe préfère l'anonymiser, il suffit de
  remplacer `nom` dans `preparer_rapport`.

## Raccordement au moteur LLM
L'Agent 5 n'a **aucune** configuration LLM propre. `llm_adapter_agent5.py` est son seul point de contact avec
`agents/common/llm_local.py` : il appelle `executer_agent(5, prompt, message_json, SchemaPydantic, llm=llm)` (JSON forcé,
validation Pydantic, 3 essais avec relance) et convertit toute panne (`AgentError`, serveur Ollama arrêté, modèle absent)
en `ErreurLLM`, dont le message ne contient ni prompt ni réponse du modèle.
- **Modèle :** celui de `llm_local.modele_pour(5)` : `OLLAMA_MODEL_AGENT5`, puis `OLLAMA_MODEL`, puis `mistral:7b` (défaut de l'agent 5).
  Rien à régler pour utiliser Mistral 7B.
- **Faux modèle des tests :** `llm(modele, system, messages, schema) -> str (JSON)`, comme dans `llm_local`.
- Pour changer de moteur ou de modèle, ne modifier que `llm_local.py` / les variables d'environnement, pas l'Agent 5.

## Exécuter et tester
Depuis la racine du dépôt :
```bash
python -m pytest agents/agent5_report -v                         # tests unitaires (faux modèle, sans Ollama)
python -m pytest agents -q                                       # avec les tests des autres agents et des mocks
python -m agents.agent5_report.agent5_prototype --sans-modele    # faits seuls sur les mocks
python -m agents.agent5_report.agent5 --sans-modele --cas incoherent   # rapport complet, rédaction par gabarit

# avec le vrai modèle local
pip install -r agents/requirements.txt
ollama serve & ollama pull mistral:7b                           # modèle de l'agent 5 (ou OLLAMA_MODEL=... pour un autre)
python -m agents.agent5_report.agent5_prototype                  # prototype sur les deux chaînes de mocks
python -m agents.agent5_report.agent5 --cas conforme             # agent complet
python -m pytest agents/agent5_report/test_agent5_prototype.py -v    # le test d'intégration ne s'ignore plus
```

## Intégration dans l'orchestrateur (à faire par Fatima, l'orchestrateur n'est pas modifié ici)
```python
from agents.agent5_report.agent5 import executer_agent5
from agents.agent5_report.erreurs_agent5 import Agent5Error

# après les agents 1 à 4 (objets Pydantic ou dictionnaires) :
try:
    rapport = executer_agent5({"agent1": a1, "agent2": a2, "agent3": a3, "agent4": a4}, contexte=contexte)  # RapportCandidature
    enregistrer_en_base(rapport.model_dump())
except Agent5Error as exc:                       # message sans donnée personnelle -> statut « Erreur de traitement »
    marquer_erreur(candidature, str(exc))
```
- L'Agent 3 doit déjà être passé par `sans_donnees_sensibles(...)` ; l'agent 5 retire malgré tout `infos_cin` (double sécurité).
- `agent3` peut être `None` (l'agent 4 le tolère) ; `agent1`, `agent2`, `agent4` sont obligatoires.
- En cas de panne du modèle, l'agent 5 produit quand même un rapport (repli par gabarit). Pour le savoir, utiliser
  `generer_rapport_avec_trace(...)` qui renvoie aussi `TraceAgent5(redaction="llm" | "repli", cause_repli=...)`.
  `repli=False` lève l'erreur au lieu de replier.

## Hypothèses et limites connues
- « Critère obligatoire à 0 » est interprété comme le critère `competences_obligatoires` (score 0).
- Les points forts/manquants sont écrits en français par le code, avec des seuils fixes (`SEUIL_POINT_FORT = 70`).
- Le garde-fou « terme absent des faits » est heuristique (majuscule en milieu de phrase) : il peut rejeter à tort un
  texte correct (le repli prend alors le relais), mais ne détecte pas une invention écrite en minuscules.
- Le PDF `docs/contrats/contrats_agents.pdf` parle de `manques` et `mention_decision_humaine` : le schéma réel
  (`points_manquants`, `decision_finale`) fait foi.

## État
- [ ] Prompt et prototype validés avec le vrai modèle (tests faits avec faux modèle ; Ollama absent de l'environnement de développement)
- [x] Agent complet
- [x] Tests (sans Ollama)
- [ ] Intégré à l'orchestrateur
