import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpLeft, ArrowUpRight, Briefcase, ChevronDown, GraduationCap, MapPin, Search } from "lucide-react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Avatar, MarqueLogo, Puces, Reveal, useCompte, useParallaxe } from "../ui.jsx";
import { ScenePrincipale, Vignette } from "../scene.jsx";

const LIGNES = ["Une nouvelle", "façon de recruter"];
function TitreGeant() {
  let i = 0;
  return (
    <h1 className="titre-geant" aria-label={LIGNES.join(" ")}>
      {LIGNES.map((ligne, k) => (
        <span key={k} style={{ display: "block" }} aria-hidden="true">
          {ligne.split(" ").map((mot, m) => (
            <span key={m}>{m > 0 && <span className="esp" />}<span className="mot">{[...mot].map((c) => <span className="l" key={i} style={{ "--i": i++ }}>{c}</span>)}</span></span>
          ))}
        </span>
      ))}
    </h1>
  );
}

const experience = (n) => (n === 0 ? "Débutant accepté" : `${n} an${n > 1 ? "s" : ""} d'expérience`);

function Filtres({ f, setF, lieux, variante }) {
  const maj = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const allerAuxOffres = () => document.querySelector("#offres")?.scrollIntoView({ behavior: "smooth" });
  const contenu = (
    <>
      <label className="filtre-champ"><small><MapPin size={13} />Lieu</small>
        <select value={f.lieu} onChange={maj("lieu")}><option value="">Partout</option>{lieux.map((l) => <option key={l}>{l}</option>)}</select><ChevronDown className="fleche" size={16} /></label>
      <label className="filtre-champ"><small><Briefcase size={13} />Expérience</small>
        <select value={f.exp} onChange={maj("exp")}><option value="">Toutes</option><option value="0">Débutant</option><option value="1">1 à 2 ans</option><option value="3">3 ans et plus</option></select><ChevronDown className="fleche" size={16} /></label>
      <label className="filtre-champ"><small><Search size={13} />Mot-clé</small>
        <input value={f.q} onChange={maj("q")} placeholder="Python, données…" aria-label="Mot-clé" /></label>
    </>
  );
  return variante === "liste" ? <div className="filtre-liste">{contenu}</div> : (
    <div className="filtre">{contenu}<button className="go" onClick={allerAuxOffres} aria-label="Voir les résultats"><Search size={19} /></button></div>
  );
}

function CartePoste({ o, i }) {
  return (
    <Reveal delai={(i % 3) * 0.09} as="div">
      <Link to={`/offres/${o.id}`} className="carte-poste carte">
        <div className="couv"><Vignette id={o.id} />{o.localisation && <span className="etiquette">{o.localisation}</span>}</div>
        <div className="corps">
          <h3>{o.titre}</h3>
          <div className="meta">
            <span><Briefcase size={16} />{experience(o.experience_annees)}</span>
            {o.diplome_demande && <span><GraduationCap size={16} />{o.diplome_demande}</span>}
          </div>
          <Puces liste={o.competences_obligatoires.slice(0, 4)} vide="" />
          <div className="pied-carte"><b style={{ fontWeight: 800 }}>Voir l'offre</b><span className="rond-fleche"><ArrowUpRight size={20} /></span></div>
        </div>
      </Link>
    </Reveal>
  );
}

export default function Home() {
  const { user } = useAuth();
  const [offres, setOffres] = useState(null), [erreur, setErreur] = useState("");
  const [f, setF] = useState({ lieu: "", exp: "", q: "" });
  const parallaxe = useParallaxe();

  useEffect(() => { api.get("/offres").then((d) => setOffres(d.offres)).catch((e) => setErreur(e.message)); }, []);
  const lieux = useMemo(() => [...new Set((offres || []).map((o) => o.localisation).filter(Boolean))], [offres]);
  const visibles = useMemo(() => (offres || []).filter((o) => {
    const q = f.q.trim().toLowerCase();
    const texte = [o.titre, o.description, o.localisation, ...o.competences_obligatoires, ...o.competences_souhaitees].join(" ").toLowerCase();
    const n = o.experience_annees;
    return (!f.lieu || o.localisation === f.lieu) && (!q || texte.includes(q)) &&
      (f.exp === "" || (f.exp === "0" && n === 0) || (f.exp === "1" && n >= 1 && n <= 2) || (f.exp === "3" && n >= 3));
  }), [offres, f]);
  const total = offres?.length ?? 0, compte = useCompte(offres ? total : null);
  const unique = offres?.[0];
  const filtre = f.lieu || f.exp || f.q;

  return (
    <>
      <section className="fenetre" ref={parallaxe} aria-label="Présentation">
        <ScenePrincipale />
        <div className="barre-haut">
          <Link to={{ pathname: "/", hash: "#offres" }} className="pilule"><ArrowUpLeft size={18} />Postuler</Link>
          <Filtres f={f} setF={setF} lieux={lieux} variante="hero" />
          <Link to={user?.role === "admin" ? "/admin" : "/connexion"} className="pilule">Recruter<ArrowUpRight size={18} /></Link>
        </div>
        <TitreGeant />
        <p className="intro">Passerelle relie celles et ceux qui cherchent un poste à celles et ceux qui le proposent. Chaque dossier est <b>lu avec attention</b>, expliqué clairement, et c'est toujours <b>une personne qui décide</b>.</p>

        <Link to={{ pathname: "/", hash: "#offres" }} className="carte-trouver">
          <h2>Trouvez le bon poste</h2>
          <p>Parcourez les offres ouvertes, postulez, puis suivez votre dossier étape par étape.</p>
          <div className="chiffre-ligne">
            <b>{compte}</b><small>offre{total > 1 ? "s" : ""}<br />ouverte{total > 1 ? "s" : ""}</small>
            <span className="visages" aria-hidden="true">{[0, 1, 2].map((k) => <Avatar key={k} i={k + 1} variante={k + 1} size={42} />)}</span>
            <span className="rond-fleche"><ArrowUpRight size={22} /></span>
          </div>
        </Link>

        {unique ? (
          <Link to={`/offres/${unique.id}`} className="carte-offre givre">
            <div className="haut">
              <div><h3>{unique.titre}</h3>{unique.localisation && <p className="lieu"><MapPin size={16} />{unique.localisation}</p>}</div>
              <span className="rond-fleche"><ArrowUpRight size={22} /></span>
            </div>
            <p className="apercu">{unique.description}</p>
            <div className="infos"><span><Briefcase size={16} />{experience(unique.experience_annees)}</span>{unique.diplome_demande && <span><GraduationCap size={16} />{unique.diplome_demande}</span>}</div>
            <Puces liste={unique.competences_obligatoires.slice(0, 3)} vide="" />
          </Link>
        ) : (
          <div className="carte-offre givre"><h3>{offres ? "Aucune offre pour le moment" : "Chargement…"}</h3><p className="apercu">De nouveaux postes sont publiés régulièrement. Revenez bientôt.</p></div>
        )}
        <Link to="/" className="pastille-marque" aria-label="Passerelle"><MarqueLogo clair /></Link>
      </section>

      <div className="conteneur">
        <section className="section" id="offres">
          <Reveal className="section-tete">
            <div>
              <h2>Des postes décrits avec soin</h2>
              <p>Ce qu'on attend, ce qu'on apprécie, où et avec quelle expérience. Pas de jargon, pas de surprise.</p>
            </div>
            {offres && <p className="compte">{visibles.length} poste{visibles.length > 1 ? "s" : ""}{filtre ? " correspondant" + (visibles.length > 1 ? "s" : "") : ""}{filtre && <button onClick={() => setF({ lieu: "", exp: "", q: "" })}>Tout afficher</button>}</p>}
          </Reveal>
          <Filtres f={f} setF={setF} lieux={lieux} variante="liste" />
          {erreur && <div className="alerte">{erreur}</div>}
          <div className="liste-offres">
            {visibles.map((o, i) => <CartePoste key={o.id} o={o} i={i} />)}
            {offres && visibles.length === 0 && (
              <div className="vide carte"><h3>{filtre ? "Aucun poste ne correspond" : "Aucune offre ouverte pour le moment"}</h3><p>{filtre ? "Essayez d'élargir le lieu ou l'expérience, ou changez de mot-clé." : "Revenez bientôt : de nouveaux postes sont publiés régulièrement."}</p>{filtre && <button className="btn btn-plein btn-petit" onClick={() => setF({ lieu: "", exp: "", q: "" })}>Tout afficher</button>}</div>
            )}
          </div>
        </section>

        <section className="section">
          <Reveal className="recit">
            <div>
              <h2>La machine prépare. Une personne décide.</h2>
              <p className="texte">Cinq agents lisent l'offre et votre dossier, comparent, puis rédigent un rapport expliqué. Mais ils ne démarrent jamais seuls, et ils ne prennent jamais la décision finale.</p>
              <Link to="/comment-ca-marche" className="btn btn-plein">Voir comment c'est fait <ArrowRight size={18} /></Link>
            </div>
            <ol className="recit-liste">
              <li><div><b>Vous déposez votre dossier</b><span>CV, diplôme et CIN, en toute simplicité.</span></div></li>
              <li><div><b>Le recruteur lance l'analyse</b><span>Rien ne démarre sans lui.</span></div></li>
              <li><div><b>Un rapport expliqué</b><span>Chaque point du score est justifié.</span></div></li>
              <li><div><b>Une personne décide</b><span>Le score aide, il ne tranche pas.</span></div></li>
            </ol>
          </Reveal>
        </section>
      </div>
    </>
  );
}
