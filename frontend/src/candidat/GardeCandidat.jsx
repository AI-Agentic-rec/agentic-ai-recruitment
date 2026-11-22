import { Navigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

/* Réserve l'espace candidat aux candidats connectés (un recruteur est renvoyé vers son espace). */
export default function GardeCandidat({ children }) {
  const { user, chargement } = useAuth();
  if (chargement) return <div className="conteneur" style={{ paddingTop: 140, display: "grid", placeItems: "center" }}><div className="rond" /></div>;
  if (!user) return <Navigate to="/connexion" replace />;
  if (user.role === "admin") return <Navigate to="/admin" replace />;
  return children;
}
