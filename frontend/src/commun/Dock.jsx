import { Link, NavLink, useNavigate } from "react-router-dom";
import { Briefcase, House, LayoutDashboard, LogIn, LogOut, UserPlus, UserRound } from "lucide-react";
import { useTranslation } from "react-i18next"; // ✅ IMPORT
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar } from "../ui.jsx";
import LangueSwitch from "./LangueSwitch.jsx"; // ✅ IMPORT

export default function Dock() {
  const { user, deconnexion } = useAuth();
  const { t } = useTranslation(); // ✅ HOOK DE TRADUCTION
  const toast = useToast(), nav = useNavigate();
  
  const sortir = async () => { await deconnexion(); toast("À bientôt !"); nav("/"); };
  const cl = ({ isActive }) => (isActive ? "actif" : "");

  return (
    <nav className="dock givre" aria-label="Navigation principale">
      <NavLink to="/" end className={cl} data-etiquette={t('nav.home')}><House size={22} /></NavLink>
      <Link to={{ pathname: "/", hash: "#offres" }} data-etiquette={t('nav.offers')}><Briefcase size={22} /></Link>
      
      <span className="sep" />
      
      {/* ✅ BOUTON DE CHANGEMENT DE LANGUE */}
      <LangueSwitch />

      {user ? (
        <>
          {user.role === "admin" && <NavLink to="/admin" className={cl} data-etiquette={t('nav.admin_space')}><LayoutDashboard size={22} /></NavLink>}
          {user.role === "candidat" && <NavLink to="/candidat" className={cl} data-etiquette={t('nav.my_space')}><UserRound size={22} /></NavLink>}
          <span data-etiquette={`${user.prenom} ${user.nom}`}><Avatar i={user.id} size={40} /></span>
          <button onClick={sortir} data-etiquette={t('nav.logout')} aria-label={t('nav.logout')}><LogOut size={21} /></button>
        </>
      ) : (
        <>
          <NavLink to="/connexion" className={cl} data-etiquette={t('nav.login')}><LogIn size={22} /></NavLink>
          <NavLink to="/inscription" className={cl} data-etiquette={t('nav.register')}><UserPlus size={22} /></NavLink>
        </>
      )}
    </nav>
  );
}