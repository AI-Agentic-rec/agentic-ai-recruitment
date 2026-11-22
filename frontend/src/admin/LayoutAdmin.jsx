import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Briefcase, Users, LogOut } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar, Marque } from "../ui.jsx";
import LangueSwitch from "../commun/LangueSwitch.jsx"; // ✅ Assure-toi d'avoir le switch ici aussi


export default function LayoutAdmin() {
  const { user, deconnexion } = useAuth();
  const nav = useNavigate(), toast = useToast();

  const sortir = async () => {
    await deconnexion();
    toast("À bientôt !");
    nav("/");
  };

  const classe = ({ isActive }) => (isActive ? "actif" : "");

  return (
    <div className="admin">
      <aside className="menu">
        <Marque />
        <nav aria-label="Espace recruteur">
          {/* ✅ Nouveau menu */}
          <NavLink to="/admin" end className={classe}>
            <LayoutDashboard size={19} />Tableau de bord
          </NavLink>
          <NavLink to="/admin/offers" className={classe}>
            <Briefcase size={19} />Offres
          </NavLink>
          <NavLink to="/admin/candidatures" className={classe}>
            <Users size={19} />Candidatures
          </NavLink>
        </nav>

        <div className="moi">
          <Avatar i={user.id} size={46} />
          <div>
            <b>{user.prenom} {user.nom}</b>
            <small>Recruteur</small>
          </div>
        </div>

        <LangueSwitch /> {/* ✅ Bouton de langue dans l'admin */}

        <Link to="/" className="btn btn-doux btn-petit">Voir le site public</Link>
        <button className="btn btn-doux btn-petit" onClick={sortir}>
          <LogOut size={16} />Se déconnecter
        </button>
      </aside>

      <section className="panneau">
        <Outlet />
      </section>
    </div>
  );
}