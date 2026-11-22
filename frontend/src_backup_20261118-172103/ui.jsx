import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { X } from "lucide-react";

/* ---------- la marque : une passerelle (un arc) entre deux personnes ---------- */
export function MarqueLogo({ clair = false }) {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M6 33 C12 9 36 9 42 33" fill="none" stroke={clair ? "#fff8ee" : "#1b1a3f"} strokeWidth="3.6" strokeLinecap="round" />
      <circle cx="8" cy="36" r="4.6" fill="#7f9be0" /><circle cx="40" cy="36" r="4.6" fill="#ff9f6b" />
    </svg>
  );
}
export function Marque({ to = "/" }) {
  return <Link to={to} className="marque" aria-label="Passerelle, retour à l'accueil"><MarqueLogo />Passerelle</Link>;
}

/* ---------- visages illustrés : pour que le site reste humain ---------- */
const PEAUX = ["#f2c6a0", "#e0a77a", "#b97a52", "#8d5a3b", "#f6d7bd"];
const CHEVEUX = ["#2b1b14", "#4a2c1a", "#161012", "#7a4a2a", "#3b2a4a"];
const HAUTS = ["#7f9be0", "#ff9f6b", "#5eb894", "#1b1a3f", "#e8b4c8"];
const FONDS = [["#fde3d2", "#f9cdb4"], ["#dce6fb", "#bccdf5"], ["#dff3ea", "#bde4d2"], ["#ece6fa", "#d5cbf2"]];

export function Avatar({ i = 0, size = 56, variante = i % 4, className = "" }) {
  const peau = PEAUX[i % PEAUX.length], cheveux = CHEVEUX[(i + 1) % CHEVEUX.length], haut = HAUTS[(i + 2) % HAUTS.length], [f1, f2] = FONDS[i % FONDS.length];
  return (
    <svg className={"avatar " + className} width={size} height={size} viewBox="0 0 100 100" aria-hidden="true" style={{ borderRadius: "50%", flex: "none" }}>
      <defs><linearGradient id={"fondAv" + i + size} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor={f1} /><stop offset="1" stopColor={f2} /></linearGradient></defs>
      <rect width="100" height="100" fill={`url(#fondAv${i}${size})`} />
      {variante === 1 && <path d="M25 48 C21 14 79 14 75 48 L78 80 C66 78 64 62 64 54 L36 54 C36 62 34 78 22 80 Z" fill={cheveux} />}
      {variante === 3 && <circle cx="50" cy="17" r="11" fill={cheveux} />}
      <path d="M10 100 C12 76 30 68 50 68 C70 68 88 76 90 100 Z" fill={haut} />
      <rect x="43" y="58" width="14" height="14" rx="6" fill={peau} />
      <circle cx="50" cy="44" r="21" fill={peau} />
      {variante === 0 && <path d="M28 44 C26 20 74 20 72 44 C66 32 34 32 28 44 Z" fill={cheveux} />}
      {variante === 1 && <path d="M29 42 C32 24 68 24 71 42 C60 36 40 36 29 42 Z" fill={cheveux} />}
      {variante === 2 && [32, 42, 52, 62, 70].map((x, k) => <circle key={k} cx={x} cy={k % 2 ? 24 : 27} r="10" fill={cheveux} />)}
      {variante === 3 && <path d="M29 42 C30 26 70 26 71 42 C62 34 38 34 29 42 Z" fill={cheveux} />}
      <circle cx="42" cy="46" r="2" fill="#1b1410" /><circle cx="58" cy="46" r="2" fill="#1b1410" />
      <path d="M43 54 Q50 60 57 54" fill="none" stroke="#1b1410" strokeWidth="2" strokeLinecap="round" />
      <circle cx="36" cy="53" r="4" fill="#ff9f6b" opacity=".3" /><circle cx="64" cy="53" r="4" fill="#ff9f6b" opacity=".3" />
    </svg>
  );
}

/* ---------- mouvements : apparition au défilement, compteur, parallaxe ---------- */
export function Reveal({ children, delai = 0, className = "", as: Tag = "div", ...reste }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    if (!("IntersectionObserver" in window)) { el.classList.add("visible"); return; }
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { el.classList.add("visible"); obs.disconnect(); } }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    obs.observe(el); return () => obs.disconnect();
  }, []);
  return <Tag ref={ref} className={"reveal " + className} style={{ "--d": delai + "s" }} {...reste}>{children}</Tag>;
}

export function useCompte(cible, duree = 1400) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (cible == null) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { setV(cible); return; }
    let raf, debut; const t0 = performance.now();
    const pas = (t) => { debut = debut ?? t; const p = Math.min(1, (t - t0) / duree), e = 1 - Math.pow(1 - p, 3); setV(Math.round(cible * e)); if (p < 1) raf = requestAnimationFrame(pas); };
    raf = requestAnimationFrame(pas); return () => cancelAnimationFrame(raf);
  }, [cible, duree]);
  return v;
}

export function useParallaxe() {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current; if (!el || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const bouge = (e) => { const r = el.getBoundingClientRect(); el.style.setProperty("--px", ((e.clientX - r.left) / r.width - 0.5) * 2); el.style.setProperty("--py", ((e.clientY - r.top) / r.height - 0.5) * 2); };
    const repos = () => { el.style.setProperty("--px", 0); el.style.setProperty("--py", 0); };
    el.addEventListener("pointermove", bouge); el.addEventListener("pointerleave", repos);
    return () => { el.removeEventListener("pointermove", bouge); el.removeEventListener("pointerleave", repos); };
  }, []);
  return ref;
}

/* ---------- saisie de mots-clés : Entrée ou virgule pour ajouter ---------- */
export function SaisieTags({ valeur, onChange, placeholder }) {
  const [texte, setTexte] = useState("");
  const ajouter = (brut) => {
    const nouveaux = brut.split(",").map((t) => t.trim()).filter(Boolean);
    if (!nouveaux.length) return;
    const existants = new Set(valeur.map((v) => v.toLowerCase()));
    onChange([...valeur, ...nouveaux.filter((t) => !existants.has(t.toLowerCase()))]); setTexte("");
  };
  return (
    <div className="tags">
      {valeur.map((t) => (
        <span className="tag" key={t}>{t}<button type="button" aria-label={"Retirer " + t} onClick={() => onChange(valeur.filter((v) => v !== t))}><X size={12} /></button></span>
      ))}
      <input value={texte} placeholder={valeur.length ? "" : placeholder}
        onChange={(e) => (e.target.value.endsWith(",") ? ajouter(e.target.value) : setTexte(e.target.value))}
        onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); ajouter(texte); } if (e.key === "Backspace" && !texte && valeur.length) onChange(valeur.slice(0, -1)); }}
        onBlur={() => ajouter(texte)} />
    </div>
  );
}

export const Puces = ({ liste, classe = "puce", vide = "Non précisées" }) => (
  <ul className="puces">{liste.length ? liste.map((c) => <li className={classe} key={c}>{c}</li>) : <li style={{ color: "var(--doux)" }}>{vide}</li>}</ul>
);
