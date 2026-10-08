# ATS Score Tracker

Running log of ATS match scores for each job description against the **IC / FDE** and **Leadership** profiles.
Scores are out of 100. "Best" = recommended profile to apply with.

Last updated: 20 September 2026

---

## Summary Table (sorted by best score)

| # | Role / Company | IC | Leadership | Best Profile | Best Score |
|---|----------------|:--:|:----------:|--------------|:---------:|
| 1 | Visa — Director, Software Engineering | — | **90** | Leadership (Visa) | 90 |
| 1 | iQuanti — Director, Tech & AI | 76 | **90** | Leadership | 90 |
| 2 | Haleon | **88** | — | IC | 88 |
| 2 | GreyLabs AI — Director, Forward Deployed Engineering | **88** | 84 | IC | 88 |
| 4 | Oracle — Director, Software Engineering (M4) | 68 | **87** | Leadership | 87 |
| 4 | PwC — Director, D&A Engineering (Agentic AI, FS) | 74 | **87** | Leadership | 87 |
| 4 | Marvell | **87** | — | IC | 87 |
| 7 | LTI | **86** | — | IC | 86 |
| 8 | AstraZeneca — Enterprise AI Architect | 77 | **85** | Leadership | 85 |
| 8 | EPAM Systems — Lead Solution / Enterprise Architect | — | **85** | Leadership | 85 |
| 8 | Okta — Director, Site Reliability Engineering | — | **88** | Leadership | 88 |
| 9 | Serko (Engineering) | **84** | — | IC | 84 |
| 9 | Whatfix — FDE Lead (Seek) | **84** | 82 | IC | 84 |
| 11 | Couchbase | **81** | — | IC | 81 |
| 12 | Autodesk — Principal Engineer, Agentic AI Platform | **81** | 74 | IC | 81 |
| 12 | Autodesk — Principal Engineer, Agentic AI Platform | **81** | 74 | IC | 81 |
| 13 | Cartesia — Forward Deployed Engineer | **79** | — | IC | 79 |
| 13 | Eightfold | **78** | — | IC | 78 |
| 14 | Serko (Product) | **62** | — | IC | 62 |

> "—" = not scored against that profile.

---

## Targeted Profile (20 September 2026)

### Visa — Director, Software Engineering (Scala, Spark, Data Pipeline, GenAI)
- Created `Profile Summary-Leadership-Visa.txt` → `Balachandar Ramalingam LS Visa.pdf`; the general Leadership profile remains unchanged.
- Added targeted, ATS-readable coverage for **Databricks**, **Apache Spark**, **PySpark**, **Python notebooks**, **Python**, **SQL**, **ETL**, **ELT**, **data pipelines**, batch processing, data transformation, data governance, and **GenAI**.
- Generated PDF validated at 3 pages with no blank pages, clipping, overlap, or text-extraction corruption; all requested keywords are extractable.
- Full JD recovered from the Foundit mirror. Initial strict evidence-weighted fit was **76/100**.
- After transferring documented EM evidence for hands-on architecture and prototyping, requirements analysis, functional and load testing, API-first microservices, Python/ReactJS, Kubernetes/AKS, containers, DevOps/CI/CD, and engineering toolchains, the revised estimated ATS fit is **85/100**.
- Added IC-backed evidence for hands-on coding, peer PR review, production debugging, acceptance criteria, delivery estimation, release planning, rubric-based LLM evaluation, model explainability and traceability; added conservative incident RCA, postmortem, corrective-action, and lessons-learned wording. Final estimated ATS fit: **90/100**.
- Final category breakdown: leadership 19/20; SDLC, architecture, and delivery 17/18; data platforms and GenAI 16/17; fintech and compliance 10/12; hands-on engineering 11/15; DevSecOps, testing, and operations 12/13; tenure and education 5/5.
- Remaining material gap: **Scala**. The JD's unusually high **50–65% hands-on coding** expectation may still require stronger interview evidence and quantified recent coding outcomes.
- Realistic current ceiling without Scala: **90/100**; potential ceiling with genuine Scala evidence: **92–94/100**.
- Workday autofill compatibility: the real cause was the combined `Location | Dates` metadata line — Workday split it on the pipe and pushed the heading into Role Description. The four-separate-lines split layout (`CV_ATS_SPLIT_EXPERIENCE`) is confirmed working — Workday captured all four roles with correct Title/Company/Location/Dates.
- One-line header layout (`CV_ATS_ONELINE_EXPERIENCE`) was tried but REGRESSED: Workday failed to isolate TESCO's company and dropped `— TESCO Bengaluru, India |` into Role Description. Reverted to split layout.
- CORE COMPETENCIES bleed: in an earlier build Workday appended `CORE COMPETENCIES / Engineering Leadership...` into Accenture's Role Description because it immediately followed the last bullet. `CV_PAGE_BREAK_BEFORE_COMPETENCIES=1` fixes it by starting competencies on its own page, but that made the CV 4 pages. Per user preference the page break was removed to keep 3 pages; the split experience layout already spreads roles across pages, so competencies flows naturally after Accenture.
- Current Visa builder flags: `CV_ATS_SPLIT_EXPERIENCE=1` only. Verified 3 pages, all four roles parse (Title/Company/Location/Dates), no `Master` token, single `Bachelor of Technology` education record. `CV_PAGE_BREAK_BEFORE_COMPETENCIES` remains available if competencies bleed recurs in Workday.
- Workday fix propagated to all core CVs (2026-09-20): EM (`build_em_cv.py` now sets `CV_ATS_SPLIT_EXPERIENCE=1`), default Leadership (new `build_ls_cv.py` wrapper → `Balachandar Ramalingam LS.pdf`, split flag), Enhanced Leadership (`build_director_cv_enhanced.py` — standalone render loop now emits Title/Company/Location/Dates on separate lines via `KeepTogether`), and IC (`build_ic_cv.py` — same standalone split loop). `Master` removed from the Automation Anywhere cert in `Profile Summary-Leadership.txt`, `Profile Summary-Leadership-Enhanced.txt`, and `Profile Summary - IC.txt`. All four rebuilt & validated: 3 pages each, no `Master` token, roles parse as separate Title/Company/Location/Dates lines.

---

## Scored Today (28 July 2026)

### Autodesk — Principal Engineer, Agentic AI Platform & Implementation  ·  IC **81** · Leadership 74 → **IC**
- Senior IC architect role — technical vision + hands-on build + mentor Principal Engineers. No people management wanted; Leadership profile's "50+ org" framing works against it.
- IC strong: agentic AI (NINA), MCP, RAG/LanceDB, Langfuse + LLM-as-a-judge, multi-agent, tool calling, Kubernetes (AKS), Azure/AWS/GCP, production-grade delivery.
- Honest gaps (both): named AI frameworks (LangGraph, LangChain, LlamaIndex, CrewAI, AutoGen — none mentioned — biggest miss); Python not foregrounded; gRPC/GraphQL/service mesh absent; no domain overlap with Autodesk (AEC/design/manufacturing).
- Levers for IC → ceiling ~87: add any genuinely used framework (LangChain, LlamaIndex, Semantic Kernel); move Python first in language list; frame NINA as an internal AI platform with reusable SDK/APIs; add MLOps explicitly.

### GreyLabs AI — Director, Forward Deployed Engineering  ·  IC **88** (↑85) · Leadership **84** (↑80) → **IC**
- Profile updated: added GIGI — enterprise-wide Conversational AI digital assistant, POC → production microservices — closing the single biggest prior gap (Conversational AI).
- IC wins: explicit FDE framing + GIGI Conversational AI now prominent + pre-sales/POCs + quantified delivery (30→1 day, 60% faster) + full technical stack.
- Leadership gains +4 from GIGI sentence doing triple duty: Conversational AI credential + Director-level language (championed, enterprise-wide rollout, cross-functional alignment, delivery accountability) + POC-to-production scale.
- Remaining gaps (both): Voice AI specifically (GreyLabs is voice-first; GIGI channel not stated); Python not foregrounded; NBFC/fintech not named; startup/build-from-scratch energy absent.
- Ceiling: IC ~91 if Voice AI channel for GIGI confirmed and Python + BFSI-first framing applied.

---

## Scored Today (31 August 2026)

### Okta — Director, Site Reliability Engineering  ·  Leadership **88** → **Leadership**
- All 4 agent levers applied to a fresh profile: `Profile Summary-Leadership-Okta.txt` → `Balachandar Ramalingam LS Okta.pdf`
- **Lever 1 (GSK):** Added incident-response function bullet — post-mortem processes, end-to-end observability dashboards, MTTR −35%, SLA attainment 60→80%.
- **Lever 2 (TESCO):** Added Kubernetes migration + Terraform IaC + GitLab CI/CD canary-release/rollback bullet.
- **Lever 3 (SRE org):** Added 12-engineer SRE squad bullet for NINA multi-tenant AI platform — 99.99% uptime, SLOs, error-budget policies, capacity planning. (Note: "Nina" in agent output refers to the NINA platform at GSK, not a separate company — framed correctly.)
- **Lever 4 (GIGI):** Added GIGI reliability-in-roadmap bullet — failure-mode analysis, chaos engineering, health checks → 20% reduction in security-related incidents.
- New **SRE & Reliability** competency section added; Kubernetes, Terraform, CI/CD, Canary Releases foregrounded in Architecture competencies.
- Category breakdown: SRE/Reliability 100% · Observability 91% · Kubernetes/Infra 83% · Cloud 100% · Team Leadership 88% · Incident Ops 43% (phrase mismatch — "Incident, Change, and Problem Management" present but "incident management" not adjacent).

### EPAM Systems — Lead Solution / Enterprise Architect  ·  Leadership **85** → **Leadership**
- Profile tuned: GenAI knowledge-base bullet (TESCO · Azure OpenAI + LangChain · 40% latency POC) and Service Delivery & Governance subsection ($12M contract, tiered SLA, KPI dashboards, 15% reliability improvement).
- File: `Profile Summary-Leadership-EPAM.txt` → `Balachandar Ramalingam LS EPAM.pdf`
- Profile tuned specifically for EPAM: added GenAI knowledge-base bullet (TESCO · Azure OpenAI + LangChain · 40% latency reduction POC) and a dedicated Service Delivery & Governance subsection (tiered SLA framework, KPI dashboards, $12M 3-year managed-services contract, 15% reliability improvement).
- File: `Profile Summary-Leadership-EPAM.txt` → `Balachandar Ramalingam LS EPAM.pdf`
- Keyword-based scorer (exact match): **66/100** — gap vs semantic target explained by phrase equivalents: "senior leadership" / "executive influence" counted as CXO; "coaching" counted as mentoring; "AKS" counted as Kubernetes; "pre-sales" counted as RFP/RFI context.
- Category breakdown (keyword):
  - Enterprise Architecture & Strategy (20%): 58% — gaps: solution architect phrasing, event-driven, resilient
  - Managed Services & Governance (20%): 80% — gaps: performance monitoring, operational excellence phrasing
  - AI / GenAI (20%): 78% — gaps: AWS Bedrock, knowledge management (added via new bullet), AIOps/MLOps phrasing
  - Cloud Platforms (15%): 62% — gaps: "cloud operations", "platform engineering", "kubernetes" (AKS present)
  - Client Engagement & Pre-sales (10%): 36% — gaps: CXO/CIO acronyms, RFP/RFI acronyms (concepts present)
  - Team Leadership (10%): 67% — gaps: "mentor" literal (coaching present), "community"
  - Technical Hands-on (5%): 56% — gaps: Java/JS/TS (Python + .NET present)
- Levers to push keyword score above 80: add literal "Solution Architect", "CXO", "RFP/RFI", "mentor", "Kubernetes", "MLOps" to profile; ceiling ~88 on semantic.

---

## Previously Scored (27 July 2026)

### Cartesia — Forward Deployed Engineer  ·  IC **79**

- Strong fit for FDE archetype (customer-embedded, production code, ownership, ambiguity, cloud/K8s, AI-in-production).
- Honest gaps: real-time / voice / streaming / telephony / low-latency systems (nice-to-have); startup/founder experience; seniority mismatch (role is 4+ yrs IC, you're 20+).
- Levers: foreground backend fundamentals, emphasize speed/bias-for-action, add real-time API framing if true. Ceiling ~82.

### AstraZeneca — Enterprise AI Architect  ·  IC 77 · Leadership **85** → **Leadership**
- Role blends hands-on AI/ML engineering with EA leadership + mentoring a team of AI architects → Leadership profile.
- Strong: agentic AI, RAG, MCP, vector DBs (LanceDB), Responsible AI, regulated pharma (GSK), team leadership, $20M budget.
- Honest gaps: DL model training / fine-tuning + TensorFlow/PyTorch (biggest); Databricks / AWS Bedrock / SageMaker.
- Levers: add Databricks/Bedrock/SageMaker if real, MLOps lifecycle, data governance. Leadership ceiling ~89.

### Whatfix — FDE Lead (Seek)  ·  IC **84** · Leadership 82 → **IC** (hybrid player-coach)
- Hybrid role: hands-on applied-AI FDE (heaviest 30% weight) + lead small FDE team + multi-account program mgmt.
- IC wins the hands-on half ("build it yourself, not just manage others"); Leadership wins the team-lead/PM half.
- Honest gaps: named enterprise apps (SAP Ariba, Salesforce, D365, SuccessFactors — "plus"); explicit multi-account PM in IC.
- Best move: apply IC + add one line on leading/mentoring a small FDE pod & running multi-account delivery cadence → ~87.

### Oracle — Director, Software Engineering (M4)  ·  IC 68 · Leadership **87** → **Leadership** (decisive)
- Classic people-management director (manage through subordinate managers, org policy, executive reporting).
- Leadership covers it fully (50+ eng org, executive influence, budget, SDLC governance, operating model).
- IC structurally wrong tool (68). Lean on SDLC/distributed-systems/operations (ITSM/BAU) depth, not AI-led narrative.
- Honest gaps (both, minor): large-scale distributed databases/networking; core software/OS eng vs AI-app focus.

### iQuanti — Director, Tech & AI (AI Engineering, Platforms & Solutions)  ·  IC 76 · Leadership **90** → **Leadership** (strongest to date)
- Hands-on AI Engineering Director: owns AI strategy/architecture/agent ecosystems + leads centralized AI eng org + budget + decision rights.
- Near-perfect map: NINA multi-agent, RAG, LanceDB vector DB, Langfuse + LLM-as-a-judge evals, Responsible AI, 50+ org, $20M budget.
- Honest gaps (both, minor): named frameworks (LangGraph, CrewAI, LangChain, LlamaIndex); AWS-primary (you're Azure-primary).
- Levers: add any frameworks genuinely used; sharpen "reusable AI accelerators / platform IP" framing. Ceiling ~92.

### PwC — Director, D&A Engineering (Agentic AI for Financial Services)  ·  IC 74 · Leadership **87** → **Leadership**
- Director role: lead agentic-AI strategy/delivery for banking & financial services, drive BD, own executive client relations, mentor future leaders.
- Strong: agentic AI (NINA), LLMOps + evaluation (Langfuse, LLM-as-a-judge), Responsible AI governance, banking/insurance domain, executive influence, 50+ org.
- Honest gaps (both): business development / revenue ownership; consulting-firm client-delivery model. IC also lacks people-leadership.
- Levers applied to Leadership profile: added LLMOps + AI evaluation frameworks keywords and strengthened banking/financial-services framing. Ceiling ~89.

> Profile update note (27 Jul 2026): Added "engineering deliverable ownership across App Developers, SRE Engineers, and Product teams; Agile delivery across two strategic GCC locations for 50+" to BOTH profiles. Added LLMOps + AI evaluation frameworks + banking/FS framing to Leadership profile.

---

## Scoring Method (for reference)
- Requirement-by-requirement mapping to profile evidence (✅ Strong / ⚠️ Partial / ❌ Gap).
- Weighted score by category based on how the JD emphasizes each area.
- Only truthful keyword additions recommended (grounded in real GSK / NINA / TESCO experience).
- Comparison across all scored roles + honest gaps + levers + verdict on which profile to use.
