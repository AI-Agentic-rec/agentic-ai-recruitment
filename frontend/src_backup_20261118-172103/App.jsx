import { Navigate, Route, Routes } from "react-router-dom";
import { Fond, RetourEnHaut } from "./commun/Fond.jsx";
import { Connexion, Inscription } from "./commun/Auth.jsx";
// espace visiteur
import LayoutVisiteur from "./visiteur/LayoutVisiteur.jsx";
import Home from "./visiteur/Home.jsx";
import OffreDetail from "./visiteur/OffreDetail.jsx";
import Comment from "./visiteur/Comment.jsx";
import NotFound from "./visiteur/NotFound.jsx";
// espace candidat
import GardeCandidat from "./candidat/GardeCandidat.jsx";
import LayoutCandidat from "./candidat/LayoutCandidat.jsx";
import MonEspace from "./candidat/MonEspace.jsx";
// espace admin
import GardeAdmin from "./admin/GardeAdmin.jsx";
import LayoutAdmin from "./admin/LayoutAdmin.jsx";
import AdminOffres from "./admin/AdminOffres.jsx";
import OffreForm from "./admin/OffreForm.jsx";
import AgentsLab from "./admin/AgentsLab.jsx";

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
          <Route path="offres/:id" element={<OffreDetail />} />
          <Route path="comment-ca-marche" element={<Comment />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* espace candidat */}
        <Route path="candidat" element={<GardeCandidat><LayoutCandidat /></GardeCandidat>}>
          <Route index element={<MonEspace />} />
          <Route path="*" element={<Navigate to="/candidat" replace />} />
        </Route>

        {/* espace admin / recruteur */}
        <Route path="admin" element={<GardeAdmin><LayoutAdmin /></GardeAdmin>}>
          <Route index element={<AdminOffres />} />
          <Route path="offres/nouvelle" element={<OffreForm />} />
          <Route path="offres/:id/modifier" element={<OffreForm />} />
          <Route path="agents" element={<AgentsLab />} />
        </Route>
      </Routes>
    </>
  );
}
