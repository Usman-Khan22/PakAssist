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
- **15 records** — grown from an original starter set of 6, now covering
  Islamabad, Lahore, Rawalpindi, Faisalabad, Multan, Gujranwala, Attock,
  and Bhakkar in Punjab; two Karachi branches in Sindh; Peshawar in KP;
  and Quetta in Balochistan. Still not a complete national list — most
  smaller districts remain uncovered (see `driving_license.md`'s "Open
  Research Items").
- Confidence breakdown in the current file:
  - **High** — Islamabad (ITP), Lahore Manawan, Rawalpindi, Attock, Bhakkar:
    confirmed directly on official `.gov.pk`/`.gop.pk` government sites.
  - **Medium-High** — Karachi Clifton & Nazimabad branches: sourced from
    `dls.gos.pk`, a provincial-government-linked domain, not yet
    cross-verified against `sindhpolice.gov.pk` directly.
  - **Medium** — Faisalabad, Multan, Gujranwala, Peshawar: sourced from a
    mix of a `kp.gov.pk` page (Peshawar) and an unofficial directory site
    reproducing what claims to be Traffic Police Punjab contact info
    (the other three) — treat as needing confirmation before being quoted
    to a user as fact.
  - **Low-Medium** — Quetta: phone numbers only, sourced from a third-party
    business directory, no confirmed street address.
- **To extend Punjab further:** the full official list lives at
  `https://trafficpolice.punjab.gov.pk/licensing_offices` and
  `https://ctplahore.gop.pk/license-centers` for Lahore's smaller booths,
  but both block automated fetching (robots.txt). A team member should open
  them in a browser and copy the remaining district/booth entries by hand.
- **Do not** pull driving-license office addresses from third-party sites
  like `dlims-punjab.com.pk`, `dlims.org.pk`, or similar look-alike domains
  found during research — they are not on the `.gov.pk` domain, their data
  conflicts with official sources, and a couple of them visually mimic the
  real DLIMS branding closely enough to be worth flagging to the team as a
  possible phishing/scam risk, not just a data quality issue. A new one
  surfaced in this update too: `transport.kpdata.gov.pk.onl`, which stuffs
  "gov.pk" into a `.onl` domain to look official — it is not a real
  government address and should never be linked to a user.

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
