<!--
PLACEHOLDER FILE.
This is a stand-in for Member 4's real knowledge_base/passport.md, used only so
the RAG pipeline in this repo has something real to ingest, chunk, embed, and
retrieve during development and tests. Replace with the actual team file —
do not treat the content below as verified.
-->

## Metadata

- Authority: Directorate General of Immigration & Passports (DGI&P)
- Official source: https://dgip.gov.pk/
- Date last verified: 2025-01-01 (placeholder)
- Confidence: high

## Overview

The Machine Readable Passport (MRP) is issued by DGI&P to Pakistani citizens
for international travel. Applications can be submitted online via the
Pak-Identity portal and completed in person at a Passport & Regional Office.

## Eligibility

Any Pakistani citizen holding a valid CNIC (or B-Form for minors) may apply.
Minors require a guardian's CNIC and consent.

## Required documents

- Valid CNIC or B-Form
- Passport-size photograph (as per DGI&P specification)
- Previous passport, if renewing
- Proof of guardianship, for minors

## Process steps

1. Register and fill the application on the Pak-Identity online portal.
2. Pay the applicable fee via bank or online payment.
3. Book or walk in for a biometric appointment at a Passport Office.
4. Collect the passport from the office or via courier, depending on service tier.

## Fees

Fees vary by passport type (normal/urgent/executive) and booklet size
(36/72 pages). See the official fee notification on dgip.gov.pk for current
figures — do not state a specific rupee amount without checking the latest
notification date.

## Validity / renewal

Standard passports are typically valid for 5 or 10 years depending on the
booklet chosen. Renewal follows the same process as a new application.

## Office/contact

See `../service_center_datasets/passport_service_centers.json` for the full
list of 180 office locations.

## Common pitfalls

- Submitting photos that don't meet the official size/background spec causes
  rejection at the counter.
- Urgent/executive fee tiers are often confused with normal processing time.

## Suggested user intents

- "What documents do I need for a new passport?"
- "How long does a Pakistani passport take?"
- "Where is my nearest passport office?"

## Open research items

- Confirm current fee table against the latest DGI&P notification.
