import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next"; // ✅ IMPORT
import { ArrowLeft, Briefcase, GraduationCap, Languages, MapPin, Pencil } from "lucide-react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Puces, Reveal } from "../ui.jsx";

import { Vignette } from "../scene.jsx";


export default function OffreDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t } = useTranslation(); // ✅ HOOK

  const [offre, setOffre] = useState(null), [erreur, setErreur] = useState("");
  useEffect(() => { setOffre(null); setErreur(""); api.get(`/offers/${id}`).then((d) => setOffre(d.offre)).catch((e) => setErreur(e.message)); }, [id]);

  if (erreur) return (
    <div className="conteneur" style={{ padding: "90px 24px", textAlign: "center", display: "grid", gap: 16, justifyItems: "center" }}>
      <h1 style={{ fontSize: "2.8rem" }}>Cette offre est introuvable</h1>
      <p style={{ color: "var(--doux)", maxWidth: 420 }}>{erreur}</p>
      <Link to="/" className="btn btn-plein">Voir les offres ouvertes</Link>
    </div>
  );
  if (!offre) return <div className="conteneur" style={{ paddingTop: 120, display: "grid", placeItems: "center" }}><div className="rond" /></div>;

  const exp = offre.experience_annees === 0 ? "Débutant accepté" : `${offre.experience_annees} an${offre.experience_annees > 1 ? "s" : ""}`;

  return (
    <div className="conteneur">
      <Link to="/" className="retour"><ArrowLeft size={18} />Toutes les offres</Link>
      <div className="bandeau">
        <Vignette id={offre.id} />
        <div className="plaque givre">
          <h1>{offre.titre}</h1>
          <p className="meta">
            {offre.localisation && <span><MapPin size={17} />{offre.localisation}</span>}
            {offre.date_publication && <span>Publiée le {new Date(offre.date_publication).toLocaleDateString("fr-FR")}</span>}
          </p>
        </div>
      </div>
      <article className="detail">
        <div>
          <Reveal><h2>Le poste</h2><div className="prose">{offre.description.split("\n").filter((p) => p.trim()).map((p, i) => <p key={i}>{p}</p>)}</div></Reveal>
          <Reveal delai={0.1}>
            <h2>Ce qu'on recherche</h2>
            <p className="libelle">Indispensable</p><Puces liste={offre.competences_obligatoires} />
            <p className="libelle">Apprécié</p><Puces liste={offre.competences_souhaitees} classe="puce chaud" />
          </Reveal>
        </div>
        <Reveal as="aside" delai={0.15} className="lateral carte">
          <dl className="faits">
            <div className="fait"><span className="icone-rond"><Briefcase size={20} /></span><div><dt>Expérience</dt><dd>{exp}</dd></div></div>
            <div className="fait"><span className="icone-rond"><GraduationCap size={20} /></span><div><dt>Diplôme</dt><dd>{offre.diplome_demande || "Non précisé"}</dd></div></div>
            <div className="fait"><span className="icone-rond"><Languages size={20} /></span><div><dt>Langues</dt><dd>{offre.langues.join(", ") || "Non précisées"}</dd></div></div>
          </dl>

          {/* Bouton Postuler pour visiteur non connecté */}
          {!user && (
            <>
              <Link to="/connexion" className="btn btn-plein btn-large">Postuler</Link>
              <p className="note">Connectez-vous ou créez un compte pour postuler.</p>
            </>
          )}

          {/* Bouton Postuler ACTIF pour candidat */}
          {user?.role === "candidat" && (
            <>
              <Link to={`/offers/${offre.id}/postuler`} className="btn btn-plein btn-large">Postuler</Link>
              <p className="note">Vous serez invité à fournir CV, diplôme et CIN.</p>
            </>
          )}

          {/* Bouton Modifier pour admin */}
          {user?.role === "admin" && (
            <Link to={`/admin/offers/${offre.id}/modifier`} className="btn btn-doux btn-large">
              <Pencil size={17} />Modifier cette offre
            </Link>
          )}

          <div className="apres">
            <h4>Et après ?</h4>
            <ol>
              <li>Vous déposez votre dossier : CV, diplôme et CIN.</li>
              <li>Votre profil est étudié par notre équipe de recrutement.</li>
              <li>Vos compétences sont évaluées au regard des exigences du poste.</li>
              <li>Une décision vous est communiquée rapidement.</li>
            </ol>
          </div>
        </Reveal>
      </article>
    </div>
  );
}