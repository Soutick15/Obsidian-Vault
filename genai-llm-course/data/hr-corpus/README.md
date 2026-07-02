# HR Corpus — Acme Corp Sample Knowledge Base

## What Is This?

This directory contains a **synthetic HR and recruitment document corpus** for the Acme Corp fictional company. It is sample data used as the shared knowledge base for the AI Training capstone project across all three tracks:

- **Developer track**: Build a RAG-based internal knowledge assistant that answers employee questions from these documents.
- **QA track**: Test the assistant's accuracy, coverage, and edge-case handling using the example questions below as eval seeds.
- **DevOps track**: Deploy, scale, and monitor the assistant in a containerized environment.

All documents are **entirely fictional**. Any resemblance to real companies, policies, or persons is coincidental. Do not treat any information here as actual legal or HR advice.

---

## Document Index

| File | Description |
|---|---|
| `employee-handbook-overview.md` | Company overview, values, key contacts, at-will employment basics |
| `leave-and-pto-policy.md` | PTO accrual by tenure, sick leave, parental leave, bereavement, jury duty |
| `benefits-and-insurance.md` | Health/dental/vision plans, 401(k) match, life/disability, wellness stipend, EAP |
| `remote-work-policy.md` | Remote-first policy, core hours, home office stipend, international work rules |
| `code-of-conduct.md` | Expected behaviors, prohibited conduct, harassment, conflict of interest, reporting |
| `expense-and-reimbursement-policy.md` | Spending limits, travel rules, meal policy, submission process |
| `performance-review-process.md` | Review cadence (mid-year + annual), rating scale, calibration, merit impact, PIPs |
| `recruitment-and-hiring-process.md` | Interview loop stages, offer process, referral bonus ($2,000), internal mobility |
| `onboarding-checklist.md` | Day 1 / Week 1 / Month 1 checklists for new employees |
| `it-and-security-policy.md` | Accounts, passwords, MFA, device policy, acceptable use, VPN, data classification |
| `compensation-and-promotion.md` | Salary bands (L1–L7), merit increase ranges, promotion process, RSU vesting |
| `holidays-2026.md` | Full list of 12 company holidays for 2026, floating holiday, weekend rules |

---

## Example Questions and Source Documents

These 10 questions are grounded in the corpus and serve as **eval/test seeds** for the QA track. Each question should be answerable by the assistant from the listed source document(s).

| # | Question | Primary Source(s) |
|---|---|---|
| 1 | How many PTO days do new employees get in their first two years? | `leave-and-pto-policy.md` |
| 2 | What is the parental leave policy for a non-birth parent? | `leave-and-pto-policy.md` |
| 3 | What are the stages of the interview process at Acme Corp? | `recruitment-and-hiring-process.md` |
| 4 | Which company holidays fall in 2026, and are there any that land on a weekend? | `holidays-2026.md` |
| 5 | How much does Acme Corp match on 401(k) contributions? | `benefits-and-insurance.md` |
| 6 | What is the home office setup stipend for new remote employees? | `remote-work-policy.md` |
| 7 | What happens if an employee is rated "2 — Partially Meets" in a performance review? | `performance-review-process.md`, `compensation-and-promotion.md` |
| 8 | How does the employee referral bonus work, and how much is it? | `recruitment-and-hiring-process.md` |
| 9 | What are the password and MFA requirements for company accounts? | `it-and-security-policy.md` |
| 10 | When do merit increases take effect, and what increase can a "Meets Expectations" employee expect? | `performance-review-process.md`, `compensation-and-promotion.md` |

---

## Internal Consistency Notes

Key facts that are consistent across documents (verify these stay in sync if any document is updated):

- PTO for new employees: **15 days/year** (0–2 years of service) — `leave-and-pto-policy.md`
- Parental leave (primary): **16 weeks** paid; (secondary): **6 weeks** paid — `leave-and-pto-policy.md`
- 401(k) match: **100% up to 4% of salary**, 3-year graded vesting — `benefits-and-insurance.md`
- Home office stipend: **$750 one-time** — `remote-work-policy.md`
- Referral bonus: **$2,000** after 90 days of new hire's employment — `recruitment-and-hiring-process.md`
- Merit increases effective: **March 1** each year — `performance-review-process.md`, `compensation-and-promotion.md`
- "Meets Expectations" merit range: **3–5%** — `compensation-and-promotion.md`
- Performance reviews: **twice yearly** (mid-year in July, annual in January) — `performance-review-process.md`

---

*Corpus version: 1.0 | Created January 2026 for AI Training capstone | People Operations, Acme Corp (fictional)*
