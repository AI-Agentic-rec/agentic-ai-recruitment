import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { SaisieTags } from "../ui.jsx";

const VIDE = {
  titre: "",
  description: "",
  localisation: "",
  diplome_demande: "",
  experience_annees: 0,
  competences_obligatoires: [],
  competences_souhaitees: [],
  langues: [],
};

export default function OffreForm() {
  const { id } = useParams();
  const { user } = useAuth();
  const [f, setF] = useState(VIDE);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const nav = useNavigate();
  const toast = useToast();

  useEffect(() => {
    if (id) {
      api.get(`/offers/${id}`)
        .then((d) => setF(d.offre))
        .catch((e) => setErreur(e.message));
    }
  }, [id]);

  const maj = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const envoyer = async (action) => {
    setErreur("");
    setEnvoi(true);

    const corps = {
      ...f,
      experience_annees: Number(f.experience_annees) || 0,
      action,
      id_admin: user?.id,
    };

    try {
      if (id) {
        await api.patch(`/offers/${id}`, corps);
        toast("Offre mise à jour.");
      } else {
        await api.post("/offers", corps);
        toast(action === "publier"
          ? "Offre publiée : elle est visible sur le site."
          : "Brouillon enregistré.");
      }
      nav("/admin");
    } catch (e) {
      setErreur(e.message);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <>
      <div className="tete-page">
        <div>
          <h1>{id ? "Modifier l'offre" : "Nouvelle offre"}</h1>
          <p>Ces informations seront aussi lues par l'agent d'analyse des offres.</p>
        </div>
        <Link to="/admin" className="btn btn-carte"><ArrowLeft size={17} />Retour</Link>
      </div>

      {erreur && <div className="alerte" style={{ marginBottom: 18 }} role="alert">{erreur}</div>}

      <form onSubmit={(e) => { e.preventDefault(); envoyer("brouillon"); }}>
        <section className="bloc-form carte">
          <h2>Le poste</h2>
          <label className="champ">Titre du poste
            <input value={f.titre} onChange={maj("titre")} required placeholder="Développeur(se) Python / FastAPI" />
          </label>
          <label className="champ">Description
            <textarea rows={6} value={f.description} onChange={maj("description")} required placeholder="Missions, contexte, équipe…" />
          </label>
          <label className="champ">Localisation
            <input value={f.localisation} onChange={maj("localisation")} placeholder="Casablanca, Télétravail…" />
          </label>
        </section>

        <section className="bloc-form carte">
          <h2>Les exigences</h2>
          <div className="deux">
            <label className="champ">Diplôme demandé
              <input value={f.diplome_demande} onChange={maj("diplome_demande")} placeholder="Licence en informatique" />
            </label>
            <label className="champ">Années d'expérience
              <input type="number" min={0} max={60} value={f.experience_annees} onChange={maj("experience_annees")} />
            </label>
          </div>

          <div className="champ">Compétences indispensables <small>Entrée ou virgule pour ajouter</small>
            <SaisieTags valeur={f.competences_obligatoires} onChange={(v) => setF({ ...f, competences_obligatoires: v })} placeholder="Python, FastAPI, SQL" />
          </div>
          <div className="champ">Compétences appréciées <small>Entrée ou virgule pour ajouter</small>
            <SaisieTags valeur={f.competences_souhaitees} onChange={(v) => setF({ ...f, competences_souhaitees: v })} placeholder="Docker, Git" />
          </div>
          <div className="champ">Langues
            <SaisieTags valeur={f.langues} onChange={(v) => setF({ ...f, langues: v })} placeholder="Français, Anglais" />
          </div>
        </section>

        <div className="actions-form">
          {id ? (
            <button className="btn btn-plein" disabled={envoi}>Enregistrer les modifications</button>
          ) : (
            <>
              <button type="submit" className="btn btn-carte" disabled={envoi}>Enregistrer en brouillon</button>
              <button type="button" className="btn btn-plein" disabled={envoi} onClick={() => envoyer("publier")}>Publier maintenant</button>
            </>
          )}
        </div>
      </form>
    </>
  );
}