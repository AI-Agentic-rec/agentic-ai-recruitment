import { Link } from "react-router-dom";
import { Hourglass } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { Avatar, Reveal } from "../ui.jsx";

export default function MonEspace() {
  const { user } = useAuth();
  return (
    <div className="conteneur" style={{ display: "grid", gap: 24, paddingBottom: 80 }}>
      <Reveal className="carte" style={{ display: "flex", alignItems: "center", gap: 20, padding: 28 }}>
        <Avatar i={user.id} size={72} />
        <div>
          <h1 style={{ fontSize: "2.2rem" }}>Bonjour {user.prenom} !</h1>
          <p style={{ color: "var(--doux)" }}>{user.prenom} {user.nom} · {user.email}</p>
        </div>
      </Reveal>
      <Reveal className="carte" delai={0.1} style={{ display: "grid", gap: 12, padding: 28, justifyItems: "start" }}>
        <span className="icone-rond"><Hourglass size={22} /></span>
        <h2>Mes candidatures</h2>
        <p style={{ color: "var(--doux)", maxWidth: 520 }}>Le dépôt de candidature et le suivi des résultats arrivent bientôt. En attendant, parcourez les offres ouvertes.</p>
        <Link className="btn btn-plein" to="/#offres">Voir les offres</Link>
      </Reveal>
    </div>
  );
}
