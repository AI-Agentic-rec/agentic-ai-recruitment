import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [chargement, setChargement] = useState(true);

  // Au démarrage : ne recharge /me QUE si un user_id existe
  useEffect(() => {
    const id = localStorage.getItem("user_id");
    if (!id) {
      setChargement(false);
      return;
    }
    api.get("/auth/me")
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem("user_id");
        localStorage.removeItem("role");
        setUser(null);
      })
      .finally(() => setChargement(false));
  }, []);

  const connexion = useCallback(async (email, password) => {
    const d = await api.post("/auth/login", { email, password });
    localStorage.setItem("user_id", d.user.id);
    localStorage.setItem("role", d.user.role);
    setUser(d.user);
    return d.user;
  }, []);

  const inscription = useCallback((champs) => api.post("/auth/register", champs), []);

  const deconnexion = useCallback(async () => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("role");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, chargement, connexion, inscription, deconnexion, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}