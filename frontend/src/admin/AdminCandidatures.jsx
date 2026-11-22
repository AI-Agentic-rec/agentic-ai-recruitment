import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { useToast } from "../toast.jsx";
import { X, Printer, CheckCircle, XCircle, FileText, Play } from "lucide-react";

const LIBELLE_STATUT = {
  en_attente_de_traitement: "En attente",
  en_cours_de_traitement: "En cours",
  analyse_terminee: "Terminée",
  erreur_de_traitement: "Erreur",
};

export default function AdminCandidatures() {
  const [data, setData] = useState(null);
  const [erreur, setErreur] = useState("");
  const [occupe, setOccupe] = useState({});
  const toast = useToast();

  // ✅ NOUVEAU : État pour la sélection multiple
  const [selection, setSelection] = useState([]);
  const [loadingLot, setLoadingLot] = useState(false);

  const [resultat, setResultat] = useState(null);
  const [loadingResultat, setLoadingResultat] = useState(false);
  const [docsModal, setDocsModal] = useState(null);

  const charger = useCallback(() => {
    api.get("/candidatures")
      .then((d) => {
        setData(d);
        // On nettoie la sélection des éléments qui ne sont plus "en attente"
        setSelection(prev => prev.filter(id => d.candidatures.find(c => c.id === id && c.statut === "en_attente_de_traitement")));
      })
      .catch((e) => setErreur(e.message));
  }, []);

  useEffect(() => { charger(); }, [charger]);

  // ✅ Gérer la sélection
  const toggleSelection = (id) => {
    setSelection(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };
  const toggleAll = () => {
    const enAttente = data.candidatures.filter(c => c.statut === "en_attente_de_traitement").map(c => c.id);
    if (selection.length === enAttente.length) setSelection([]);
    else setSelection(enAttente);
  };

  const lancerTraitement = async (id) => {
    setOccupe((o) => ({ ...o, [id]: true }));
    try {
      await api.post(`/candidatures/${id}/lancer-traitement`);
      toast("Traitement lancé !");
      charger();
    } catch (e) { toast(e.message, "err"); } 
    finally { setOccupe((o) => ({ ...o, [id]: false })); }
  };

  // ✅ Lancer le traitement par lot
  const lancerTraitementLot = async () => {
    if (selection.length === 0) return;
    setLoadingLot(true);
    try {
      await api.post(`/candidatures/lancer-traitement-lot`, { candidature_ids: selection });
      toast(`${selection.length} traitement(s) lancé(s) !`);
      setSelection([]);
      charger();
    } catch (e) { toast(e.message, "err"); } 
    finally { setLoadingLot(false); }
  };

  const voirResultat = async (id) => {
    setLoadingResultat(true);
    try {
      const res = await api.get(`/candidatures/${id}/resultat`);
      setResultat(res);
    } catch (e) { toast(e.message, "err"); } 
    finally { setLoadingResultat(false); }
  };

  const envoyerDecision = async (id, decision) => {
    if (!window.confirm(`Confirmer la décision : ${decision} ? (Un email sera envoyé)`)) return;
    try {
      await api.post(`/candidatures/${id}/decision`, { decision });
      toast(`Email de décision envoyé !`);
      charger();
    } catch (e) { toast(e.message, "err"); }
  };

  const enAttente = data?.candidatures.filter(c => c.statut === "en_attente_de_traitement") || [];

  return (
    <>
      <style>{`
        @media print {
          body * { visibility: hidden; }
          .modal-print, .modal-print * { visibility: visible; }
          .no-print { display: none !important; }
          .modal-print { position: absolute !important; left: 0 !important; top: 0 !important; width: 100% !important; max-width: 100% !important; box-shadow: none !important; border: none !important; background: white !important; padding: 0 !important; margin: 0 !important; }
          .print-overlay { position: static !important; background: transparent !important; display: block !important; }
          @page { margin: 1.5cm; }
        }
      `}</style>

      <div className="tete-page no-print">
        <div>
          <h1>Les candidatures</h1>
          <p>Consultez les dossiers reçus et lancez l'analyse par les agents IA.</p>
        </div>
      </div>

      {/* ✅ BARRE D'ACTION POUR LE TRAITEMENT PAR LOT */}
      {enAttente.length > 0 && (
        <div className="carte no-print" style={{ padding: "15px", marginBottom: "20px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--fond)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input type="checkbox" checked={selection.length === enAttente.length && enAttente.length > 0} onChange={toggleAll} style={{ width: 18, height: 18, cursor: "pointer" }} />
            <span style={{ fontWeight: "bold" }}>Tout sélectionner ({enAttente.length} en attente)</span>
          </div>
          <button className="btn btn-plein" onClick={lancerTraitementLot} disabled={selection.length === 0 || loadingLot}>
            <Play size={18} style={{ marginRight: 8 }} /> 
            {loadingLot ? "Lancement..." : `Lancer la sélection (${selection.length})`}
          </button>
        </div>
      )}

      {erreur && <div className="alerte no-print">{erreur}</div>}

      <div className="lignes no-print">
        {data?.candidatures.map((c) => (
          <div key={c.id} className="ligne carte" style={{ display: "flex", alignItems: "center", gap: 15 }}>
            
            {/* ✅ CASE À COCHER */}
            <div>
              {c.statut === "en_attente_de_traitement" ? (
                <input type="checkbox" checked={selection.includes(c.id)} onChange={() => toggleSelection(c.id)} style={{ width: 18, height: 18, cursor: "pointer" }} />
              ) : (
                <div style={{ width: 18, height: 18 }}></div> // Espace vide pour garder l'alignement
              )}
            </div>

            <div style={{ flex: 1 }}>
              <span className={"statut " + c.statut}>{LIBELLE_STATUT[c.statut] || c.statut}</span>
              <h3>{c.candidat_prenom} {c.candidat_nom} <small style={{fontWeight: 400, color: "var(--doux)"}}>pour</small> {c.offre_titre}</h3>
              <small>Reçue le {c.date_candidature ? new Date(c.date_candidature).toLocaleDateString("fr-FR") : "?"} · {c.documents.length} doc(s)</small>
            </div>
            
            <div className="actions">
              <button className="btn btn-carte btn-petit" onClick={() => setDocsModal(c.documents)}>
                <FileText size={16} style={{ marginRight: 5 }} /> Documents
              </button>

              {c.statut === "en_attente_de_traitement" && (
                <button className="btn btn-carte btn-petit" disabled={occupe[c.id]} onClick={() => lancerTraitement(c.id)}>
                  {occupe[c.id] ? "..." : "Lancer seul"}
                </button>
              )}
              {c.statut === "en_cours_de_traitement" && (
                <span style={{ color: "var(--abricot)", fontWeight: "bold" }}>Agents en cours…</span>
              )}
              {c.statut === "analyse_terminee" && (
                <button className="btn btn-plein btn-petit" onClick={() => voirResultat(c.id)}>Voir les résultats</button>
              )}
              {c.statut === "erreur_de_traitement" && (
                <button className="btn btn-danger btn-petit" onClick={() => lancerTraitement(c.id)}>Relancer</button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ... Les modales Documents et Résultats (inchangées) ... */}
      {docsModal && (
        <div className="no-print" style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center", zIndex: 1000 }}>
          <div className="carte" style={{ width: "90%", maxWidth: "450px", padding: "28px", position: "relative" }}>
            <button onClick={() => setDocsModal(null)} style={{ position: "absolute", top: 15, right: 15, background: "none", border: "none", cursor: "pointer" }}><X size={24} /></button>
            <h2 style={{ marginBottom: 20 }}>Documents du candidat</h2>
            <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 10 }}>
              {docsModal.map(d => (
                <li key={d.id}>
                  <a href={`http://localhost:8000/api/candidatures/documents/${d.id}`} target="_blank" rel="noreferrer" className="btn btn-carte" style={{ width: "100%", justifyContent: "flex-start" }}>
                    <FileText size={18} style={{ marginRight: 8 }} /> Ouvrir le {d.type.toUpperCase()}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {resultat && (
        <div className="print-overlay" style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "grid", placeItems: "center", zIndex: 1000 }}>
          <div className="carte modal-print" style={{ width: "90%", maxWidth: "800px", maxHeight: "90vh", overflowY: "auto", padding: "40px", position: "relative" }}>
            <button onClick={() => setResultat(null)} style={{ position: "absolute", top: 20, right: 20, background: "none", border: "none", cursor: "pointer" }} className="no-print"><X size={24} /></button>
            <button onClick={() => window.print()} className="btn btn-carte no-print" style={{ position: "absolute", top: 20, left: 20, display: "flex", alignItems: "center", gap: "5px" }}><Printer size={18} /> Imprimer PDF</button>
            
            <h2 style={{ marginBottom: 20, marginTop: 30 }}>Résultats de l'analyse</h2>
            {resultat.candidature && (
              <div style={{ marginBottom: 20, padding: 15, background: "var(--fond)", borderRadius: 8 }}>
                <p style={{ margin: 0 }}><strong>Candidat :</strong> {resultat.candidature.candidat_prenom} {resultat.candidature.candidat_nom}</p>
                <p style={{ margin: 0 }}><strong>Poste :</strong> {resultat.candidature.offre_titre}</p>
              </div>
            )}
            
            <div style={{ display: "flex", gap: "20px", marginBottom: "20px", flexWrap: "wrap" }}>
              <div className="carte c1" style={{ flex: 1, padding: "15px", textAlign: "center", minWidth: "150px", border: "1px solid var(--bordure)" }}>
                <span style={{ fontSize: "0.9rem", color: "var(--doux)" }}>Score global</span>
                <div style={{ fontSize: "2.5rem", fontWeight: "bold", color: "var(--texte)" }}>{resultat.score_global.toFixed(1)}<span style={{fontSize: "1rem", fontWeight: "normal"}}>/100</span></div>
              </div>
              <div className="carte c2" style={{ flex: 1, padding: "15px", textAlign: "center", minWidth: "150px", border: "1px solid var(--bordure)" }}>
                <span style={{ fontSize: "0.9rem", color: "var(--doux)" }}>Cohérence docs</span>
                <div style={{ fontSize: "2rem", fontWeight: "bold", color: resultat.verification?.score_coherence >= 50 ? "green" : "red" }}>{resultat.verification?.score_coherence || 0}%</div>
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <h4>Compétences validées</h4>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "8px" }}>
                {resultat.competences_correspondantes.map((c, i) => (
                  <span key={i} style={{ background: "#e6f4ea", color: "#1e8e3e", padding: "4px 10px", borderRadius: "12px", fontSize: "0.85rem", border: "1px solid #b7e1cd", fontWeight: "bold" }}>{c}</span>
                ))}
              </div>
            </div>

            {resultat.competences_manquantes.length > 0 && (
              <div style={{ marginBottom: "20px" }}>
                <h4>Compétences manquantes</h4>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "8px" }}>
                  {resultat.competences_manquantes.map((c, i) => (
                    <span key={i} style={{ background: "var(--alerte)", color: "white", padding: "4px 10px", borderRadius: "12px", fontSize: "0.85rem" }}>{c}</span>
                  ))}
                </div>
              </div>
            )}

            {resultat.rapport && (
              <div style={{ marginBottom: "20px" }}>
                <h4>Rapport de l'Agent 5</h4>
                <p style={{ fontStyle: "italic", background: "var(--fond)", padding: "15px", borderRadius: "8px", marginTop: "8px", borderLeft: "4px solid var(--ciel)" }}>"{resultat.rapport.resume}"</p>
                {resultat.rapport.points_forts && (
                   <ul style={{ paddingLeft: "20px", marginTop: "8px" }}>{resultat.rapport.points_forts.map((p, i) => <li key={i}>{p}</li>)}</ul>
                )}
              </div>
            )}

            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "20px", paddingTop: "20px", borderTop: "1px solid var(--bordure)" }}>
              <strong>Avis indicatif :</strong>
              <span style={{ textTransform: "uppercase", fontWeight: "bold", padding: "4px 10px", borderRadius: "4px", background: resultat.avis_indicatif === "favorable" ? "#e6f4ea" : resultat.avis_indicatif === "defavorable" ? "#fce8e6" : "#fef7e0", color: resultat.avis_indicatif === "favorable" ? "#1e8e3e" : resultat.avis_indicatif === "defavorable" ? "#d93025" : "#b06000" }}>
                {resultat.avis_indicatif || "Non défini"}
              </span>
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 30, paddingTop: 20, borderTop: "1px solid var(--bordure)", justifyContent: "flex-end" }} className="no-print">
               <button onClick={() => envoyerDecision(resultat.candidature.id, "accepte")} className="btn btn-plein" style={{ background: "#1e8e3e", color: "white" }}><CheckCircle size={18} style={{ marginRight: 8 }} /> Accepter</button>
               <button onClick={() => envoyerDecision(resultat.candidature.id, "refuse")} className="btn btn-danger"><XCircle size={18} style={{ marginRight: 8 }} /> Refuser</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}