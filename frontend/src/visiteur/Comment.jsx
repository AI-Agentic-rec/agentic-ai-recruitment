import { Link } from "react-router-dom";
import { ArrowRight, Eye, FileSearch, FileText, HandHeart, Scale, ScrollText, ShieldCheck, Upload, UserCheck } from "lucide-react";
import { Reveal } from "../ui.jsx";

const ETAPES = [
  { Icone: Upload, titre: "Vous déposez votre dossier", texte: "Votre CV, votre diplôme et votre CIN. Le dossier est enregistré et attend, tranquillement.", fait: true, badge: "Disponible" },
  { Icone: UserCheck, titre: "Le recruteur lance l'analyse", texte: "Aucune analyse ne démarre toute seule : elle commence uniquement quand le recruteur clique sur « Lancer le traitement ».", fait: true, badge: "Règle d'or" },
  { Icone: FileSearch, titre: "Agent 1 : il lit l'offre", texte: "Il transforme l'annonce en exigences claires : diplôme, expérience, compétences indispensables et appréciées, langues, missions.", fait: true, badge: "Disponible" },
  { Icone: FileText, titre: "Agent 2 : il lit le CV", texte: "Il en tire un profil structuré : formations, expériences, compétences. Les durées sont calculées par le programme, jamais devinées.", fait: true, badge: "Disponible" },
  { Icone: ShieldCheck, titre: "Agent 3 : il vérifie les documents", texte: "Il compare le diplôme et la CIN avec le CV, et signale les incohérences.", fait: true, badge: "Disponible" }, // ✅ Modifié
  { Icone: Scale, titre: "Agent 4 : il compare et note", texte: "Six critères pondérés donnent un score, avec la justification de chaque point.", fait: true, badge: "Disponible" }, // ✅ Modifié
  { Icone: ScrollText, titre: "Agent 5 : il rédige le rapport", texte: "Points forts, manques, incohérences et conclusion, dans un texte que n'importe qui peut relire.", fait: true, badge: "Disponible" }, // ✅ Modifié
  { Icone: HandHeart, titre: "Une personne décide", texte: "Le score est une aide à la décision. La décision finale de recrutement appartient toujours à un humain.", fait: true, badge: "Toujours" },
];

export default function Comment() {
  return (
    <div className="conteneur">
      <div className="page-titre">
        <h1>Comment votre dossier est lu</h1>
        <p>Huit étapes, dans l'ordre, avec une règle simple : la machine prépare, l'humain décide.</p>
      </div>
      <div className="chemin">
        {ETAPES.map(({ Icone, titre, texte, fait, badge }, i) => (
          <Reveal key={titre} delai={(i % 3) * 0.06} className={"jalon carte" + (fait ? " fait" : "")}>
            <span className="icone-rond" style={{ color: "var(--abricot)" }}><Icone size={22} /></span>
            <div><h3>{titre}</h3><p>{texte}</p></div>
            {/* Le badge "pret" donne la couleur verte */}
            <span className={"badge" + (badge === "Disponible" ? " pret" : "")}>{badge}</span>
          </Reveal>
        ))}
      </div>
      <section className="section">
        <Reveal className="section-tete"><div><h2>Trois promesses</h2><p>Ce qui ne changera pas, quelle que soit la technologie derrière.</p></div></Reveal>
        <Reveal className="engagement">
          <div><span className="icone-rond"><Scale size={22} /></span><h3>Équitable</h3><p>Le score aide à décider. Il ne remplace jamais le regard d'une personne.</p></div>
          <div><span className="icone-rond"><Eye size={22} /></span><h3>Transparent</h3><p>Chaque critère est noté et justifié. Vous savez ce qui a pesé dans le résultat.</p></div>
          <div><span className="icone-rond"><ShieldCheck size={22} /></span><h3>Confidentiel</h3><p>Les documents ne sont accessibles qu'à leur propriétaire et au recruteur. Cette version de démonstration n'utilise que des données fictives.</p></div>
        </Reveal>
        <div style={{ marginTop: 34 }}><Link to="/" className="btn btn-plein">Voir les offres <ArrowRight size={18} /></Link></div>
      </section>
    </div>
  );
}