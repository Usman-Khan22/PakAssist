# PakAssist Knowledge Base

This folder is the Member 4 (Research, Data, QA & Integration) deliverable:
a trusted, sourced knowledge base for the services PakAssist currently
supports. It is written in Markdown so it's easy for the team to review,
edit, and fact-check by hand right now, and structured so it can be chunked
and loaded into a retrieval system (RAG) later, once that milestone is
scheduled — per `PROJECT_CONTEXT.md`, this repo does not build RAG yet.

## Files

| File | Service | Confidence |
|---|---|---|
| `passport.md` | Pakistani passport (DGI&P) | High — single federal authority, one official site |
| `driving_license.md` | Driving license (all provinces) | Medium — decentralized, fee figures need per-province confirmation |

## Why the two documents look different

The passport is issued by one federal body (DGI&P), so the information is
consistent and the fee tables can be stated with confidence, tied to a
specific notification date. Driving licenses are issued by five separate
provincial/territorial authorities, so the process is generally consistent
but exact fees and portal names vary and are harder to verify from public
sources alone. `driving_license.md` is written to be explicit about that
uncertainty rather than presenting an unverified number as fact — this
matters for the "identify hallucinations" part of Member 4's job, since an
agent trained on overconfident source data will produce overconfident (and
possibly wrong) answers.

## Document Structure (used consistently, so it's easy to chunk later)

Each service file follows this template:
1. **Metadata** — authority, official source URLs, date last verified, confidence level
2. **Overview**
3. **Eligibility**
4. **Required documents**
5. **Process steps**
6. **Fees**
7. **Validity / renewal / edge cases**
8. **Office hours / contact**
9. **Common pitfalls** — things the agent should proactively warn users about
10. **Suggested user intents** — example questions this document should be able to answer, useful later for retrieval testing and QA
11. (where relevant) **Open research items** — known gaps for the team to close

## How to Extend This

When adding a new service (e.g., CNIC/ID card, vehicle registration):
1. Copy the section structure above.
2. Cite only official `.gov.pk` sources where possible. If no official
   source exists or is unclear, say so explicitly rather than guessing —
   see how `driving_license.md` handles Balochistan and KP.
3. Note the date you verified the information and re-check every few
   months, since fees and rules change by government notification.
4. Add a "Common pitfalls" and "Suggested user intents" section — these
   feed directly into the QA test set (Member 4's hallucination-testing
   work) and eventually into retrieval evaluation.

## Not Yet Covered

Per `PROJECT_CONTEXT.md`'s next milestone, only the services actually
scheduled should get full treatment. Not yet built:
- CNIC / ID card (NADRA)
- Vehicle registration
- Appointment booking specifics (see the separate service-center and
  appointment-slot datasets, planned next)
- Urdu-language versions of this content

## Sources Log

See `sources.md` for the full list of URLs consulted, with dates, so QA
can re-verify or trace any fact back to where it came from.

## Related: Service Center Datasets

Office-level data (addresses, phone numbers, per-office confidence ratings)
now lives in structured JSON alongside a summary table inside each service
file's "Office Locations" section:
`../service_center_datasets/passport_service_centers.json` (180 offices,
high confidence) and
`../service_center_datasets/driving_license_service_centers.json` (6
starter records, mixed confidence — driving license offices are
provincially fragmented, see that file's own README for why).
