import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Upload } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export default function Postuler() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const toast = useToast();
  const [cv, setCv] = useState(null);
  const [diplome, setDiplome] = useState(null);
  const [cin, setCin] = useState(null);
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");

  const envoyer = async (e) => {
    e.preventDefault();
    if (!cv || !diplome || !cin) {
      setErreur("Veuillez fournir les 3 documents (CV, Diplôme, CIN).");
      return;
    }
    setEnvoi(true);
    setErreur("");
    try {
      const formData = new FormData();
      formData.append("id_offre", id);
      formData.append("id_candidat", user.id);
      formData.append("cv", cv);
      formData.append("diplome", diplome);
      formData.append("cin", cin);

      const res = await fetch(`${BASE_URL}/candidatures`, {
        method: "POST",
        headers: { "X-User-Id": String(user.id) },
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Erreur ${res.status}`);
      }

      toast("Candidature envoyée avec succès !");
      nav("/candidat");
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <div className="conteneur" style={{ paddingBottom: 80 }}>
      <Link to={`/offers/${id}`} className="retour">
        <ArrowLeft size={18} />Retour à l'offre
      </Link>
      <h1 style={{ fontSize: "2.4rem", marginBottom: 10 }}>Postuler à cette offre</h1>
      <p style={{ color: "var(--doux)", marginBottom: 30 }}>
        Fournissez votre CV (PDF ou DOCX), votre diplôme et votre CIN (images JPG ou PNG).
      </p>

      {erreur && <div className="alerte" style={{ marginBottom: 18 }}>{erreur}</div>}

      <form onSubmit={envoyer} className="carte" style={{ padding: 28, display: "grid", gap: 20 }}>
        {[
          { label: "CV (PDF ou DOCX uniquement)", setter: setCv, fichier: cv, accept: ".pdf,.docx" },
          { label: "Diplôme (JPG ou PNG uniquement)", setter: setDiplome, fichier: diplome, accept: ".jpg,.jpeg,.png" },
          { label: "CIN (JPG ou PNG uniquement)", setter: setCin, fichier: cin, accept: ".jpg,.jpeg,.png" },
        ].map(({ label, setter, fichier, accept }, i) => (
          <label key={i} className="champ">
            {label}
            <span className="btn btn-carte" style={{ cursor: "pointer", display: "inline-flex", gap: 8 }}>
              <Upload size={16} />
              {fichier ? fichier.name : "Choisir un fichier"}
              <input
                type="file"
                accept={accept}
                style={{ display: "none" }}
                onChange={(e) => setter(e.target.files[0] || null)}
              />
            </span>
          </label>
        ))}

        <button type="submit" className="btn btn-plein btn-large" disabled={envoi}>
          {envoi ? "Envoi en cours…" : "Envoyer ma candidature"}
        </button>
      </form>
    </div>
  );
}