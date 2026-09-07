import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { applyLanguage, getStoredLanguage } from './language';

import './styles/tokens.css';
import './styles/globals.css';
import './styles/components.css';
import './styles/header.css';
import './styles/buttons.css';
import './styles/search.css';
import './styles/typography.css';
import './styles/rtl.css';
applyLanguage(getStoredLanguage());
createRoot(document.getElementById('root')!).render(<StrictMode><BrowserRouter><App /></BrowserRouter></StrictMode>);
