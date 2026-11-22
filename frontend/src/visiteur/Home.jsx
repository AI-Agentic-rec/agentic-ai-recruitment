import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next"; // ✅ IMPORT
import { ArrowRight, ArrowUpLeft, ArrowUpRight, Briefcase, ChevronDown, GraduationCap, MapPin, Search } from "lucide-react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Avatar, MarqueLogo, Puces, Reveal, useCompte, useParallaxe } from "../ui.jsx";
import { ScenePrincipale, Vignette } from "../scene.jsx";

// ✅ Le composant accepte maintenant les lignes en paramètre
function TitreGeant({ lines }) {
  let i = 0;
  return (
    <h1 className="titre-geant" aria-label={lines.join(" ")}>
      {lines.map((ligne, k) => (
        <span key={k} style={{ display: "block" }} aria-hidden="true">
          {ligne.split(" ").map((mot, m) => (
            <span key={m}>{m > 0 && <span className="esp" />}<span className="mot">{[...mot].map((c) => <span className="l" key={i} style={{ "--i": i++ }}>{c}</span>)}</span></span>
          ))}
        </span>
      ))}
    </h1>
  );
}

// ✅ Traduction de la fonction experience
const formatExperience = (n, t) => {
  return n === 0 ? t('home.beginner') : t('home.years_exp', { count: n });
};

function Filtres({ f, setF, lieux, variante }) {
  const { t } = useTranslation(); // ✅ HOOK ICI
  const maj = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const allerAuxOffres = () => document.querySelector("#offres")?.scrollIntoView({ behavior: "smooth" });
  
  const contenu = (
    <>
      <label className="filtre-champ"><small><MapPin size={13} />{t('filters.location')}</small>
        <select value={f.lieu} onChange={maj("lieu")}><option value="">{t('filters.everywhere')}</option>{lieux.map((l) => <option key={l}>{l}</option>)}</select><ChevronDown className="fleche" size={16} /></label>
      <label className="filtre-champ"><small><Briefcase size={13} />{t('filters.experience')}</small>
        <select value={f.exp} onChange={maj("exp")}><option value="">{t('filters.all')}</option><option value="0">{t('filters.beginner')}</option><option value="1">{t('filters.1_2_years')}</option><option value="3">{t('filters.3_plus')}</option></select><ChevronDown className="fleche" size={16} /></label>
      <label className="filtre-champ"><small><Search size={13} />{t('filters.keyword')}</small>
        <input value={f.q} onChange={maj("q")} placeholder={t('filters.keyword_placeholder')} aria-label={t('filters.keyword')} /></label>
    </>
  );
  return variante === "liste" ? <div className="filtre-liste">{contenu}</div> : (
    <div className="filtre">{contenu}<button className="go" onClick={allerAuxOffres} aria-label={t('filters.view_results')}><Search size={19} /></button></div>
  );
}

function CartePoste({ o, i }) {
  const { t } = useTranslation(); // ✅ HOOK ICI
  return (
    <Reveal delai={(i % 3) * 0.09} as="div">
      <Link to={`/offers/${o.id}`} className="carte-poste carte">
        <div className="couv"><Vignette id={o.id} />{o.localisation && <span className="etiquette">{o.localisation}</span>}</div>
        <div className="corps">
          <h3>{o.titre}</h3>
          <div className="meta">
            <span><Briefcase size={16} />{formatExperience(o.experience_annees, t)}</span>
            {o.diplome_demande && <span><GraduationCap size={16} />{o.diplome_demande}</span>}
          </div>
          <Puces liste={o.competences_obligatoires.slice(0, 4)} vide="" />
          <div className="pied-carte"><b style={{ fontWeight: 800 }}>{t('home.see_job')}</b><span className="rond-fleche"><ArrowUpRight size={20} /></span></div>
        </div>
      </Link>
    </Reveal>
  );
}

export default function Home() {
  const { user } = useAuth();
  const { t } = useTranslation(); // ✅ HOOK PRINCIPAL
  const [offres, setOffres] = useState(null), [erreur, setErreur] = useState("");
  const [f, setF] = useState({ lieu: "", exp: "", q: "" });
  const parallaxe = useParallaxe();

  useEffect(() => { api.get("/offers").then((d) => setOffres(d.offres)).catch((e) => setErreur(e.message)); }, []);
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
          <Link to={{ pathname: "/", hash: "#offres" }} className="pilule"><ArrowUpLeft size={18} />{t('home.apply')}</Link>
          <Filtres f={f} setF={setF} lieux={lieux} variante="hero" />
          <Link to={user?.role === "admin" ? "/admin" : "/connexion"} className="pilule">{t('home.recruit')}<ArrowUpRight size={18} /></Link>
        </div>
        
        {/* ✅ On passe les lignes traduites au composant */}
        <TitreGeant lines={[t('home.line1'), t('home.line2')]} />
        
        <p className="intro">{t('home.intro')}</p>

        <Link to={{ pathname: "/", hash: "#offres" }} className="carte-trouver">
          <h2>{t('home.find_job')}</h2>
          <p>{t('home.find_job_desc')}</p>
          <div className="chiffre-ligne">
            <b>{compte}</b><small>{total > 1 ? t('home.offers_open_plural', { count: total }) : t('home.offers_open_single', { count: total })}</small>
            <span className="visages" aria-hidden="true">{[0, 1, 2].map((k) => <Avatar key={k} i={k + 1} variante={k + 1} size={42} />)}</span>
            <span className="rond-fleche"><ArrowUpRight size={22} /></span>
          </div>
        </Link>

        {unique ? (
          <Link to={`/offers/${unique.id}`} className="carte-offre givre">
            <div className="haut">
              <div><h3>{unique.titre}</h3>{unique.localisation && <p className="lieu"><MapPin size={16} />{unique.localisation}</p>}</div>
              <span className="rond-fleche"><ArrowUpRight size={22} /></span>
            </div>
            <p className="apercu">{unique.description}</p>
            <div className="infos"><span><Briefcase size={16} />{formatExperience(unique.experience_annees, t)}</span>{unique.diplome_demande && <span><GraduationCap size={16} />{unique.diplome_demande}</span>}</div>
            <Puces liste={unique.competences_obligatoires.slice(0, 3)} vide="" />
          </Link>
        ) : (
          <div className="carte-offre givre">
            <h3>{offres ? t('home.no_offers') : t('home.loading')}</h3>
            <p className="apercu">{t('home.new_jobs_soon')}</p>
          </div>
        )}
        <Link to="/" className="pastille-marque" aria-label="Passerelle"><MarqueLogo clair /></Link>
      </section>

      <div className="conteneur">
        <section className="section" id="offres">
          <Reveal className="section-tete">
            <div>
              <h2>{t('home.careful_jobs')}</h2>
              <p>{t('home.careful_jobs_desc')}</p>
            </div>
            {offres && <p className="compte">
              {t('home.jobs_count', { count: visibles.length })}
              {filtre && " " + t('home.matching')} 
              {filtre && <button onClick={() => setF({ lieu: "", exp: "", q: "" })}>{t('home.show_all')}</button>}
            </p>}
          </Reveal>
          <Filtres f={f} setF={setF} lieux={lieux} variante="liste" />
          {erreur && <div className="alerte">{erreur}</div>}
          <div className="liste-offres">
            {visibles.map((o, i) => <CartePoste key={o.id} o={o} i={i} />)}
            {offres && visibles.length === 0 && (
              <div className="vide carte">
                <h3>{filtre ? t('home.no_results') : t('home.no_offers')}</h3>
                <p>{filtre ? t('home.try_wider') : t('home.new_jobs_soon')}</p>
                {filtre && <button className="btn btn-plein btn-petit" onClick={() => setF({ lieu: "", exp: "", q: "" })}>{t('home.show_all')}</button>}
              </div>
            )}
          </div>
        </section>

        <section className="section">
          <Reveal className="recit">
            <div>
              <h2>{t('home.process_title')}</h2>
              <p className="texte">{t('home.process_desc')}</p>
              <Link to={{ pathname: "/", hash: "#offres" }} className="btn btn-plein">{t('home.discover_offers')} <ArrowRight size={18} /></Link>
            </div>
            <ol className="recit-liste">
              <li><div><b>{t('home.step1_title')}</b><span>{t('home.step1_desc')}</span></div></li>
              <li><div><b>{t('home.step2_title')}</b><span>{t('home.step2_desc')}</span></div></li>
              <li><div><b>{t('home.step3_title')}</b><span>{t('home.step3_desc')}</span></div></li>
              <li><div><b>{t('home.step4_title')}</b><span>{t('home.step4_desc')}</span></div></li>
            </ol>
          </Reveal>
        </section>
      </div>
    </>
  );
}