// Petit client pour l'API FastAPI. Le cookie de connexion (HttpOnly) est envoyé automatiquement.
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
  const options = { method, credentials: "same-origin", headers: {} };
  if (formData) options.body = formData;
  else if (body !== undefined) { options.headers["Content-Type"] = "application/json"; options.body = JSON.stringify(body); }
  let res;
  try { res = await fetch("/api" + chemin, options); }
  catch { throw new ApiError(0, "Le serveur ne répond pas. Vérifiez qu'il est bien lancé (4_lancer_site.bat)."); }
  let data = null;
  try { data = await res.json(); } catch { /* réponse sans contenu */ }
  if (!res.ok) throw new ApiError(res.status, messageDe(data) || "Une erreur est survenue. Réessayez dans un instant.");
  return data;
}

export const api = {
  get: (p) => requete(p),
  post: (p, body) => requete(p, { method: "POST", body }),
  put: (p, body) => requete(p, { method: "PUT", body }),
  del: (p) => requete(p, { method: "DELETE" }),
  upload: (p, formData) => requete(p, { method: "POST", formData }),
};
