import { createContext, useCallback, useContext, useState } from "react";
import { Check, TriangleAlert } from "lucide-react";

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }) {
  const [msg, setMsg] = useState(null);
  const afficher = useCallback((texte, type = "ok") => {
    const id = Date.now(); setMsg({ texte, type, id });
    setTimeout(() => setMsg((m) => (m && m.id === id ? null : m)), 3800);
  }, []);
  return (
    <ToastContext.Provider value={afficher}>
      {children}
      {msg && (
        <div className={"toast " + msg.type} role="status" key={msg.id}>
          {msg.type === "ok" ? <Check size={18} /> : <TriangleAlert size={18} />}
          <span>{msg.texte}</span>
        </div>
      )}
    </ToastContext.Provider>
  );
}
