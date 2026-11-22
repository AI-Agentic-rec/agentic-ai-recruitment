import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { Puces } from "../ui.jsx";

const pause = (ms) => new Promise((r) => setTimeout(r, ms));
const periode = (a, b) => (a || b ? `${a || "?"} → ${b || "aujourd'hui"}` : "");
const langue = (l) => l.langue + (l.niveau ? ` (${l.niveau})` : "");

function Bloc({ titre, children }) { return <div className="res-bloc"><h4>{titre}</h4>{children}</div>; }
function Liste({ items }) { return <ul>{(items.length ? items : ["—"]).map((t, i) => <li key={i}>{t}</li>)}</ul>; }

function ResExigences({ d }) {
  return (
    <>
      <Bloc titre="Poste"><p>{d.titre_poste || "(titre non trouvé)"}</p></Bloc>
      <Bloc titre="Diplôme demandé"><p>{(d.diplome_demande || "non précisé") + (d.niveau_diplome_min != null ? ` · niveau Bac+${d.niveau_diplome_min}` : "")}</p></Bloc>
      <Bloc titre="Expérience minimale"><p>{d.experience_min_annees} an(s)</p></Bloc>
      <Bloc titre="Compétences obligatoires"><Puces liste={d.competences_obligatoires} vide="—" /></Bloc>
      <Bloc titre="Compétences souhaitées"><Puces liste={d.competences_souhaitees} classe="puce chaud" vide="—" /></Bloc>
      <Bloc titre="Langues"><p>{d.langues.map(langue).join(", ") || "non précisées"}</p></Bloc>
      <Bloc titre="Missions"><Liste items={d.missions} /></Bloc>
    </>
  );
}

function ResProfil({ d }) {
  const nom = [d.prenom, d.nom].filter(Boolean).join(" ") || "(nom non trouvé)";
  const plein = (arr) => arr.filter((v) => v !== null && v !== undefined && v !== "").join(" · ");
  return (
    <>
      <Bloc titre="Candidat"><p>{plein([nom, d.email, d.telephone])}</p></Bloc>
      <Bloc titre="Formations"><Liste items={d.formations.map((x) => plein([x.diplome, x.specialite, x.etablissement, periode(x.date_debut, x.date_fin)]))} /></Bloc>
      <Bloc titre="Expériences"><Liste items={d.experiences.map((x) => plein([x.poste, x.entreprise, periode(x.date_debut, x.date_fin), x.duree_annees != null ? `≈ ${x.duree_annees} an(s)` : ""]))} /></Bloc>
      <Bloc titre="Expérience totale"><p>{d.experience_totale_annees} an(s) · calculée par le programme, pas par le modèle</p></Bloc>
      <Bloc titre="Compétences"><Puces liste={d.competences} vide="—" /></Bloc>
      <Bloc titre="Langues"><p>{d.langues.map(langue).join(", ") || "non précisées"}</p></Bloc>
      <Bloc titre="Certifications"><Liste items={d.certifications} /></Bloc>
    </>
  );
}

function Compteur({ debut }) {
  const [s, setS] = useState(0);
  useEffect(() => { const t = setInterval(() => setS(Math.round((Date.now() - debut) / 1000)), 1000); return () => clearInterval(t); }, [debut]);
  return <span>Mistral réfléchit… {s} s (jusqu'à 2 minutes la première fois)</span>;
}

function Zone({ etat, agent }) {
  if (!etat) return null;
  if (etat.statut === "attente") return <div className="attente" aria-live="polite"><span className="rond" /><Compteur debut={etat.debut} /></div>;
  if (etat.statut === "erreur") return <div className="alerte" role="alert"><b>L'agent n'a pas réussi : </b>{etat.message}</div>;
  return (
    <div className="resultat" aria-live="polite">
      <p className="duree">Terminé en {etat.job.duree} s · réponse validée par le schéma de l'équipe</p>
      {agent === 1 ? <ResExigences d={etat.job.resultat} /> : <ResProfil d={etat.job.resultat} />}
      <details><summary>Voir le JSON brut</summary><pre>{JSON.stringify(etat.job.resultat, null, 2)}</pre></details>
    </div>
  );
}

export default function AgentsLab() {
  const [etatIA, setEtatIA] = useState(null), [offres, setOffres] = useState([]), [exemples, setExemples] = useState([]);
  const [offreId, setOffreId] = useState(""), [exemple, setExemple] = useState(""), [fichier, setFichier] = useState(null);
  const [r1, setR1] = useState(null), [r2, setR2] = useState(null);
  const vivant = useRef(true);

  useEffect(() => {
    vivant.current = true;
    api.get("/admin/agents/statut").then(setEtatIA).catch(() => setEtatIA({ pret: false, message: "État inconnu" }));
    api.get("/offers").then((d) => { setOffres(d.offres); if (d.offres[0]) setOffreId(String(d.offres[0].id)); }).catch(() => {});
    api.get("/admin/agents/exemples").then((d) => { setExemples(d.exemples); if (d.exemples[0]) setExemple(d.exemples[0]); }).catch(() => {});
    return () => { vivant.current = false; };
  }, []);

  // 1) on demande le lancement  2) le serveur répond tout de suite avec un numéro de job  3) on l'interroge toutes les 2 s
  const suivre = async (demarrer, setEtat) => {
    setEtat({ statut: "attente", debut: Date.now() });
    try {
      const { job_id } = await demarrer();
      for (;;) {
        await pause(2000);
        if (!vivant.current) return;
        const job = await api.get(`/admin/agents/jobs/${job_id}`);
        if (job.statut === "en_cours") continue;
        setEtat(job.statut === "termine" ? { statut: "fini", job } : { statut: "erreur", message: job.message });
        return;
      }
    } catch (e) { vivant.current && setEtat({ statut: "erreur", message: e.message }); }
  };
  const occupe1 = r1?.statut === "attente", occupe2 = r2?.statut === "attente";
  const envoyerCV = () => {
    if (!fichier) return setR2({ statut: "erreur", message: "Choisissez d'abord un fichier PDF ou DOCX." });
    const fd = new FormData(); fd.append("fichier", fichier);
    suivre(() => api.upload("/admin/agents/cv/analyser", fd), setR2);
  };

  return (
    <>
      <div className="tete-page">
        <div><h1>Agents IA</h1><p>Essayez les agents un par un, avant de les relier au traitement des candidatures.</p></div>
        <span className={"pilule-etat " + (etatIA ? (etatIA.pret ? "ok" : "ko") : "")}><i />{etatIA ? etatIA.message : "Vérification d'Ollama…"}</span>
      </div>
      <div className="explique carte">
        <b>Ce qui se passe quand vous cliquez</b>
        <ol>
          <li>Le site envoie le texte à l'agent, une fonction Python.</li>
          <li>L'agent le transmet à Ollama, qui fait tourner le modèle Mistral 7B sur votre ordinateur.</li>
          <li>Mistral répond en JSON, et l'agent vérifie la réponse avec le schéma de l'équipe.</li>
          <li>Le résultat s'affiche ici. Comptez jusqu'à 2 minutes.</li>
        </ol>
      </div>

      <section className="agent carte">
        <div className="agent-tete"><span className="agent-num">1</span><div><h2>Lire une offre</h2><p>Le Job Requirement Agent en tire des exigences structurées.</p></div></div>
        <label className="champ">Choisissez une offre
          <select value={offreId} onChange={(e) => setOffreId(e.target.value)} disabled={!offres.length}>
            {offres.length ? offres.map((o) => <option key={o.id} value={o.id}>{o.titre} ({o.statut === "publiee" ? "publiée" : o.statut === "cloturee" ? "clôturée" : "brouillon"})</option>) : <option>Aucune offre : créez-en une d'abord</option>}
          </select>
        </label>
        <div><button className="btn btn-plein" disabled={!offreId || occupe1} onClick={() => suivre(() => api.post(`/admin/agents/offre/${offreId}/analyser`), setR1)}>Analyser l'offre</button></div>
        <Zone etat={r1} agent={1} />
      </section>

      <section className="agent b carte">
        <div className="agent-tete"><span className="agent-num">2</span><div><h2>Lire un CV</h2><p>Le CV Extraction Agent en tire un profil structuré, au format PDF ou Word.</p></div></div>
        <label className="champ">Envoyer un CV <small>fictif uniquement · PDF ou DOCX · 5 Mo maximum</small>
          <input type="file" accept=".pdf,.docx" onChange={(e) => setFichier(e.target.files[0] || null)} />
        </label>
        <div><button className="btn btn-plein" disabled={occupe2} onClick={envoyerCV}>Analyser ce CV</button></div>
        {exemples.length > 0 && (
          <div className="ligne-choix">
            <label className="champ">…ou essayez un CV d'exemple
              <select value={exemple} onChange={(e) => setExemple(e.target.value)}>{exemples.map((n) => <option key={n}>{n}</option>)}</select>
            </label>
            <button className="btn btn-carte" style={{ alignSelf: "end" }} disabled={occupe2} onClick={() => suivre(() => api.post(`/admin/agents/cv/exemple/${encodeURIComponent(exemple)}`), setR2)}>Analyser l'exemple</button>
          </div>
        )}
        <Zone etat={r2} agent={2} />
      </section>
    </>
  );
}
