import { Navigate, Route, Routes } from "react-router-dom";
import { Fond, RetourEnHaut } from "./commun/Fond.jsx";
import { Connexion, Inscription } from "./commun/Auth.jsx";
// espace visiteur
import LayoutVisiteur from "./visiteur/LayoutVisiteur.jsx";
import Home from "./visiteur/Home.jsx";
import OffreDetail from "./visiteur/OffreDetail.jsx";
import NotFound from "./visiteur/NotFound.jsx";
// espace candidat
import GardeCandidat from "./candidat/GardeCandidat.jsx";
import LayoutCandidat from "./candidat/LayoutCandidat.jsx";
import MonEspace from "./candidat/MonEspace.jsx";
import Postuler from "./candidat/Postuler.jsx";
// espace admin
import GardeAdmin from "./admin/GardeAdmin.jsx";
import LayoutAdmin from "./admin/LayoutAdmin.jsx";
import AdminDashboard from "./admin/AdminDashboard.jsx"; // ✅ NOUVEL IMPORT (Remplace AgentsLab)
import AdminOffres from "./admin/AdminOffres.jsx";
import OffreForm from "./admin/OffreForm.jsx";
import AdminCandidatures from "./admin/AdminCandidatures.jsx";

export default function App() {
  return (
    <>
      <Fond />
      <RetourEnHaut />
      <Routes>
        {/* connexion / inscription : communes aux trois espaces */}
        <Route path="connexion" element={<Connexion />} />
        <Route path="inscription" element={<Inscription />} />

        {/* espace visiteur : site public */}
        <Route element={<LayoutVisiteur />}>
          <Route index element={<Home />} />
          <Route path="offers/:id" element={<OffreDetail />} />
          <Route path="offers/:id/postuler" element={<GardeCandidat><Postuler /></GardeCandidat>} />
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* espace candidat */}
        <Route path="candidat" element={<GardeCandidat><LayoutCandidat /></GardeCandidat>}>
          <Route index element={<MonEspace />} />
          <Route path="*" element={<Navigate to="/candidat" replace />} />
        </Route>

        {/* espace admin / recruteur */}
        <Route path="admin" element={<GardeAdmin><LayoutAdmin /></GardeAdmin>}>
          {/* ✅ La page d'accueil de l'admin est maintenant le Tableau de bord */}
          <Route index element={<AdminDashboard />} />
          
          {/* ✅ Routes pour les offres */}
          <Route path="offers" element={<AdminOffres />} />
          <Route path="offers/nouvelle" element={<OffreForm />} />
          <Route path="offers/:id/modifier" element={<OffreForm />} />
          
          {/* ✅ Route pour les candidatures */}
          <Route path="candidatures" element={<AdminCandidatures />} />
        </Route>
      </Routes>
    </>
  );
}