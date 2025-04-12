"use client"

import { Fragment, useState } from 'react'
import { Terminal, ChevronDown } from 'lucide-react'

interface LanguageOption {
  code: string;
  name: string;
  flag: string;
}

const languages: LanguageOption[] = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
  { code: 'ta', name: 'தமிழ்', flag: '🇮🇳' },
  { code: 'te', name: 'తెలుగు', flag: '🇮🇳' },
  { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳' },
  { code: 'mr', name: 'मराठी', flag: '🇮🇳' }
];

export default function ChatHeader() {
  const [language, setLanguage] = useState<LanguageOption>(languages[0]);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLanguageChange = (lang: LanguageOption) => {
    setLanguage(lang);
    setDropdownOpen(false);
    // Here you would typically emit an event or use context to notify other components
    // about the language change
    window.dispatchEvent(new CustomEvent('language-change', { detail: lang.code }));
  };

  return (
    <div className="flex items-center gap-2 border-b border-white/10 bg-black/50 px-4 py-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-600/20">
        <Terminal size={18} className="text-purple-400" />
      </div>
      <h1 className="text-lg font-medium text-white">Your AI Agent</h1>
      <div className="ml-auto flex items-center">
        <div className="h-2 w-2 rounded-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
        <span className="ml-2 text-xs text-green-400">Online</span>
      </div>
      <div className="relative">
        <button 
          className="flex items-center space-x-1 text-white text-sm bg-gray-800/50 hover:bg-gray-700/50 px-2 py-1 rounded-md"
          onClick={() => setDropdownOpen(!dropdownOpen)}
        >
          <span className="mr-1">{language.flag}</span>
          <span>{language.name}</span>
          <ChevronDown size={16} />
        </button>
        
        {dropdownOpen && (
          <div className="absolute right-0 mt-2 w-40 rounded-md shadow-lg bg-black/80 backdrop-blur-xl border border-white/10 z-50">
            <div className="py-1">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  className="flex items-center w-full px-4 py-2 text-sm text-white hover:bg-white/10"
                  onClick={() => handleLanguageChange(lang)}
                >
                  <span className="mr-2">{lang.flag}</span>
                  <span>{lang.name}</span>
                  {lang.code === language.code && (
                    <span className="ml-auto">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

