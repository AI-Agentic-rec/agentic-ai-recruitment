/* ===== Illustrations : un paysage de brume et de montagnes, et la passerelle que des personnes traversent =====
   Tout est dessiné en SVG (aucune image externe). Les crêtes sont générées avec une graine : chaque offre a donc son propre petit paysage. */

function hasard(graine) {
  let a = graine >>> 0;
  return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export function crete(graine, base, amplitude, { n = 14, x0 = -140, x1 = 1740, bas = 940, lisse = 0.55 } = {}) {
  const r = hasard(graine), pas = (x1 - x0) / n, pts = [];
  let h = 0.5;
  for (let i = 0; i <= n; i++) {
    h = h * (1 - lisse) + r() * lisse;
    pts.push([x0 + i * pas, base - amplitude * Math.min(1, h + (r() > 0.8 ? 0.32 : 0))]);
  }
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d + ` L${x1} ${bas} L${x0} ${bas} Z`;
}

const bez = (t, a, b, c) => (1 - t) * (1 - t) * a + 2 * (1 - t) * t * b + t * t * c;
const COURBE = { x0: 372, y0: 588, cx: 711, cy: 478, x1: 1050, y1: 586 };           // le tablier de la passerelle
const pt = (t, dy = 0, c = COURBE) => [bez(t, c.x0, c.cx, c.x1), bez(t, c.y0, c.cy, c.y1) + dy];

function Passerelle() {
  const poteaux = Array.from({ length: 23 }, (_, i) => i / 22);
  const marche = (inverse) => {                                    // chemin des promeneurs (les pieds posés sur le tablier)
    const pts = Array.from({ length: 13 }, (_, i) => pt(i / 12, -12));
    return "M" + (inverse ? [...pts].reverse() : pts).map((p) => p.map((v) => v.toFixed(1)).join(" ")).join(" L");
  };
  const gens = [
    { c: "#1b1a3f", d: 70, deb: -10, inv: false }, { c: "#ff9f6b", d: 84, deb: -52, inv: true },
    { c: "#6bbf9f", d: 96, deb: -30, inv: false }, { c: "#f4f1ff", d: 76, deb: -61, inv: true }, { c: "#7f9be0", d: 110, deb: -80, inv: false },
  ];
  return (
    <g>
      <path d={`M${COURBE.x0} ${COURBE.y0 + 2} Q${COURBE.cx} ${COURBE.cy + 6} ${COURBE.x1} ${COURBE.y1 + 2} L${COURBE.x1} ${COURBE.y1 + 18} Q${COURBE.cx} ${COURBE.cy + 26} ${COURBE.x0} ${COURBE.y0 + 20} Z`} fill="#dde3f8" opacity=".9" />
      <path d={`M${COURBE.x0} ${COURBE.y0} Q${COURBE.cx} ${COURBE.cy} ${COURBE.x1} ${COURBE.y1}`} fill="none" stroke="#fff8ee" strokeWidth="9" strokeLinecap="round" />
      <path d={`M${COURBE.x0} ${COURBE.y0 - 30} Q${COURBE.cx} ${COURBE.cy - 30} ${COURBE.x1} ${COURBE.y1 - 30}`} fill="none" stroke="#fff8ee" strokeWidth="3" strokeLinecap="round" />
      {poteaux.map((t, i) => { const [x, y] = pt(t), [, yh] = pt(t, -30); return <line key={i} x1={x} y1={y} x2={x} y2={yh} stroke="#fff8ee" strokeWidth="2" opacity=".9" />; })}
      {poteaux.filter((_, i) => i % 4 === 2).map((t, i) => { const [x, y] = pt(t, -32); return (
        <g key={i}><circle cx={x} cy={y} r="22" fill="#ffc27a" opacity=".38" className="lampe" style={{ animationDelay: `${i * 0.7}s` }} /><circle cx={x} cy={y} r="4.5" fill="#ffd9a3" /></g>
      ); })}
      {gens.map((g, i) => (
        <g key={i}>
          <animateMotion dur={`${g.d}s`} begin={`${g.deb}s`} repeatCount="indefinite" path={marche(g.inv)} />
          <g className="marcheur" style={{ animationDelay: `${i * 0.19}s` }}>
            <circle cx="0" cy="-17" r="3.8" fill={g.c} /><path d="M-3.6 -12.5 h7.2 q1 7 .2 12.5 h-7.6 q-.8 -5.5 .2 -12.5 z" fill={g.c} />
          </g>
        </g>
      ))}
    </g>
  );
}

export function ScenePrincipale() {
  const arbres = (x0, x1, y, graine) => { const r = hasard(graine); return Array.from({ length: 11 }, (_, i) => { const x = x0 + (x1 - x0) * (i / 10) + r() * 18, h = 40 + r() * 34; return <path key={i} d={`M${x} ${y} l${-9} 0 l9 ${-h} l9 ${h} z`} fill="#2e3a7c" opacity={0.9} />; }); };
  return (
    <svg className="scene" viewBox="0 0 1600 900" preserveAspectRatio="xMinYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="ciel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#7e96da" /><stop offset=".42" stopColor="#a9bdf0" /><stop offset=".7" stopColor="#d9d3ee" /><stop offset=".88" stopColor="#f6cdb4" /><stop offset="1" stopColor="#f9dcc4" /></linearGradient>
        <radialGradient id="soleil" cx="1130" cy="590" r="460" gradientUnits="userSpaceOnUse"><stop offset="0" stopColor="#fff0d8" stopOpacity=".95" /><stop offset=".35" stopColor="#ffd9b8" stopOpacity=".5" /><stop offset="1" stopColor="#ffd9b8" stopOpacity="0" /></radialGradient>
        <linearGradient id="m1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#c3ccee" /><stop offset="1" stopColor="#d8dbf0" /></linearGradient>
        <linearGradient id="m2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#a1b0e2" /><stop offset="1" stopColor="#c2cbec" /></linearGradient>
        <linearGradient id="m3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8496d3" /><stop offset="1" stopColor="#a9b6e4" /></linearGradient>
        <linearGradient id="brume" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff" stopOpacity="0" /><stop offset=".55" stopColor="#fff" stopOpacity=".6" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></linearGradient>
        <linearGradient id="falaise" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#5565ab" /><stop offset="1" stopColor="#323d80" /></linearGradient>
        <filter id="flou" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14" /></filter>
      </defs>
      <rect width="1600" height="900" fill="url(#ciel)" />
      <rect width="1600" height="900" fill="url(#soleil)" />
      <circle cx="1130" cy="600" r="44" fill="#fff4e2" opacity=".9" />
      <g className="nuages" filter="url(#flou)" opacity=".75">
        <ellipse className="nuage n1" cx="330" cy="210" rx="190" ry="34" fill="#fff" /><ellipse className="nuage n2" cx="980" cy="150" rx="250" ry="40" fill="#fff" opacity=".8" />
        <ellipse className="nuage n3" cx="1420" cy="290" rx="170" ry="30" fill="#fff" opacity=".9" /><ellipse className="nuage n4" cx="640" cy="330" rx="150" ry="24" fill="#fff" opacity=".7" />
      </g>
      <g className="couche" style={{ "--k": 5 }}><path d={crete(11, 505, 150, { n: 11 })} fill="url(#m1)" /></g>
      <rect y="470" width="1600" height="150" fill="url(#brume)" />
      <g className="couche" style={{ "--k": 11 }}><path d={crete(23, 585, 150, { n: 12 })} fill="url(#m2)" /></g>
      <rect y="540" width="1600" height="140" fill="url(#brume)" opacity=".85" />
      <g className="couche" style={{ "--k": 18 }}><path d={crete(37, 680, 130, { n: 13 })} fill="url(#m3)" /></g>
      <rect y="640" width="1600" height="160" fill="url(#brume)" opacity=".8" />
      <g className="couche" style={{ "--k": 28 }}>
        <path d="M-260 940 L-260 470 C-170 446 20 470 120 506 C230 548 310 584 372 590 L440 606 L440 940 Z" fill="url(#falaise)" />
        <path d="M1000 940 L1000 596 L1050 588 C1160 576 1270 540 1370 498 C1490 448 1640 440 1860 470 L1860 940 Z" fill="url(#falaise)" />
        {arbres(-120, 330, 548, 5)}{arbres(1100, 1500, 560, 9)}
        <Passerelle />
      </g>
      <rect y="760" width="1600" height="160" fill="url(#brume)" opacity=".55" />
      <g className="oiseaux" fill="none" stroke="#3a4690" strokeWidth="2" strokeLinecap="round">
        {[0, 1, 2].map((i) => <g key={i}><animateMotion dur={`${48 + i * 9}s`} begin={`${-i * 14}s`} repeatCount="indefinite" path="M-60 260 C400 180 900 330 1700 230" /><path d="M-9 0 q4.5 -5 9 0 q4.5 -5 9 0" /></g>)}
      </g>
    </svg>
  );
}

/* ----- petit paysage propre à chaque offre (couverture des cartes) ----- */
const CIELS = [["#8aa3e6", "#f7d2b8"], ["#8fd0cf", "#fbe6c8"], ["#a897e0", "#f9cfc4"], ["#86bfa6", "#f6e3c0"]];
export function Vignette({ id, className = "" }) {
  const [haut, bas] = CIELS[id % CIELS.length], s = id * 7 + 3;
  return (
    <svg className={"vignette " + className} viewBox="0 0 640 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id={`vc${id}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={haut} /><stop offset="1" stopColor={bas} /></linearGradient>
        <linearGradient id={`vm${id}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".55" /><stop offset="1" stopColor="#fff" stopOpacity=".15" /></linearGradient>
      </defs>
      <rect width="640" height="300" fill={`url(#vc${id})`} />
      <circle cx={380 + (id % 4) * 40} cy="150" r="30" fill="#fff6e6" opacity=".9" />
      <path d={crete(s, 190, 90, { n: 8, x0: -20, x1: 660, bas: 320 })} fill={`url(#vm${id})`} />
      <path d={crete(s + 5, 235, 70, { n: 9, x0: -20, x1: 660, bas: 320 })} fill="#fff" opacity=".42" />
      <path d={crete(s + 9, 280, 52, { n: 7, x0: -20, x1: 660, bas: 320 })} fill="#1b1a3f" opacity=".78" />
      <path d="M190 262 Q320 214 450 262" fill="none" stroke="#fff8ee" strokeWidth="5" strokeLinecap="round" />
      <path d="M190 242 Q320 194 450 242" fill="none" stroke="#fff8ee" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/* ----- grande silhouette très pâle derrière toute la page ----- */
export function FondPage() {
  return (
    <div className="fond-page" aria-hidden="true">
      <svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice">
        <path d={crete(71, 640, 240, { n: 10 })} fill="#d3dbea" opacity=".6" />
        <path d={crete(83, 760, 190, { n: 11 })} fill="#c4cfe3" opacity=".5" />
      </svg>
    </div>
  );
}
