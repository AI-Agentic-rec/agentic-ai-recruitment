import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    api.get("/auth/me").then((d) => setUser(d.user)).catch(() => setUser(null)).finally(() => setChargement(false));
  }, []);

  const connexion = useCallback(async (email, password) => {
    const d = await api.post("/auth/login", { email, password });
    setUser(d.user); return d.user;
  }, []);
  const inscription = useCallback((champs) => api.post("/auth/register", champs), []);
  const deconnexion = useCallback(async () => { await api.post("/auth/logout"); setUser(null); }, []);

  return <AuthContext.Provider value={{ user, chargement, connexion, inscription, deconnexion }}>{children}</AuthContext.Provider>;
}
