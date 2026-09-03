# Knowledge Base: Driving License in Pakistan

## Metadata
- **Service category:** Transport / Licensing
- **Issuing authority:** There is **no single national authority**. Driving licenses are issued provincially/territorially:
  - Punjab: Punjab Traffic Police, via DLIMS (Driving License Issuance & Management System)
  - Sindh: Sindh Police, via DLS Online (Driving Licensing System)
  - Khyber Pakhtunkhwa (KP): KP Excise, Taxation & Transport Department
  - Islamabad Capital Territory (ICT): Islamabad Traffic Police (ITP)
  - Balochistan: Balochistan Excise & Taxation Department
- **Official portals found:**
  - Punjab: https://dlims.punjab.gov.pk (also referenced as dlims-punjab.com.pk on some government-linked pages — verify the `.gov.pk` domain is used before sharing with a user)
  - Sindh: https://dlsonline.sindhpolice.gov.pk and https://dls.gos.pk
  - Islamabad: https://islamabadpolice.gov.pk/itp (portal also referred to as dlims.islamabadpolice.gov.pk)
  - KP: managed by the KP Excise, Taxation & Transport Department; a newer digital system named "DASTAK" has been reported as of 2026 — **needs direct verification with the KP department before publishing as fact**
  - Balochistan: managed by the provincial Excise & Taxation Department; no single dedicated online portal was confirmed during this research pass
- **Last verified by research team:** 2026-08-29
- **Confidence:** **Medium.** Unlike the passport, this is a decentralized service. The process (learner → wait → test → permanent license) is consistently reported and reliable. Exact fee amounts vary across sources (including some claiming to be "official") and are **not** treated as fully trustworthy here — see Section 5.

---

## 1. Overview

There is no single "Pakistani driving license" system — each province/territory runs its own licensing authority, online portal, fee schedule, and waiting periods. The PakAssist agent should always ask the user which province/city they are in before giving process or fee details, since answers genuinely differ.

## 2. License Categories (broadly consistent nationwide)

| Category | Covers |
|---|---|
| Motorcycle (MC) | Two-wheelers |
| Light Transport Vehicle (LTV) | Cars and light vehicles, private use |
| Heavy Transport Vehicle (HTV) | Buses, trucks |
| Public Service Vehicle (PSV) | Commercial passenger vehicles (taxis, vans, buses) |
| International Driving Permit (IDP) | For driving abroad; requires an existing valid permanent license |

Minimum age is generally 18 for motorcycle and car categories (commercial/heavy categories may require a higher minimum age — confirm per province).

## 3. General Process (applies across provinces, with local variation in exact steps)

1. **Register / create an account** on the relevant provincial portal using CNIC.
2. **Apply for a Learner's Permit** online or at the licensing office. This lets you practice driving under supervision only — it does not permit independent driving.
3. **Mandatory waiting period** after the learner permit before the permanent license can be applied for. This varies by province and category — Punjab has been reported at around 42 days; Sindh has been reported at 45 days (private) / 60 days (commercial). **Confirm the current figure on the applicable provincial portal**, since these periods are policy decisions that can change.
4. **Book and pass** a theory test (traffic signs/rules) and a practical driving test.
5. **Submit documents, pay the fee, and complete biometrics/photograph** at the licensing office or a mobile facilitation unit.
6. **Receive the license** — many provinces now issue a digital/e-license immediately, with a physical smart card following by mail/courier or collected in person.
7. **Track status and verify licenses** online via CNIC on the provincial portal.

## 4. Required Documents (typical, confirm province-specific list)

- Original CNIC + photocopy.
- Passport-size photographs (recent, per portal's specification).
- Medical fitness certificate/form (some provinces require a specific "Medical Form-B" attested by a government medical officer, e.g., Islamabad).
- Proof of fee payment (bank challan / PSID / online payment receipt).
- Learner's permit (for the permanent license application step).
- For an International Driving Permit: an existing valid Pakistani permanent license.

## 5. Fees — Handle With Care

Multiple non-government aggregator sites report different numbers for the same license category (e.g., a Punjab motorcycle learner fee has been reported anywhere from Rs. 60 to Rs. 180 depending on the source, and permanent license fees anywhere from roughly Rs. 500 to Rs. 2,150). This spread suggests either:
- Genuine year-to-year fee revisions that different articles captured at different times, and/or
- Some aggregator sites simply being inaccurate or outdated.

**Recommendation for the PakAssist agent:** Do not quote a single "official" fee number for driving licenses unless it has been independently confirmed directly on the relevant government portal (`dlims.punjab.gov.pk`, `dlsonline.sindhpolice.gov.pk`, `islamabadpolice.gov.pk/itp`) at response time, or the QA team has verified it against an official notification/screenshot. Where exact figures can't be confirmed, give the user a rough range and direct them to generate their PSID on the official portal, where the exact current fee is always shown before payment.

Indicative (unverified) ranges seen across multiple sources, for context only:
- Learner permit: roughly Rs. 60–1,000 depending on province.
- Permanent car (LTV) license: roughly Rs. 500–3,000 depending on province, validity, and category.
- Renewal: typically cheaper than a new license, often charged per year of validity.
- International Driving Permit (Punjab): reported around Rs. 1,650.

## 6. Province Notes

### Punjab
- Portal: DLIMS (official domain `dlims.punjab.gov.pk`).
- Has moved to Smart Card driving licenses (replacing paper).
- Supports online appointment booking, application tracking, and e-payment.

### Sindh
- Portal: DLS Online (`dlsonline.sindhpolice.gov.pk`), with a companion info site `dls.gos.pk` and a mobile app.
- Reported to let applicants choose the license validity period (3 or 5 years) at the time of application, which is different from provinces with a fixed validity.
- Process reported to include a pre-appointment booking step, front-desk verification, medical exam, fee payment, theory test, road test, and courier delivery of the physical card.

### Islamabad Capital Territory (ICT)
- Authority: Islamabad Traffic Police (ITP), portal at `islamabadpolice.gov.pk/itp`.
- Offers online license verification, online renewal (including for overseas Pakistanis), and online appointment booking for the ITP License Branch (Shakarparian).
- Requires a "Medical Form-B" attested by a medical officer as part of the application.
- A license expired for more than ~3 years may require the applicant to retake the practical test — confirm current threshold with ITP.

### Khyber Pakhtunkhwa (KP)
- Managed by the KP Excise, Taxation & Transport Department.
- Online services are reported as less developed than Punjab/Sindh/Islamabad as of 2026; a newer system ("DASTAK") has been mentioned in secondary sources but was **not independently confirmed** during this research pass — flag for follow-up verification before including in user-facing answers.

### Balochistan
- Managed by the provincial Excise & Taxation Department.
- No dedicated, clearly-documented online portal was confirmed during this research pass. Treat Balochistan driving license information as **low confidence** until verified directly with the department.

## 7. Office Locations

Unlike the passport (one national list), driving license offices are
scattered across five separate provincial systems, and only a partial list
could be verified directly against official sources during this research
pass. The structured dataset is at
`service_center_datasets/driving_license_service_centers.json` — treat its
`confidence` field as the trust level for each record.

Confirmed so far:

| Province | Office | Address | Phone | Confidence |
|---|---|---|---|---|
| Islamabad (ICT) | ITP License Branch, Shakarparian | Shakarparian, Islamabad | — | High |
| Punjab | Attock Driving Licensing Branch | DSP Traffic Office, Saddar Bazar, Attock Cantt | 0579-316006 | High |
| Punjab | Bhakkar Driving Licensing Branch | Driving Licensing Branch, DPO Office, Bhakkar | 0453-9200357 | High |
| Sindh | Sindh Police Driving License Dept. (province-wide, online-first via DLS) | Branch addresses not yet independently confirmed | — | Medium |
| KP | KP Excise, Taxation & Transport Dept. | Not confirmed | — | Low |
| Balochistan | Balochistan Excise & Taxation Dept. | Not confirmed | — | Low |

**For the full Punjab district list:** the official source is
`https://trafficpolice.punjab.gov.pk/licensing_offices`, but it blocks
automated scraping — someone on the team needs to open it in a browser and
transcribe the remaining districts by hand. **Do not** substitute addresses
from non-`.gov.pk` sites found during research (e.g. `dlims-punjab.com.pk`,
`dlims.org.pk`) — several of these are not official and closely mimic the
real DLIMS branding, which is itself worth a note to the wider team as a
citizen-facing scam risk, separate from our own data-quality concerns.

## 8. Common Pitfalls (for the agent to proactively warn users about)

- Assuming there's one national driving license system — there isn't; the process depends on the applicant's province.
- Trying to apply for a permanent license before the mandatory learner-permit waiting period has elapsed.
- Not bringing province-specific required documents (e.g., Islamabad's Medical Form-B).
- Assuming fee amounts quoted by unofficial websites are current — always route the user to the official portal to confirm before they pay.
- Confusing a Learner's Permit with a full license — a learner permit does not allow unsupervised driving.

## 9. Suggested User Intents This Document Should Answer

- "How do I get a driving license in Lahore/Karachi/Islamabad?"
- "How long do I have to wait after getting a learner's permit?"
- "What documents do I need for a driving license in Punjab?"
- "How do I get an International Driving Permit?"
- "How do I renew my driving license?"
- "Where do I check if my driving license is genuine?"
- "Where's the nearest driving license office to me?" (answerable with high confidence only for the offices marked "High" in the dataset; otherwise the agent should be upfront that it can only point to the provincial portal/department, not a specific branch)

## 10. Open Research Items (for QA / follow-up)

- [ ] Confirm the exact, current learner and permanent license fees directly from each provincial portal (screenshot + date).
- [ ] Confirm KP's "DASTAK" system name, scope, and URL directly with the KP Excise & Transport Department.
- [ ] Confirm whether Balochistan has any online portal at all.
- [ ] Confirm minimum ages for HTV/PSV categories per province.
- [ ] Confirm exact learner-to-permanent waiting periods per province and category (this document currently reports informally-sourced figures for Punjab and Sindh only).
