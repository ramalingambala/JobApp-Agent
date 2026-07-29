# Job Application Agent

An agentic AI system that scores a candidate's professional profiles (an
**Individual Contributor** profile and a **Leadership** profile) against any job
description, identifies gaps, and suggests grounded, actionable improvements —
then logs every run into a cumulative ATS-style PDF report.

Built with **LangGraph** for orchestration, **LlamaIndex + Chroma** for
Retrieval-Augmented Generation (RAG), and a multi-provider LLM setup
(**Groq** primary, **Azure OpenAI / OpenAI** fallback).

> A full write-up of the architecture, tech choices, RAG design, trade-offs and
> FAQ is in [`docs/Codebase-Technical-Assessment.pdf`](docs/Codebase-Technical-Assessment.pdf).

---

## What it does

- Ingests a job description from a **URL**, a **file of URLs** (bulk), or **pasted text**.
- Extracts structured requirements (title, company, must-haves, nice-to-haves, seniority).
- Retrieves the most relevant profile passages (IC vs Leadership) via RAG.
- Produces an ATS-style score **/100 per profile**, recommends the stronger profile,
  and lists strengths, gaps, and improvement "levers".
- Appends each run to a JSON log and rebuilds a cumulative `ATS-Report.pdf`.

## Architecture

A LangGraph state machine with five linear nodes:

```
START → fetch_jd → parse_jd → score_profiles → analyse_gaps → update_ats → END
```

| Node             | Responsibility                                             | Tech                              |
| ---------------- | ---------------------------------------------------------- | --------------------------------- |
| `fetch_jd`       | Fetch JD text from a URL / search query                    | Exa                               |
| `parse_jd`       | Extract a structured `_ParsedJD` (Pydantic) model          | LlamaIndex `structured_predict`   |
| `score_profiles` | RAG-retrieve profile chunks and score both profiles        | Chroma + LlamaIndex + Groq LLM    |
| `analyse_gaps`   | Turn gaps into grounded improvement levers                 | Groq LLM                          |
| `update_ats`     | Append run to log and rebuild the cumulative PDF report     | ReportLab                         |

## Tech stack

- **Orchestration:** LangGraph
- **LLM framework:** LangChain (Groq primary, Azure OpenAI / OpenAI fallback with automatic rate-limit failover)
- **Structured extraction + RAG:** LlamaIndex
- **Vector store:** Chroma (local, persisted)
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (local, CPU — no API key)
- **Job data:** Exa (SDK, with optional Exa MCP server)
- **UI:** Streamlit  ·  **Reporting:** ReportLab  ·  **Config:** python-dotenv

## Getting started

```bash
# 1. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# then edit .env with your own API keys

# 3. Add your profile text files and point .env at them
#    (IC_PROFILE_PATH and LEADERSHIP_PROFILE_PATH)

# 4. Run the web app
streamlit run app.py

# ...or the CLI
python main.py --url "https://example.com/jobs/view/12345"
```

## Configuration

All configuration is via environment variables — see [`.env.example`](.env.example)
for the full list. No secrets are committed to this repository.

If you are behind a TLS-inspecting corporate proxy, set `CORP_CA_BUNDLE` to your
CA bundle path (see [`ssl_patch.py`](ssl_patch.py)); otherwise it is a no-op.

## Notes

- Profile text, the built vector store (`chroma_db/`), and run outputs (`output/`)
  are intentionally **git-ignored** — bring your own data.
- Scores are LLM-assisted decision support, not an absolute measure.

## License

Personal project — no warranty. Add a license file if you intend others to reuse it.
