import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Eye, Pencil, Plus, Send, Trash2, Lock } from "lucide-react";
import { api } from "../api.js";
import { useToast } from "../toast.jsx";

const LIBELLE = { brouillon: "Brouillon", publiee: "Publiée", cloturee: "Clôturée" };

export default function AdminOffres() {
  const [data, setData] = useState(null), [erreur, setErreur] = useState("");
  const toast = useToast();
  const charger = useCallback(() => api.get("/offers").then(setData).catch((e) => setErreur(e.message)), []);
  useEffect(() => { charger(); }, [charger]);

  const agir = async (promesse, message) => {
    try { await promesse(); toast(message); charger(); } catch (e) { toast(e.message, "err"); }
  };
  const c = data?.counts || { brouillon: 0, publiee: 0, cloturee: 0 };
  
  return (
    <>
      <div className="tete-page">
        <div><h1>Les offres</h1><p>Rédigez, publiez et clôturez vos annonces.</p></div>
        <Link to="/admin/offers/nouvelle" className="btn btn-plein"><Plus size={18} />Nouvelle offre</Link>
      </div>
      <div className="compteurs">
        <div className="compteur carte c0"><b>{c.brouillon}</b><small>en brouillon</small></div>
        <div className="compteur carte c1"><b>{c.publiee}</b><small>publiée{c.publiee > 1 ? "s" : ""}</small></div>
        <div className="compteur carte c2"><b>{c.cloturee}</b><small>clôturée{c.cloturee > 1 ? "s" : ""}</small></div>
      </div>
      {erreur && <div className="alerte">{erreur}</div>}
      <div className="lignes">
        {data?.offres.map((o) => (
          <div className="ligne carte" key={o.id}>
            <div>
              <span className={"statut " + o.statut}>{LIBELLE[o.statut]}</span>
              <h3>{o.titre}</h3>
              <small>{o.localisation || "Lieu non précisé"} · créée le {new Date(o.date_creation).toLocaleDateString("fr-FR")}</small>
            </div>
            <div className="actions">
              {o.statut === "publiee" && <Link className="btn btn-carte btn-petit" to={`/offers/${o.id}`}><Eye size={16} />Voir</Link>}
              {o.statut !== "cloturee" && <Link className="btn btn-carte btn-petit" to={`/admin/offers/${o.id}/modifier`}><Pencil size={16} />Modifier</Link>}
              
              {o.statut === "brouillon" && (
                <button className="btn btn-plein btn-petit" onClick={() => agir(() => api.post(`/offers/${o.id}/publier`), "Offre publiée.")}><Send size={16} />Publier</button>
              )}
              {o.statut === "publiee" && (
                <button className="btn btn-danger btn-petit" onClick={() => window.confirm("Clôturer cette offre ?") && agir(() => api.post(`/offers/${o.id}/cloturer`), "Offre clôturée.")}><Lock size={16} />Clôturer</button>
              )}
              
              {/* ✅ BOUTON SUPPRIMER TOUJOURS VISIBLE */}
              <button className="btn btn-danger btn-petit" style={{ background: "transparent", border: "1px solid var(--alerte)", color: "var(--alerte)" }} onClick={() => window.confirm(`Supprimer définitivement l'offre "${o.titre}" ?`) && agir(() => api.del(`/offers/${o.id}`), "Offre supprimée.")}><Trash2 size={16} />Supprimer</button>
            </div>
          </div>
        ))}
        {data && data.offres.length === 0 && (
          <div className="vide carte"><h3>Aucune offre</h3><p>Créez votre première offre.</p><Link to="/admin/offers/nouvelle" className="btn btn-plein btn-petit">Créer</Link></div>
        )}
      </div>
    </>
  );
}