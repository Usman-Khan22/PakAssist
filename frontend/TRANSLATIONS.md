All authored English and Urdu copy belongs in [src/translations.ts](src/translations.ts). Each entry must include both `en` and `ur`; TypeScript checks this shape.

Use reactive translations in components:

```tsx
const { t, language, localize } = useLanguage();
<h2>{t.popularGovernmentDirectories}</h2>
<h3>{localize(service.title[language])}</h3>
```

Store dynamic display values as `LocalizedText` objects referencing `copy`. Select the language when rendering, rather than storing translated strings in component state. Keep slugs, category identifiers, status identifiers, URLs and React keys stable across language changes. User-entered chat text stays as entered.

`localize` and `t` isolate Latin fragments in Urdu prose. Use `ltr-isolate` for standalone official domains and branding. Interpolate templates before calling `localize`, so bidirectional controls do not interfere with placeholders.

Language state lives in [src/language.ts](src/language.ts), updates React subscribers, persists when storage is available, and sets the document language, direction and title. It never rewrites DOM text. The mock API retains its English response format; page components consume bilingual service data directly.

Run `npm run build` and `npm run test:language`. The browser check starts its own local Vite server and uses installed Microsoft Edge by default. Set `PLAYWRIGHT_CHANNEL=chrome` to use installed Chrome, or `TEST_BASE_URL` to test an already running frontend. It checks all routes in both languages, repeated switches, dynamic states, Urdu search, checklist state, chat, persistence and mobile rendering. Screenshots are saved under the ignored `.verification/screenshots` directory.
