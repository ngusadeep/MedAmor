# OncoSync: Orchestrating Multi-Agent Tumor Boards

## 🎯 Project Overview
OncoSync reduces lung cancer treatment delays from 21 to 7 days by creating an AI-powered virtual tumor board that synchronizes radiology, pathology, and clinical data using Google's MedGemma. Our agentic system leverages all 7 MedGemma capabilities to provide comprehensive patient analysis in hours instead of weeks, while maintaining strict privacy compliance through local deployment.

## 📊 Problem Statement
**The Clinical Crisis: 3-Week Treatment Delays**
- **Current Reality**: Stage III NSCLC patients wait 21 days on average for tumor board decisions
- **Human Cost**: Every week of delay decreases 5-year survival by 2%
- **Systemic Burden**: Specialists spend 90+ minutes preparing for each case
- **Guideline Inconsistency**: Only 67% of cases follow NCCN guidelines consistently

**Root Causes:**
- Scheduling Bottlenecks: Coordinating 5+ specialists across departments
- Information Silos: Radiology, pathology, and clinical data remain disconnected
- Manual Synthesis: Doctors manually compile 50+ pages per patient
- Resource Constraints: Limited specialist availability creates backlogs

**Target User & Impact:**
- **Primary Users**: Oncologists, Radiologists, Pathologists, Tumor Board Coordinators
- **Secondary Users**: Patients (through faster treatment), Healthcare Systems (through efficiency)
- **Annual Impact Scope**: 200,000+ new lung cancer cases in US alone

## 🎯 Project Objectives
**Primary Objectives:**
- Reduce Time-to-Treatment from 21 to 7 days for Stage III NSCLC
- Improve Guideline Adherence from 67% to 95%
- Decrease Specialist Prep Time from 90 to 15 minutes per case

**Technical Objectives:**
- Implement 7/7 MedGemma capabilities in integrated workflow
- Create LangGraph agentic system with 6 specialized nodes
- Build privacy-preserving architecture for hospital deployment
- Demonstrate real-time multimodal data synthesis

## 🏗️ Solution Architecture
**Core Workflow: The Virtual Tumor Board**
```
Patient Case Input → Radiology Agent → Multimodal Synthesizer
                     ↓
Pathology Agent ──────┘
                     ↓
Clinical Data Agent ──┘
                     ↓
Longitudinal Analysis → Guidelines RAG Engine → Treatment Recommender → Human-in-the-Loop Dashboard → Final Treatment Plan
```

**Agentic System Components:**
1. **Radiology Agent (MedGemma-CXR)**: DICOM CT/X-ray analysis, TNM staging
2. **Pathology Agent (MedGemma-Text)**: Biomarker extraction from reports
3. **Clinical Data Agent**: EHR processing and patient context summary
4. **Longitudinal Analysis Agent**: Tumor progression metrics
5. **Guidelines RAG Engine**: Evidence-based guideline retrieval
6. **Treatment Recommender**: Ranked treatment options with evidence

## 💻 Tech Stack
- **Frontend**: Next.js 14 with App Router, Shadcn/ui + Tailwind CSS
- **Backend**: FastAPI + Python (uv package manager)
- **AI/ML**: MedGemma-CXR/2B, LangGraph, LangChain, ChromaDB
- **Infrastructure**: Docker, PostgreSQL, Redis, Celery
- **Monitoring**: Prometheus + Grafana, LangSmith

## 📁 Data Sources
- **Imaging**: NIH Chest X-ray, DeepLesion CT, RIDER-LUNG-CT
- **Text**: TCGA-Reports, NCCN Guidelines, Synthea synthetic data
- **Synthetic Cases**: 100 generated NSCLC patient cases

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- uv package manager

### Quick Start with Docker (Recommended)
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OncoSync
   ```

2. **Copy environment configuration**
   ```bash
   cp env.example .env
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ChromaDB: http://localhost:8001
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### Development Setup (Alternative)
1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### 🏗️ Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 3000)   │    │   (Port 8000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Redis         │    │   ChromaDB      │
                    │   Cache/Queue   │    │   Vector DB     │
                    │   (Port 6379)   │    │   (Port 8001)   │
                    └─────────────────┘    └─────────────────┘
```

## 📋 Development Phases
- **Phase 1**: Project Foundation & Setup ✅
- **Phase 2**: Core Agent Architecture
- **Phase 3**: Data Pipeline & RAG System
- **Phase 4**: Treatment Recommendation System
- **Phase 5**: Data Ingestion & Processing
- **Phase 6**: Frontend & Integration
- **Phase 7**: Security, Testing & Deployment

---

*Built for the Kaggle x Google Gemini Hackathon*