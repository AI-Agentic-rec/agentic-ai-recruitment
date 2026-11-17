-- Schéma PostgreSQL généré à partir des modèles (app/models) : tables du diagramme de classes UML v2.
-- Documentation uniquement : la base est créée par Alembic (`alembic upgrade head`), pas par ce fichier.
-- Régénérer : python -m database.schema.generer_sql > database/schema/schema.sql

CREATE TYPE role_utilisateur AS ENUM ('ADMIN', 'CANDIDAT');
CREATE TYPE statut_offre AS ENUM ('BROUILLON', 'PUBLIEE', 'CLOTUREE');
CREATE TYPE statut_candidature AS ENUM ('ENVOYEE', 'EN_ATTENTE_DE_TRAITEMENT', 'EN_COURS_DE_TRAITEMENT', 'ANALYSE_TERMINEE', 'ERREUR_DE_TRAITEMENT');
CREATE TYPE type_document AS ENUM ('CV', 'DIPLOME', 'CIN');
CREATE TYPE avis_indicatif AS ENUM ('FAVORABLE', 'DEFAVORABLE', 'A_ETUDIER');
CREATE TYPE niveau_conformite AS ENUM ('CONFORME', 'PARTIELLEMENT_CONFORME', 'NON_CONFORME');

CREATE TABLE utilisateur (
	id SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenom VARCHAR(100) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	mot_de_passe_hash VARCHAR(255) NOT NULL, 
	role role_utilisateur NOT NULL, 
	telephone VARCHAR(30), 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_utilisateur_email ON utilisateur (email);

CREATE TABLE offre (
	id SERIAL NOT NULL, 
	id_admin INTEGER NOT NULL, 
	titre VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	diplome_demande VARCHAR(255), 
	experience_annees FLOAT, 
	competences_obligatoires JSONB NOT NULL, 
	competences_souhaitees JSONB NOT NULL, 
	langues JSONB NOT NULL, 
	localisation VARCHAR(255), 
	statut statut_offre NOT NULL, 
	date_creation TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	date_publication TIMESTAMP WITH TIME ZONE, 
	date_cloture TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_admin) REFERENCES utilisateur (id) ON DELETE RESTRICT
);
CREATE INDEX ix_offre_id_admin ON offre (id_admin);
CREATE INDEX ix_offre_statut ON offre (statut);

CREATE TABLE candidature (
	id SERIAL NOT NULL, 
	id_candidat INTEGER NOT NULL, 
	id_offre INTEGER NOT NULL, 
	date_candidature TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	statut statut_candidature NOT NULL, 
	message_erreur TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_candidature_candidat_offre UNIQUE (id_candidat, id_offre), 
	FOREIGN KEY(id_candidat) REFERENCES utilisateur (id) ON DELETE CASCADE, 
	FOREIGN KEY(id_offre) REFERENCES offre (id) ON DELETE CASCADE
);
CREATE INDEX ix_candidature_id_candidat ON candidature (id_candidat);
CREATE INDEX ix_candidature_id_offre ON candidature (id_offre);
CREATE INDEX ix_candidature_statut ON candidature (statut);

CREATE TABLE exigences_structurees (
	id_offre INTEGER NOT NULL, 
	titre_poste VARCHAR(255), 
	diplome_demande VARCHAR(255), 
	niveau_diplome_min INTEGER, 
	experience_min_annees FLOAT NOT NULL, 
	competences_obligatoires JSONB NOT NULL, 
	competences_souhaitees JSONB NOT NULL, 
	langues JSONB NOT NULL, 
	missions JSONB NOT NULL, 
	PRIMARY KEY (id_offre), 
	FOREIGN KEY(id_offre) REFERENCES offre (id) ON DELETE CASCADE
);

CREATE TABLE document (
	id SERIAL NOT NULL, 
	id_candidature INTEGER NOT NULL, 
	type type_document NOT NULL, 
	chemin_fichier VARCHAR(1024) NOT NULL, 
	date_import TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_document_candidature_type UNIQUE (id_candidature, type), 
	FOREIGN KEY(id_candidature) REFERENCES candidature (id) ON DELETE CASCADE
);
CREATE INDEX ix_document_id_candidature ON document (id_candidature);

CREATE TABLE profil_candidat (
	id_candidature INTEGER NOT NULL, 
	nom VARCHAR(100), 
	prenom VARCHAR(100), 
	email VARCHAR(255), 
	telephone VARCHAR(50), 
	formations JSONB NOT NULL, 
	experiences JSONB NOT NULL, 
	competences JSONB NOT NULL, 
	langues JSONB NOT NULL, 
	certifications JSONB NOT NULL, 
	experience_totale_annees FLOAT NOT NULL, 
	PRIMARY KEY (id_candidature), 
	FOREIGN KEY(id_candidature) REFERENCES candidature (id) ON DELETE CASCADE
);

CREATE TABLE resultat_analyse (
	id_candidature INTEGER NOT NULL, 
	score_global FLOAT NOT NULL, 
	details JSONB NOT NULL, 
	competences_correspondantes JSONB NOT NULL, 
	competences_manquantes JSONB NOT NULL, 
	diplome_conforme BOOLEAN NOT NULL, 
	experience_candidat_annees FLOAT NOT NULL, 
	rapport JSONB, 
	avis_indicatif avis_indicatif, 
	date_analyse TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id_candidature), 
	FOREIGN KEY(id_candidature) REFERENCES candidature (id) ON DELETE CASCADE
);

CREATE TABLE verification_documents (
	id_candidature INTEGER NOT NULL, 
	infos_diplome JSONB, 
	infos_cin JSONB, 
	documents_analyses JSONB NOT NULL, 
	documents_manquants JSONB NOT NULL, 
	documents_illisibles JSONB NOT NULL, 
	incoherences JSONB NOT NULL, 
	niveau_conformite niveau_conformite NOT NULL, 
	score_coherence INTEGER NOT NULL, 
	resume TEXT NOT NULL, 
	PRIMARY KEY (id_candidature), 
	FOREIGN KEY(id_candidature) REFERENCES candidature (id) ON DELETE CASCADE
);

