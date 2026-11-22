# =====================================================================
# Script de création de 20 offres d'emploi de test
# Usage : .\creer_offres.ps1   (API attendue sur http://localhost:8000)
# =====================================================================

function Creer-Offre($body) {
    $json = $body | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/offers `
      -ContentType "application/json; charset=utf-8" `
      -Body ([System.Text.Encoding]::UTF8.GetBytes($json))
}

$ok = 0; $ko = 0

function Essayer($n, $body) {
    try { Creer-Offre $body | Out-Null; Write-Host "[$n] OK : $($body.titre)" -ForegroundColor Green; $script:ok++ }
    catch { Write-Host "[$n] ERREUR : $($body.titre) -> $($_.Exception.Message)" -ForegroundColor Red; $script:ko++ }
}

# --- Offre 1 : Data Scientist Senior ---
$body1 = @{
  titre="Data Scientist Senior"
  description="Nous recherchons un Data Scientist expérimenté pour rejoindre notre pôle IA. Vous concevrez, entraînerez et déploierez des modèles de Machine Learning en production pour des cas d'usage de scoring, de recommandation et de prévision de la demande. Missions : exploration de données massives, feature engineering, sélection et évaluation de modèles, mise en place de pipelines MLOps, restitution des résultats aux équipes métiers."
  localisation="Casablanca, Maroc (Hybride)"
  diplome_demande="Master ou Doctorat en Data Science, Statistiques ou Informatique"
  experience_annees=4
  competences_obligatoires=@("Python", "Machine Learning", "Pandas", "Scikit-learn", "SQL")
  competences_souhaitees=@("PyTorch", "TensorFlow", "MLflow", "Docker")
  langues=@("Français (C1)", "Anglais (C1)")
  id_admin=1
  action="publier"
}
Essayer 1 $body1

# --- Offre 2 : Développeur Frontend React ---
$body2 = @{
  titre="Développeur Frontend React"
  description="Au sein de notre équipe produit, vous participerez à la refonte de notre plateforme web utilisée par des milliers d'utilisateurs. Vous transformerez les maquettes Figma en interfaces réactives, accessibles et performantes. Missions : développement de composants React, intégration d'API REST, optimisation des performances, écriture de tests unitaires."
  localisation="Rabat, Maroc"
  diplome_demande="Licence ou Master en développement web"
  experience_annees=2
  competences_obligatoires=@("React", "JavaScript", "HTML", "CSS")
  competences_souhaitees=@("TypeScript", "Redux", "Tailwind CSS", "Jest")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 2 $body2

# --- Offre 3 : Chef de Projet IT / Product Owner ---
$body3 = @{
  titre="Chef de Projet IT / Product Owner"
  description="Nous cherchons un Chef de Projet IT pour piloter le développement de nos solutions logicielles. Vous serez l'interface entre les besoins métiers et l'équipe technique. Missions : rédaction de cahiers des charges, animation des cérémonies Agile (Scrum), suivi des sprints, gestion de la relation client et du budget projet."
  localisation="Télétravail complet"
  diplome_demande="Bac+5 en Management de Projets IT ou École d'Ingénieur"
  experience_annees=5
  competences_obligatoires=@("Gestion de projet", "Agile", "Scrum", "Jira")
  competences_souhaitees=@("UML", "Notions en développement web", "Figma")
  langues=@("Français (C2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 3 $body3

# --- Offre 4 : Ingénieur DevOps ---
$body4 = @{
  titre="Ingénieur DevOps"
  description="Rattaché à la direction technique, vous industrialisez le cycle de livraison de nos applications et garantissez la fiabilité de l'infrastructure cloud. Missions : conception de pipelines CI/CD, automatisation de l'infrastructure avec Terraform, orchestration de conteneurs Kubernetes, supervision et gestion des incidents, amélioration de la sécurité des déploiements."
  localisation="Casablanca, Maroc (Hybride)"
  diplome_demande="Diplôme d'ingénieur ou Master en Informatique, Réseaux ou Systèmes"
  experience_annees=3
  competences_obligatoires=@("Linux", "Docker", "Kubernetes", "CI/CD", "Git")
  competences_souhaitees=@("Terraform", "Ansible", "Prometheus", "Grafana", "AWS")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 4 $body4

# --- Offre 5 : Développeur Backend Python / Django ---
$body5 = @{
  titre="Développeur Backend Python / Django"
  description="Nous développons une plateforme SaaS de gestion de ressources humaines et recherchons un développeur backend pour renforcer l'équipe. Missions : conception d'API REST, modélisation de bases de données, écriture de tests automatisés, optimisation des requêtes, participation aux revues de code et à l'amélioration continue de l'architecture."
  localisation="Rabat, Maroc (Hybride)"
  diplome_demande="Licence ou Master en Informatique ou Génie logiciel"
  experience_annees=3
  competences_obligatoires=@("Python", "Django", "PostgreSQL", "API REST", "Git")
  competences_souhaitees=@("Celery", "Redis", "Docker", "Pytest")
  langues=@("Français (B2)", "Anglais (B1)")
  id_admin=1
  action="publier"
}
Essayer 5 $body5

# --- Offre 6 : Ingénieur Machine Learning / Vision par ordinateur ---
$body6 = @{
  titre="Ingénieur Machine Learning / Vision par ordinateur"
  description="Dans le cadre du développement d'une solution d'inspection qualité par imagerie, vous concevrez des modèles de vision par ordinateur et les optimiserez pour un déploiement en temps réel. Missions : constitution et annotation des jeux de données, entraînement de modèles de détection et de segmentation, évaluation, optimisation pour l'inférence, documentation technique."
  localisation="Agadir, Maroc"
  diplome_demande="Master ou Ingénieur en Intelligence Artificielle, Informatique ou Mathématiques appliquées"
  experience_annees=2
  competences_obligatoires=@("Python", "Deep Learning", "OpenCV", "PyTorch", "NumPy")
  competences_souhaitees=@("TensorFlow", "ONNX", "CUDA", "Docker")
  langues=@("Français (B2)", "Anglais (C1)")
  id_admin=1
  action="publier"
}
Essayer 6 $body6

# --- Offre 7 : Analyste Business Intelligence ---
$body7 = @{
  titre="Analyste Business Intelligence"
  description="Au sein de la direction financière, vous transformez les données de l'entreprise en tableaux de bord décisionnels. Missions : recueil des besoins métiers, modélisation de données, développement de rapports interactifs, automatisation des chargements de données, garantie de la qualité et de la cohérence des indicateurs."
  localisation="Casablanca, Maroc"
  diplome_demande="Bac+5 en Informatique décisionnelle, Statistiques ou Finance"
  experience_annees=3
  competences_obligatoires=@("SQL", "Power BI", "Excel", "Modélisation de données")
  competences_souhaitees=@("Python", "Tableau", "SSIS", "DAX")
  langues=@("Français (C1)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 7 $body7

# --- Offre 8 : Développeur Mobile Flutter ---
$body8 = @{
  titre="Développeur Mobile Flutter"
  description="Nous construisons une application mobile de paiement et de services de proximité. Vous rejoindrez l'équipe mobile pour développer de nouvelles fonctionnalités sur iOS et Android à partir d'une base de code unique. Missions : développement d'écrans et de logique métier, intégration d'API, tests, publication sur les stores, suivi des retours utilisateurs."
  localisation="Marrakech, Maroc (Hybride)"
  diplome_demande="Licence ou Master en Informatique"
  experience_annees=2
  competences_obligatoires=@("Flutter", "Dart", "API REST", "Git")
  competences_souhaitees=@("Firebase", "Bloc", "CI/CD", "Swift", "Kotlin")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 8 $body8

# --- Offre 9 : Ingénieur Cybersécurité ---
$body9 = @{
  titre="Ingénieur Cybersécurité"
  description="Au sein de l'équipe sécurité, vous protégez le système d'information et pilotez la réponse aux incidents. Missions : réalisation de tests d'intrusion et d'audits de vulnérabilités, supervision SOC, analyse des alertes SIEM, définition de politiques de sécurité, sensibilisation des équipes, veille sur les menaces."
  localisation="Rabat, Maroc"
  diplome_demande="Diplôme d'ingénieur ou Master en Cybersécurité ou Réseaux"
  experience_annees=3
  competences_obligatoires=@("Sécurité des systèmes", "Pentest", "Réseaux TCP/IP", "Linux", "SIEM")
  competences_souhaitees=@("ISO 27001", "Python", "Wireshark", "Metasploit")
  langues=@("Français (C1)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 9 $body9

# --- Offre 10 : Administrateur Systèmes et Réseaux ---
$body10 = @{
  titre="Administrateur Systèmes et Réseaux"
  description="Vous assurez le maintien en conditions opérationnelles de l'infrastructure informatique de l'entreprise, répartie sur plusieurs sites. Missions : administration des serveurs Windows et Linux, gestion du réseau (VLAN, pare-feu, VPN), sauvegardes, support de niveau 2 et 3, documentation et amélioration continue de l'infrastructure."
  localisation="Tanger, Maroc"
  diplome_demande="Bac+3 à Bac+5 en Réseaux et Systèmes"
  experience_annees=3
  competences_obligatoires=@("Windows Server", "Linux", "Active Directory", "Réseaux", "Virtualisation")
  competences_souhaitees=@("VMware", "Cisco", "Zabbix", "PowerShell")
  langues=@("Français (B2)", "Anglais (B1)")
  id_admin=1
  action="publier"
}
Essayer 10 $body10

# --- Offre 11 : Développeur Full Stack Node.js / React ---
$body11 = @{
  titre="Développeur Full Stack Node.js / React"
  description="Au sein d'une startup en forte croissance, vous développerez de bout en bout une plateforme de mise en relation entre prestataires et clients. Missions : conception de l'architecture applicative, développement d'API et d'interfaces, intégration de services de paiement, mise en place des tests, participation aux choix techniques."
  localisation="Casablanca, Maroc (Hybride)"
  diplome_demande="Master ou Ingénieur en Informatique"
  experience_annees=3
  competences_obligatoires=@("JavaScript", "Node.js", "React", "MongoDB", "API REST")
  competences_souhaitees=@("TypeScript", "Express", "Docker", "AWS")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 11 $body11

# --- Offre 12 : UX/UI Designer ---
$body12 = @{
  titre="UX/UI Designer"
  description="Vous concevez des parcours utilisateur clairs et soignés pour nos produits web et mobiles. Missions : recherche utilisateur, wireframes, maquettes haute-fidélité, prototypes interactifs, tests d'utilisabilité, maintenance du design system et collaboration étroite avec les développeurs."
  localisation="Télétravail complet"
  diplome_demande="Licence ou Master en Design, Multimédia ou Informatique"
  experience_annees=2
  competences_obligatoires=@("Figma", "Design UX", "Prototypage", "Design System")
  competences_souhaitees=@("Adobe XD", "Accessibilité", "HTML", "CSS")
  langues=@("Français (C1)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 12 $body12

# --- Offre 13 : Ingénieur Data (Data Engineer) ---
$body13 = @{
  titre="Ingénieur Data (Data Engineer)"
  description="Vous construisez et maintenez les pipelines qui alimentent nos équipes data en données fiables. Missions : conception d'ETL/ELT, modélisation d'un entrepôt de données, orchestration des traitements, surveillance de la qualité des données, optimisation des performances et des coûts."
  localisation="Casablanca, Maroc (Hybride)"
  diplome_demande="Master ou Ingénieur en Informatique ou Big Data"
  experience_annees=3
  competences_obligatoires=@("Python", "SQL", "ETL", "Apache Spark", "Bases de données")
  competences_souhaitees=@("Airflow", "Kafka", "dbt", "AWS", "Docker")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 13 $body13

# --- Offre 14 : Testeur QA / Ingénieur Test Automatisation ---
$body14 = @{
  titre="Testeur QA / Ingénieur Test Automatisation"
  description="Vous garantissez la qualité de nos livraisons logicielles. Missions : rédaction de plans et de cas de test, automatisation des tests fonctionnels et d'API, intégration des tests dans la chaîne CI, suivi des anomalies, reporting qualité auprès de l'équipe projet."
  localisation="Rabat, Maroc"
  diplome_demande="Licence ou Master en Informatique"
  experience_annees=2
  competences_obligatoires=@("Tests fonctionnels", "Selenium", "Jira", "SQL")
  competences_souhaitees=@("Cypress", "Postman", "Python", "CI/CD")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 14 $body14

# --- Offre 15 : Responsable Marketing Digital ---
$body15 = @{
  titre="Responsable Marketing Digital"
  description="Vous définissez et pilotez la stratégie d'acquisition et de visibilité de la marque. Missions : gestion des campagnes SEA et social ads, stratégie SEO, animation des réseaux sociaux, emailing, suivi des performances (KPI), gestion d'un budget média et encadrement d'un community manager."
  localisation="Casablanca, Maroc"
  diplome_demande="Bac+4/5 en Marketing, Communication ou École de Commerce"
  experience_annees=4
  competences_obligatoires=@("SEO", "Google Ads", "Réseaux sociaux", "Google Analytics")
  competences_souhaitees=@("Meta Ads", "Emailing", "Canva", "HubSpot")
  langues=@("Français (C2)", "Anglais (B2)", "Arabe (C2)")
  id_admin=1
  action="publier"
}
Essayer 15 $body15

# --- Offre 16 : Comptable Confirmé ---
$body16 = @{
  titre="Comptable Confirmé"
  description="Au sein du service comptable, vous assurez la tenue de la comptabilité générale et la production des états financiers. Missions : saisie et contrôle des écritures, rapprochements bancaires, déclarations fiscales (TVA, IS), clôtures mensuelles et annuelles, appui lors des audits."
  localisation="Fès, Maroc"
  diplome_demande="Bac+3 à Bac+5 en Comptabilité, Finance ou Gestion"
  experience_annees=3
  competences_obligatoires=@("Comptabilité générale", "Fiscalité marocaine", "Excel", "Clôture comptable")
  competences_souhaitees=@("Sage", "SAP", "Contrôle de gestion")
  langues=@("Français (C1)", "Arabe (C1)")
  id_admin=1
  action="publier"
}
Essayer 16 $body16

# --- Offre 17 : Assistant(e) Juridique ---
$body17 = @{
  titre="Assistant(e) Juridique"
  description="Vous apportez un soutien juridique et administratif à une équipe d'avocats d'affaires. Missions : rédaction et mise en forme d'actes et de contrats, constitution et suivi des dossiers, recherches juridiques, gestion des échéances et des archives, relation avec les clients et les juridictions."
  localisation="Agadir, Maroc"
  diplome_demande="Licence ou Master en Droit"
  experience_annees=1
  competences_obligatoires=@("Rédaction juridique", "Droit des affaires", "Suite Office", "Gestion de dossiers")
  competences_souhaitees=@("Droit des sociétés", "Veille juridique")
  langues=@("Français (C2)", "Arabe (C2)")
  id_admin=1
  action="publier"
}
Essayer 17 $body17

# --- Offre 18 : Enseignant(e)-Chercheur en Intelligence Artificielle ---
$body18 = @{
  titre="Enseignant(e)-Chercheur en Intelligence Artificielle"
  description="Notre établissement recrute un enseignant-chercheur pour renforcer la filière Intelligence Artificielle. Missions : enseignement de cours en Machine Learning et Deep Learning, encadrement de projets de fin d'études, développement de travaux de recherche et de partenariats avec l'industrie, publications scientifiques."
  localisation="Agadir, Maroc"
  diplome_demande="Doctorat en Informatique ou Intelligence Artificielle"
  experience_annees=2
  competences_obligatoires=@("Machine Learning", "Deep Learning", "Python", "Recherche scientifique")
  competences_souhaitees=@("Publications", "Encadrement de projets", "NLP", "Vision par ordinateur")
  langues=@("Français (C1)", "Anglais (C1)")
  id_admin=1
  action="publier"
}
Essayer 18 $body18

# --- Offre 19 : Ingénieur Cloud / Architecte Solutions ---
$body19 = @{
  titre="Ingénieur Cloud / Architecte Solutions"
  description="Vous accompagnez nos clients dans la conception et la migration de leurs applications vers le cloud. Missions : définition d'architectures cloud sécurisées et économiques, ateliers techniques avec les clients, migration d'applications, estimation des coûts, rédaction de documents d'architecture."
  localisation="Casablanca, Maroc (Hybride)"
  diplome_demande="Diplôme d'ingénieur ou Master en Informatique, Réseaux ou Cloud"
  experience_annees=5
  competences_obligatoires=@("AWS", "Architecture cloud", "Réseaux", "Sécurité", "Linux")
  competences_souhaitees=@("Azure", "Terraform", "Kubernetes", "Certification cloud")
  langues=@("Français (C1)", "Anglais (C1)")
  id_admin=1
  action="publier"
}
Essayer 19 $body19

# --- Offre 20 : Développeur Java / Spring Boot ---
$body20 = @{
  titre="Développeur Java / Spring Boot"
  description="Dans une équipe en charge de systèmes bancaires, vous développez des services robustes et sécurisés. Missions : conception de microservices, développement d'API, intégration avec des systèmes existants, optimisation des performances, rédaction de tests unitaires et d'intégration, documentation technique."
  localisation="Casablanca, Maroc"
  diplome_demande="Master ou Ingénieur en Informatique"
  experience_annees=4
  competences_obligatoires=@("Java", "Spring Boot", "SQL", "Microservices", "Git")
  competences_souhaitees=@("Kafka", "Docker", "Maven", "Oracle")
  langues=@("Français (B2)", "Anglais (B2)")
  id_admin=1
  action="publier"
}
Essayer 20 $body20

Write-Host ""
Write-Host "Terminé : $ok offres créées, $ko erreurs sur 20." -ForegroundColor Cyan
