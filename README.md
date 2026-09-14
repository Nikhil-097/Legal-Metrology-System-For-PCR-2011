# Legal Metrology (PCR 2011) Packaging Compliance Verification System

An automated computer vision and multimodal inspection platform designed to audit packaged commodity artwork and inkjet batch printings against the statutory mandates of the **Legal Metrology (Packaged Commodities) Rules, 2011** and the **Legal Metrology Act, 2009**.

## Quick Start (Docker Compose)
\\\ash
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
docker-compose up --build -d
\\\

## Local Development
- **Backend**: \python run.py\ (Runs on http://localhost:8000)
- **Frontend**: \cd web_dashboard && npm run dev\ (Runs on http://localhost:3000)
