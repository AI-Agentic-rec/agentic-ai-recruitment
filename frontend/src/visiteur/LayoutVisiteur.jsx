import { Outlet, useLocation } from "react-router-dom";
import Dock from "../commun/Dock.jsx";
import { Marque } from "../ui.jsx";

/* Espace VISITEUR (site public) : accueil, détail d'une offre, comment ça marche. */
export default function LayoutVisiteur() {
  const { pathname } = useLocation();
  return (
    <>
      <Dock />
      <div className="page">
        {pathname !== "/" && <div className="conteneur" style={{ padding: "6px 8px 26px" }}><Marque /></div>}
        <main><Outlet /></main>
        <footer className="pied">
          <Marque />
          <p>Des offres claires, une analyse expliquée, une décision toujours humaine.</p>
        </footer>
      </div>
    </>
  );
}
