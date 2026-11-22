import { Link, NavLink, useNavigate } from "react-router-dom";
import { Briefcase, Compass, House, LayoutDashboard, LogIn, LogOut, UserPlus, UserRound } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar } from "../ui.jsx";

/* Menu vertical (en bas sur téléphone). Il s'adapte à la personne connectée : visiteur, candidat ou recruteur. */
export default function Dock() {
  const { user, deconnexion } = useAuth();
  const toast = useToast(), nav = useNavigate();
  const sortir = async () => { await deconnexion(); toast("À bientôt !"); nav("/"); };
  const cl = ({ isActive }) => (isActive ? "actif" : "");
  return (
    <nav className="dock givre" aria-label="Navigation principale">
      <NavLink to="/" end className={cl} data-etiquette="Accueil"><House size={22} /></NavLink>
      <Link to={{ pathname: "/", hash: "#offres" }} data-etiquette="Les offres"><Briefcase size={22} /></Link>
      <NavLink to="/comment-ca-marche" className={cl} data-etiquette="Comment ça marche"><Compass size={22} /></NavLink>
      <span className="sep" />
      {user ? (
        <>
          {user.role === "admin" && <NavLink to="/admin" className={cl} data-etiquette="Espace recruteur"><LayoutDashboard size={22} /></NavLink>}
          {user.role === "candidat" && <NavLink to="/candidat" className={cl} data-etiquette="Mon espace"><UserRound size={22} /></NavLink>}
          <span data-etiquette={`${user.prenom} ${user.nom}`}><Avatar i={user.id} size={40} /></span>
          <button onClick={sortir} data-etiquette="Se déconnecter" aria-label="Se déconnecter"><LogOut size={21} /></button>
        </>
      ) : (
        <>
          <NavLink to="/connexion" className={cl} data-etiquette="Se connecter"><LogIn size={22} /></NavLink>
          <NavLink to="/inscription" className={cl} data-etiquette="Créer un compte"><UserPlus size={22} /></NavLink>
        </>
      )}
    </nav>
  );
}
