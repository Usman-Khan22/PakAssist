# Service Center Datasets

Structured (JSON) datasets of physical offices where citizens go to complete
passport and driving license services. These are meant to be loaded
programmatically later — e.g. by an "action" agent that needs to tell a user
their nearest office, or by the appointment-slot simulator (next deliverable),
which will reference `office_name` values from these files.

## Files

### `passport_service_centers.json`
- **180 offices**, covering Islamabad, all Punjab/KP/Sindh/Balochistan
  districts, Gilgit-Baltistan, Azad Jammu & Kashmir, and FATA.
- Source: the official DGI&P office list PDF —
  https://dgip.gov.pk/downloads/PassportOfficesListNew.pdf
- **Confidence: High.** This is a direct, single-source government document,
  machine-parsed into JSON. A few caveats:
  - A handful of phone numbers in the source PDF were formatted inconsistently
    (e.g., missing area code separators). Where a number looked unreliable
    it was normalized but not invented — if in doubt, treat the phone field
    as "needs confirmation" rather than dial-and-trust.
  - Karachi-II (Central), Karachi-III (West), and Karachi-IV (East) had no
    address text in the source PDF extract — their `address` field is
    marked `"Not listed in official PDF extract"` rather than guessed.
  - Worldwide missions (for overseas Pakistanis) were listed in the original
    PDF too but are **not** included in this dataset since the current
    project scope (per `PROJECT_CONTEXT.md`) is domestic services — flag if
    that scope changes.

### `driving_license_service_centers.json`
- **6 records** — this is intentionally a starter dataset, not a complete
  one, because there is no single official, scrapable list of driving
  license branches for most provinces (see `driving_license.md`'s "Open
  Research Items").
- Each record has a `confidence` field:
  - **High** — Islamabad ITP and 2 Punjab offices (Attock, Bhakkar),
    confirmed directly from official government sites.
  - **Medium** — Sindh, described at the department/process level; branch
    addresses not yet independently confirmed.
  - **Low** — KP and Balochistan, department contact only; portal details
    unconfirmed.
- **To extend Punjab further:** the full official list lives at
  `https://trafficpolice.punjab.gov.pk/licensing_offices`, but that site
  blocks automated fetching (robots.txt). A team member should open it in
  a browser and copy the per-district entries by hand, or request the data
  directly from Traffic Police Punjab.
- **Do not** pull driving-license office addresses from third-party sites
  like `dlims-punjab.com.pk`, `dlims.org.pk`, or similar look-alike domains
  found during research — they are not on the `.gov.pk` domain, their data
  conflicts with official sources, and a couple of them visually mimic the
  real DLIMS branding closely enough to be worth flagging to the team as a
  possible phishing/scam risk worth a heads-up to users, not just a data
  quality issue.

## Schema

Both files are JSON arrays of flat objects. Common fields:

| Field | Meaning |
|---|---|
| `region` / `province` | Administrative region the office is in |
| `office_name` | Name/label of the office |
| `address` | Street address as listed by the source |
| `phone` | Contact number, if published (`null` if not available) |
| `service` / `services` | What the office handles |
| `required_docs` | (driving license only) documents needed at that office |
| `portal` | Related online portal, if any |
| `confidence` | High / Medium / Low — see notes above |
| `source` | Where this record's data came from |

## Suggested Next Steps

1. Fill the `Low`-confidence driving license gaps (KP, Balochistan) with a
   direct phone/email inquiry to the relevant departments, not further web
   scraping — public info here is thin and unreliable.
2. Add a `lat`/`lng` field once the team decides whether the agent will need
   map/distance features (not in current project scope per
   `PROJECT_CONTEXT.md` — confirm before building this out).
3. Keep this dataset and `knowledge_base/sources.md` in sync — if an address
   changes, update both.
