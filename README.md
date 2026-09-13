Legal Metrology Compliance Verification System
An automated, enterprise-grade computer vision platform designed to audit packaged commodity artwork against the statutory mandates of the Legal Metrology (Packaged Commodities) Rules, 2011 and the Legal Metrology Act, 2009.
This system replaces manual 15-minute caliper inspections with a sub-2-second digital scan, empowering Legal Metrology Officers to verify Unit Sale Price (USP) mathematics, Rule 7 font-size restrictions, and mandatory declarations (MRP, Net Quantity, Consumer Care) with zero AI hallucination.

The "Neuro-Symbolic" Architecture
The Neuro Layer (Perception): Heavy image preprocessing (OpenCV/PyZbar) feeds normalized packaging images to the Google Gemini Flash Vision API. The AI is restricted strictly to extracting spatial bounding boxes and raw text.
The Symbolic Layer (Judgment): A deterministic Python backend receives the JSON payload and executes strict, hard-coded statutory mathematics. It calculates the Principal Display Panel (PDP) area, verifies font heights against physical barcode anchors, and divides MRP by Net Quantity to audit the USP.

Technology Stack
Frontend: Next.js 14, React, Tailwind CSS, Lucide React, React Leaflet (for inspection mapping).
Backend: Python 3.10, FastAPI, Uvicorn, SQLAlchemy.
Computer Vision & AI: Google Gemini API, OpenCV, Pillow, PyZbar.
Database & Evidence Storage: PostgreSQL 15 (PostGIS), MinIO (S3-Compatible).
DevOps: Docker, Docker Compose, GitHub Actions.

How to Run the Project Locally
This repository is fully containerized for seamless deployment across any operating system. We recommend using Docker Compose for the easiest setup.  
Prerequisites
Docker Desktop installed and running.

Git installed on your system.

A valid Google Gemini API Key.

Step 1: Clone and Configure
Clone the repository to your local machine:

Bash
git clone https://github.com/your-org/legal-metrology-system.git
cd legal-metrology-system
Copy the example environment file to activate the configuration variables:  


Bash
cp .env.example .env
Open the .env file in your preferred text editor and insert your Gemini API Key:  


Code snippet
GEMINI_API_KEY=your_actual_api_key_here
Step 2: Boot the Infrastructure
Use Docker Compose to build and start the entire microservice architecture (PostgreSQL database, MinIO storage, FastAPI backend, and Next.js frontend):  


Bash
docker-compose up --build -d
Note: The initial build may take 3-5 minutes as it compiles system dependencies like OpenCV and libzbar-dev.  

Step 3: Access the System
Once the containers are successfully running, the system will be available at the following local addresses:

Officer Web Dashboard (Next.js): http://localhost:3000


Backend API Swagger Docs: http://localhost:8000/docs

  

MinIO Storage Console: http://localhost:9001 (Login: minioadmin / minioadmin)

  
 
  Manual Development Setup (Without Docker)
If you wish to run the modules separately for active development, ensure you have Python 3.10 and Node.js 18+ installed.  


1. Start the FastAPI Backend:

Bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
The backend will run on http://localhost:8000.  


2. Start the Next.js Frontend:

Bash
cd web_dashboard
npm ci
npm run dev
The frontend will run on http://localhost:3000.  


Core Features & Usage
Dual-Surface Auditing: Navigate to /scan on the dashboard. Upload the front Principal Display Panel (PDP) and back information panel of any packaged commodity.  


Statutory Parameter Processing: The system will dynamically clean the image, extract EAN-13 barcodes, and verify the printed origin against GS1 India registry databases.  


Automated Defect Flagging: The backend evaluates the text against the legal_metrology_rules.json matrix. If the Unit Sale Price (USP) is missing, or the Net Quantity lacks standard metric symbols, the system flags the specific rule violation (e.g., Rule 6(1)(d)).  


Digital Evidence Generation: Click Export Statutory PDF to generate a Section 65B compliant Show-Cause notice. This dynamically generated ReportLab PDF includes the compliance breakdown and is permanently stored in the MinIO vault.  
