import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import { Avatar, Marque } from "../ui.jsx";
import { ScenePrincipale } from "../scene.jsx";

function Cote({ titre, texte }) {
  return (
    <aside className="auth-art">
      <ScenePrincipale />
      <Marque />
      <h1 className="titre">{titre}</h1>
      <div className="carte-parole givre">
        <span className="visages" aria-hidden="true">{[0, 1, 2].map((i) => <Avatar key={i} i={i + 2} variante={i} size={44} />)}</span>
        <span>{texte}</span>
      </div>
    </aside>
  );
}

export function Connexion() {
  const { user, connexion } = useAuth();
  const [email, setEmail] = useState(""), [mdp, setMdp] = useState("");
  const [erreur, setErreur] = useState(""), [envoi, setEnvoi] = useState(false);
  const nav = useNavigate(), toast = useToast();
  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/"} replace />;
  const envoyer = async (e) => {
    e.preventDefault(); setErreur(""); setEnvoi(true);
    try { const u = await connexion(email, mdp); toast(`Bienvenue ${u.prenom} !`); nav(u.role === "admin" ? "/admin" : "/"); }
    catch (err) { setErreur(err.message); } finally { setEnvoi(false); }
  };
  return (
    <div className="auth">
      <Cote titre="Content de vous revoir." texte="Retrouvez vos candidatures, vos résultats et les nouvelles offres." />
      <div className="auth-form">
        <div className="carte-auth carte">
          <h2>Connexion</h2>
          <p>Entrez vos identifiants pour continuer.</p>
          <form className="formulaire" onSubmit={envoyer}>
            {erreur && <div className="alerte" role="alert">{erreur}</div>}
            <label className="champ">Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus autoComplete="email" /></label>
            <label className="champ">Mot de passe<input type="password" value={mdp} onChange={(e) => setMdp(e.target.value)} required autoComplete="current-password" /></label>
            <button className="btn btn-plein btn-large" disabled={envoi}>{envoi ? "Connexion…" : "Se connecter"}</button>
          </form>
          <p className="pied-auth">Pas encore de compte ? <Link to="/inscription">Créer un compte</Link></p>
        </div>
      </div>
    </div>
  );
}

export function Inscription() {
  const { user, inscription } = useAuth();
  const [f, setF] = useState({ prenom: "", nom: "", email: "", telephone: "", password: "" });
  const [erreur, setErreur] = useState(""), [envoi, setEnvoi] = useState(false);
  const nav = useNavigate(), toast = useToast();
  if (user) return <Navigate to="/" replace />;
  const maj = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const envoyer = async (e) => {
    e.preventDefault(); setErreur(""); setEnvoi(true);
    try { await inscription(f); toast("Compte créé. Vous pouvez vous connecter."); nav("/connexion"); }
    catch (err) { setErreur(err.message); } finally { setEnvoi(false); }
  };
  return (
    <div className="auth">
      <Cote titre="Votre prochain poste commence ici." texte="Un compte, un profil, et vous suivez chaque candidature du dépôt jusqu'au résultat." />
      <div className="auth-form">
        <div className="carte-auth carte">
          <h2>Créer un compte</h2>
          <p>Moins d'une minute, sans engagement.</p>
          <form className="formulaire" onSubmit={envoyer}>
            {erreur && <div className="alerte" role="alert">{erreur}</div>}
            <div className="deux">
              <label className="champ">Prénom<input value={f.prenom} onChange={maj("prenom")} required autoComplete="given-name" /></label>
              <label className="champ">Nom<input value={f.nom} onChange={maj("nom")} required autoComplete="family-name" /></label>
            </div>
            <label className="champ">Email<input type="email" value={f.email} onChange={maj("email")} required autoComplete="email" /></label>
            <label className="champ">Téléphone <small>facultatif</small><input value={f.telephone} onChange={maj("telephone")} autoComplete="tel" /></label>
            <label className="champ">Mot de passe <small>8 caractères minimum</small><input type="password" value={f.password} onChange={maj("password")} minLength={8} required autoComplete="new-password" /></label>
            <button className="btn btn-plein btn-large" disabled={envoi}>{envoi ? "Création…" : "Créer mon compte"}</button>
          </form>
          <p className="pied-auth">Déjà inscrit ? <Link to="/connexion">Se connecter</Link></p>
        </div>
      </div>
    </div>
  );
}
