import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { Briefcase, Cpu, Hourglass, LogOut } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar, Marque } from "../ui.jsx";

/* Espace RECRUTEUR (admin) : menu à gauche + pages Offres, Agents IA. */
export default function LayoutAdmin() {
  const { user, deconnexion } = useAuth();
  const nav = useNavigate(), toast = useToast();
  const sortir = async () => { await deconnexion(); toast("À bientôt !"); nav("/"); };
  const classe = ({ isActive }) => (isActive ? "actif" : "");
  return (
    <div className="admin">
      <aside className="menu">
        <Marque />
        <nav aria-label="Espace recruteur">
          <NavLink to="/admin" end className={classe}><Briefcase size={19} />Offres</NavLink>
          <NavLink to="/admin/agents" className={classe}><Cpu size={19} />Agents IA</NavLink>
          <span className="bientot"><Hourglass size={19} />Candidatures<small>bientôt</small></span>
        </nav>
        <div className="moi"><Avatar i={user.id} size={46} /><div><b>{user.prenom} {user.nom}</b><small>Recruteur</small></div></div>
        <Link to="/" className="btn btn-doux btn-petit">Voir le site public</Link>
        <button className="btn btn-doux btn-petit" onClick={sortir}><LogOut size={16} />Se déconnecter</button>
      </aside>
      <section className="panneau"><Outlet /></section>
    </div>
  );
}
