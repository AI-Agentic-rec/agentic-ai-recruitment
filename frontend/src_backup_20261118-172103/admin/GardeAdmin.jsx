import { Link, Navigate } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { useAuth } from "../auth.jsx";

/* Réserve l'espace recruteur aux administrateurs. */
export default function GardeAdmin({ children }) {
  const { user, chargement } = useAuth();
  if (chargement) return <div className="conteneur" style={{ paddingTop: 140, display: "grid", placeItems: "center" }}><div className="rond" /></div>;
  if (!user) return <Navigate to="/connexion" replace />;
  if (user.role !== "admin") return (
    <div className="conteneur" style={{ padding: "140px 24px", textAlign: "center", display: "grid", gap: 16, justifyItems: "center" }}>
      <span className="icone-rond" style={{ width: 64, height: 64, color: "var(--alerte)" }}><ShieldAlert size={28} /></span>
      <h1 style={{ fontSize: "2.6rem" }}>Cet espace est réservé aux recruteurs</h1>
      <p style={{ color: "var(--doux)", maxWidth: 440 }}>Votre compte est un compte candidat. Vous pouvez parcourir les offres et suivre vos candidatures.</p>
      <Link className="btn btn-plein" to="/">Voir les offres</Link>
    </div>
  );
  return children;
}
