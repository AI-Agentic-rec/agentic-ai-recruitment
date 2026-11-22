import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Edit2, FileText, X } from "lucide-react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar, Reveal } from "../ui.jsx";

const LIBELLE_STATUT = {
  en_attente_de_traitement: "En attente",
  en_cours_de_traitement: "En cours d'analyse",
  analyse_terminee: "Analyse terminée",
  erreur_de_traitement: "Erreur",
};

export default function MonEspace() {
  const { user, setUser } = useAuth();
  const toast = useToast();

  const [candidatures, setCandidatures] = useState([]);
  const [chargement, setChargement] = useState(true);

  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState({ nom: user?.nom || "", prenom: user?.prenom || "", telephone: user?.telephone || "" });
  
  const [resultat, setResultat] = useState(null);
  const [loadingResultat, setLoadingResultat] = useState(false);
  
  // ✅ État pour la modale des documents
  const [docsModal, setDocsModal] = useState(null);

  useEffect(() => {
    api.get("/candidatures")
      .then((d) => setCandidatures(d.candidatures))
      .catch((e) => toast(e.message, "err"))
      .finally(() => setChargement(false));
  }, [toast]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const updatedUser = await api.patch("/auth/me", form);
      setUser(updatedUser);
      setEditMode(false);
      toast("Profil mis à jour !");
    } catch (err) { toast(err.message, "err"); }
  };

  const voirResultat = async (id) => {
    setLoadingResultat(true);
    try {
      const res = await api.get(`/candidatures/${id}/resultat-candidat`);
      setResultat(res);
    } catch (e) { toast(e.message, "err"); } 
    finally { setLoadingResultat(false); }
  };

  if (chargement) return <div className="conteneur" style={{ paddingTop: 120, display: "grid", placeItems: "center" }}><div className="rond" /></div>;

  return (
    <div className="conteneur" style={{ display: "grid", gap: 24, paddingBottom: 80 }}>
      <Reveal className="carte" style={{ display: "flex", alignItems: "flex-start", gap: 20, padding: 28 }}>
        <Avatar i={user.id} size={72} />
        <div style={{ flex: 1 }}>
          {!editMode ? (
            <>
              <h1 style={{ fontSize: "2.2rem", margin: 0 }}>Bonjour {user.prenom} !</h1>
              <p style={{ color: "var(--doux)", marginTop: 4 }}>{user.prenom} {user.nom} · {user.email} {user.telephone && `· ${user.telephone}`}</p>
            </>
          ) : (
            <form onSubmit={handleSaveProfile} style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 10 }}>
              <input className="champ" value={form.prenom} onChange={e => setForm({ ...form, prenom: e.target.value })} placeholder="Prénom" required />
              <input className="champ" value={form.nom} onChange={e => setForm({ ...form, nom: e.target.value })} placeholder="Nom" required />
              <input className="champ" value={form.telephone} onChange={e => setForm({ ...form, telephone: e.target.value })} placeholder="Téléphone" />
              <button type="submit" className="btn btn-plein btn-petit">Enregistrer</button>
              <button type="button" className="btn btn-carte btn-petit" onClick={() => setEditMode(false)}>Annuler</button>
            </form>
          )}
        </div>
        {!editMode && <button className="btn btn-carte btn-petit" onClick={() => setEditMode(true)}><Edit2 size={16} /> Modifier</button>}
      </Reveal>

      <Reveal className="carte" delai={0.1} style={{ padding: 28 }}>
        <h2 style={{ marginBottom: 20 }}>Mes candidatures</h2>
        {candidatures.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--doux)" }}>
            <FileText size={40} style={{ opacity: 0.5, marginBottom: 10 }} />
            <p>Vous n'avez pas encore postulé.</p>
            <Link className="btn btn-plein" to="/" style={{ marginTop: 10 }}>Voir les offres</Link>
          </div>
        ) : (
          <div style={{ display: "grid", gap: 16 }}>
            {candidatures.map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10, padding: 16, border: "1px solid var(--bordure)", borderRadius: 12 }}>
                <div>
                  <span className={"statut " + c.statut} style={{ fontSize: "0.8rem", padding: "4px 8px", marginBottom: 8, display: "inline-block" }}>{LIBELLE_STATUT[c.statut] || c.statut}</span>
                  <h3 style={{ margin: 0 }}>{c.offre_titre}</h3>
                  <small style={{ color: "var(--doux)" }}>Postulé le {new Date(c.date_candidature).toLocaleDateString("fr-FR")}</small>
                </div>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  {/* ✅ BOUTON DOCUMENTS */}
                  <button className="btn btn-carte btn-petit" onClick={() => setDocsModal(c.documents)}>Mes documents</button>
                  
                  {c.statut === "analyse_terminee" && (
                    <button className="btn btn-plein btn-petit" onClick={() => voirResultat(c.id)} disabled={loadingResultat}>{loadingResultat ? "Chargement..." : "Voir résultats"}</button>
                  )}
                  {c.statut === "en_attente_de_traitement" && <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--doux)", fontSize: "0.9rem" }}><Clock size={16} /> En attente</span>}
                  {c.statut === "en_cours_de_traitement" && <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--abricot)", fontSize: "0.9rem", fontWeight: "bold" }}><div className="rond" style={{ width: 16, height: 16, borderWidth: 2 }} /> En cours</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Reveal>

      {/* ✅ MODALE DOCUMENTS */}
      {docsModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center", zIndex: 1000 }}>
          <div className="carte" style={{ width: "90%", maxWidth: "400px", padding: "28px", position: "relative" }}>
            <button onClick={() => setDocsModal(null)} style={{ position: "absolute", top: 15, right: 15, background: "none", border: "none", cursor: "pointer" }}><X size={24} /></button>
            <h2 style={{ marginBottom: 20 }}>Mes documents</h2>
            <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 10 }}>
              {docsModal.map(d => (
                <li key={d.id}>
                  <a href={`http://localhost:8000/api/candidatures/documents/${d.id}`} target="_blank" rel="noreferrer" className="btn btn-carte" style={{ width: "100%", justifyContent: "flex-start" }}>
                    <FileText size={18} /> Télécharger le {d.type}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* MODALE RÉSULTAT CANDIDAT */}
      {resultat && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center", zIndex: 1000 }}>
          <div className="carte" style={{ width: "90%", maxWidth: "600px", padding: "28px", position: "relative" }}>
            <button onClick={() => setResultat(null)} style={{ position: "absolute", top: 15, right: 15, background: "none", border: "none", cursor: "pointer" }}><X size={24} /></button>
            <h2 style={{ marginBottom: 20 }}>Résultats de votre analyse</h2>
            <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
              <div className="carte c1" style={{ flex: 1, padding: "15px", textAlign: "center" }}>
                <span style={{ fontSize: "0.9rem", color: "var(--doux)" }}>Score de correspondance</span>
                <div style={{ fontSize: "2.5rem", fontWeight: "bold", color: "var(--texte)" }}>{resultat.score_global.toFixed(1)}<span style={{fontSize: "1rem", fontWeight: "normal"}}>/100</span></div>
              </div>
              <div className="carte c2" style={{ flex: 1, padding: "15px", textAlign: "center" }}>
                <span style={{ fontSize: "0.9rem", color: "var(--doux)" }}>Conformité du dossier</span>
                <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "var(--texte)", marginTop: 8 }}>{resultat.niveau_conformite === "CONFORME" ? "Dossier conforme" : "À vérifier"}</div>
              </div>
            </div>
            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ marginBottom: 8 }}>Compétences validées</h4>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {resultat.competences_correspondantes.length > 0 ? resultat.competences_correspondantes.map((c, i) => (
                  <span key={i} style={{ background: "#e6f4ea", color: "#1e8e3e", padding: "4px 10px", borderRadius: "12px", fontSize: "0.85rem", fontWeight: "bold", border: "1px solid #b7e1cd" }}>{c}</span>
                )) : <span style={{ color: "var(--doux)" }}>Aucune compétence identifiée</span>}
              </div>
            </div>
            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ marginBottom: 8 }}>Compétences manquantes</h4>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {resultat.competences_manquantes.length > 0 ? resultat.competences_manquantes.map((c, i) => (
                  <span key={i} style={{ background: "var(--alerte)", color: "white", padding: "4px 10px", borderRadius: "12px", fontSize: "0.85rem" }}>{c}</span>
                )) : <span style={{ color: "var(--doux)" }}>Aucune compétence manquante</span>}
              </div>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--doux)", fontStyle: "italic", marginTop: 20, textAlign: "center", borderTop: "1px solid var(--bordure)", paddingTop: 15 }}>Le rapport détaillé et les éventuelles incohérences sont réservés au recruteur.</p>
          </div>
        </div>
      )}
    </div>
  );
}