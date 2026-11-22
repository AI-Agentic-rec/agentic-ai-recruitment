import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="conteneur" style={{ padding: "130px 24px", textAlign: "center", display: "grid", gap: 16, justifyItems: "center" }}>
      <p style={{ fontFamily: "var(--display)", fontSize: "clamp(6rem, 20vw, 11rem)", lineHeight: 0.9, color: "var(--ciel)", fontWeight: 500 }}>404</p>
      <h1 style={{ fontSize: "2.4rem" }}>Cette page s'est égarée</h1>
      <p style={{ color: "var(--doux)", maxWidth: 420 }}>L'adresse demandée n'existe pas. Revenez aux offres ouvertes.</p>
      <Link to="/" className="btn btn-plein">Voir les offres</Link>
    </div>
  );
}
