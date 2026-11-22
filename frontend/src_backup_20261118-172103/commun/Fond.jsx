import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { FondPage } from "../scene.jsx";

export const Fond = FondPage;

export function RetourEnHaut() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) { setTimeout(() => document.querySelector(hash)?.scrollIntoView({ behavior: "smooth" }), 80); } else window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}
