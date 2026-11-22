import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

export default function LangueSwitch() {
  const { i18n } = useTranslation();

  const changerLangue = () => {
    const nouvelleLangue = i18n.language === 'fr' ? 'en' : 'fr';
    i18n.changeLanguage(nouvelleLangue);
    localStorage.setItem("langue", nouvelleLangue); // Sauvegarde le choix
  };

  return (
    <button 
      onClick={changerLangue} 
      className="btn btn-carte btn-petit" 
      style={{ display: 'flex', alignItems: 'center', gap: 6 }}
      title="Changer de langue"
    >
      <Globe size={16} /> 
      {i18n.language.toUpperCase()}
    </button>
  );
}