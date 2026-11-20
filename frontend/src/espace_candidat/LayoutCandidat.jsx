import { Outlet } from "react-router-dom";
import Dock from "../commun/Dock.jsx";
import { Marque } from "../ui.jsx";

/* Espace CANDIDAT : mon compte et mes candidatures. */
export default function LayoutCandidat() {
  return (
    <>
      <Dock />
      <div className="page">
        <div className="conteneur" style={{ padding: "6px 8px 26px" }}><Marque /></div>
        <main><Outlet /></main>
      </div>
    </>
  );
}
