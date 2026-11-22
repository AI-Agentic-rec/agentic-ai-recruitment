// Petit client pour l'API FastAPI.
// Envoie automatiquement X-User-Id (session simplifiée) à chaque requête.

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function messageDe(data) {
  if (!data) return null;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return "Vérifiez les champs du formulaire : certaines informations sont manquantes ou invalides.";
  return null;
}

async function requete(chemin, { method = "GET", body, formData } = {}) {
  const userId = localStorage.getItem("user_id");

  const options = {
    method,
    headers: {
      ...(userId ? { "X-User-Id": userId } : {}),
    },
  };

  if (formData) {
    options.body = formData;                          // pas de Content-Type : le navigateur le gère
  } else if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(BASE_URL + chemin, options);
  } catch {
    throw new ApiError(0, "Le serveur ne répond pas. Vérifiez qu'il est bien lancé.");
  }

  let data = null;
  try { data = await res.json(); } catch { /* réponse sans contenu (204) */ }

  if (!res.ok) throw new ApiError(res.status, messageDe(data) || "Une erreur est survenue. Réessayez dans un instant.");
  return data;
}

export const api = {
  get:    (p)       => requete(p),
  post:   (p, body) => requete(p, { method: "POST",   body }),
  put:    (p, body) => requete(p, { method: "PUT",    body }),
  patch:  (p, body) => requete(p, { method: "PATCH",  body }),   // ← nouveau
  del:    (p)       => requete(p, { method: "DELETE" }),
  delete: (p)       => requete(p, { method: "DELETE" }),         // alias pour compat
  upload: (p, formData) => requete(p, { method: "POST", formData }),
};