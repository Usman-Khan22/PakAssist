# PakAssist

PakAssist is a React and TypeScript civic-tech guide for navigating common Pakistani government services. It presents service requirements, documents, fees, timelines, and next steps in a clear interface with English and Urdu support.

PakAssist is an independent guide, not a government portal. Users should verify final requirements, fees, and application details on the relevant official `.gov.pk` website.

## Features

- Home page with service search, popular government directories, process guidance, and official gateway links
- Searchable government services directory with category filters
- Detail pages with eligibility checklists, required documents, fees, timelines, process steps, and related services
- Mock PakAssist chat experience with follow-up prompts
- Mock dashboard showing applications, appointments, and quick actions
- English and Urdu language switching
- Responsive desktop and mobile layouts
- Lucide icons and React Router navigation

## Technology

- React
- TypeScript
- Vite
- React Router
- Lucide React
- CSS

## Requirements

- Node.js 18 or newer
- npm

## Getting Started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Start the development server:

   ```bash
   npm run dev
   ```

3. Open the local URL shown by Vite, usually `http://localhost:5173`.

## Available Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Run TypeScript checks and create a production build |
| `npm run preview` | Preview the production build locally |

## Routes

| Path | Page |
| --- | --- |
| `/` | Home |
| `/services` | Government services directory |
| `/services/:slug` | Service detail page |
| `/chat` | PakAssist chat |
| `/dashboard` | User dashboard |
| `/how-it-works` | How PakAssist works |
| `/about` | About PakAssist |

## Project Structure

```text
.
├── index.html
├── package.json
├── package-lock.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
└── src
    ├── App.tsx              # Routes and page components
    ├── data.ts              # Service catalog and service types
    ├── language.ts          # English/Urdu language handling
    ├── main.tsx             # React application entry point
    ├── styles.css           # Global responsive styles
    ├── vite-env.d.ts        # Vite type declarations
    └── services
        └── api.ts           # Local mock service helpers
```

## Data and Integrations

The current application uses local mock data. The functions in `src/services/api.ts` are prepared as a simple boundary for replacing mock service, chat, and dashboard behavior with a real backend later.

## Disclaimer

Information shown by PakAssist is for guidance only. Always confirm current requirements and complete applications through official government channels.
