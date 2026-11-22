import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Users, CheckCircle, TrendingUp, Award } from "lucide-react";
import { api } from "../api.js";
import { Reveal } from "../ui.jsx";

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    offres: 0, candidatures: 0, analyses: 0, topCandidats: []
  });
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/offers"),
      api.get("/candidatures")
    ]).then(async ([offresData, candData]) => {
      const totalOffres = offresData.offres.length;
      const totalCand = candData.candidatures.length;
      
      const terminees = candData.candidatures.filter(c => c.statut === "analyse_terminee");
      
      // Récupérer les scores de toutes les candidatures terminées
      const scoresPromises = terminees.map(c => 
        api.get(`/candidatures/${c.id}/resultat`)
           .then(res => ({ ...c, score: res.score_global }))
           .catch(() => ({ ...c, score: 0 }))
      );
      
      const resultats = await Promise.all(scoresPromises);
      // Trier par score décroissant
      const top = resultats.sort((a, b) => b.score - a.score).slice(0, 3);

      setStats({
        offres: totalOffres,
        candidatures: totalCand,
        analyses: terminees.length,
        topCandidats: top
      });
    }).catch(console.error)
      .finally(() => setChargement(false));
  }, []);

  if (chargement) return <div className="rond" style={{ margin: "100px auto" }} />;

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <div className="tete-page">
        <div>
          <h1>Tableau de bord</h1>
          <p>Vue d'ensemble de votre activité de recrutement.</p>
        </div>
      </div>

      {/* CARTES STATISTIQUES */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <Reveal className="carte" style={{ padding: 24, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ background: "var(--fond)", padding: 16, borderRadius: "50%", color: "var(--ciel)" }}><Briefcase size={28} /></div>
          <div><p style={{ color: "var(--doux)", margin: 0, fontSize: "0.9rem" }}>Offres actives</p><h2 style={{ margin: 0, fontSize: "2rem" }}>{stats.offres}</h2></div>
        </Reveal>
        <Reveal className="carte" delai={0.1} style={{ padding: 24, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ background: "var(--fond)", padding: 16, borderRadius: "50%", color: "var(--abricot)" }}><Users size={28} /></div>
          <div><p style={{ color: "var(--doux)", margin: 0, fontSize: "0.9rem" }}>Candidatures reçues</p><h2 style={{ margin: 0, fontSize: "2rem" }}>{stats.candidatures}</h2></div>
        </Reveal>
        <Reveal className="carte" delai={0.2} style={{ padding: 24, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ background: "#e6f4ea", padding: 16, borderRadius: "50%", color: "#1e8e3e" }}><CheckCircle size={28} /></div>
          <div><p style={{ color: "var(--doux)", margin: 0, fontSize: "0.9rem" }}>Analyses terminées</p><h2 style={{ margin: 0, fontSize: "2rem" }}>{stats.analyses}</h2></div>
        </Reveal>
      </div>

      {/* TOP CANDIDATS */}
      <Reveal className="carte" delai={0.3} style={{ padding: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <Award size={24} color="var(--abricot)" />
          <h2 style={{ margin: 0 }}>Top 3 des meilleurs profils (IA)</h2>
        </div>
        
        {stats.topCandidats.length === 0 ? (
          <p style={{ color: "var(--doux)" }}>Lancez des analyses pour voir le classement des candidats.</p>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {stats.topCandidats.map((c, index) => (
              <div key={c.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", background: "var(--fond)", borderRadius: 12, borderLeft: `4px solid ${index === 0 ? '#1e8e3e' : index === 1 ? '#b06000' : 'var(--bordure)'}` }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <span style={{ fontSize: "1.5rem", fontWeight: "bold", color: "var(--doux)", width: 30 }}>#{index + 1}</span>
                  <div>
                    <h3 style={{ margin: 0 }}>{c.candidat_prenom} {c.candidat_nom}</h3>
                    <small style={{ color: "var(--doux)" }}>Candidat pour : {c.offre_titre}</small>
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "1.8rem", fontWeight: "bold", color: "var(--ciel)" }}>{c.score.toFixed(1)}<span style={{fontSize: "1rem"}}>/100</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Reveal>
    </div>
  );
}