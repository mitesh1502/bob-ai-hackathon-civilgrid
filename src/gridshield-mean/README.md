# GridShield MEAN Stack

**Civil-Engineering-Aware Power Grid Advisor**  
IBM Bob AI Hackathon 2026 · Problem Statement U1: Power Outage Prediction & Grid Equipment Failure Advisor

## Stack

| Layer | Technology |
|---|---|
| **M**ongoDB | Stores all asset, incident, and computed risk data |
| **E**xpress | REST API — serves assets, runs pipeline, answers advisor questions |
| **A**ngular | Single-page app — 5 pages with live data from the API |
| **N**ode.js | Runtime for Express backend + pipeline engines |

## Architecture

```
gridshield-mean/
├── backend/
│   └── src/
│       ├── server.js               ← Express entry point
│       ├── models/
│       │   ├── Asset.js            ← Mongoose schema (full computed row)
│       │   └── Incident.js
│       ├── pipeline/
│       │   ├── generateData.js     ← Port of generate_data.py  (seed=42)
│       │   ├── riskEngine.js       ← Port of risk_engine.py    (exact same factors)
│       │   ├── priorityEngine.js   ← Port of priority_engine.py
│       │   ├── recommendEngine.js  ← Port of recommend.py      (same action table)
│       │   └── seed.js             ← Runs full pipeline → saves to MongoDB
│       ├── services/
│       │   └── advisor.js          ← Port of advisor.py        (grounded NL answers)
│       └── routes/
│           ├── assets.js           ← GET /api/assets, /api/assets/stats, /api/assets/:id
│           ├── pipeline.js         ← POST /api/pipeline/run, GET /api/pipeline/incidents
│           └── advisor.js          ← POST /api/advisor/ask
└── frontend/
    └── src/app/
        ├── app.component.ts        ← Shell with sidebar + pipeline rerun button
        ├── pages/
        │   ├── dashboard/          ← KPI cards + top-10 table
        │   ├── risk-table/         ← Sortable, filterable full asset table
        │   ├── asset-detail/       ← Factor bar chart + action card + safety note
        │   ├── reactive/           ← Reactive vs preventive comparison
        │   └── advisor/            ← Grounded NL Q&A chat interface
        ├── services/
        │   └── gridshield.service.ts ← HttpClient wrapper for all API calls
        └── models/
            └── asset.model.ts      ← TypeScript interfaces
```

## Quick Start (Windows)

### Prerequisites
- [Node.js 18+](https://nodejs.org)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community) — must be running on `localhost:27017`

### 1. Clone / navigate to this folder
```
cd gridshield-mean
```

### 2. One-click launch
```
start.bat
```
This will:
1. Install all npm dependencies (backend + frontend)
2. Seed the MongoDB database (runs the full data + risk + priority + recommendation pipeline)
3. Start the Express API on **http://localhost:3000**
4. Start the Angular dev server on **http://localhost:4200**

### 3. Manual steps (if needed)

**Backend only:**
```bash
cd backend
copy env.example .env.local     # or create .env with MONGO_URI and PORT
npm install
node src/pipeline/seed.js       # populate MongoDB once
npm run dev                     # starts nodemon dev server
```

**Frontend only:**
```bash
cd frontend
npm install
npm start                       # starts Angular dev server on :4200
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assets` | All 40 assets sorted by priority_score |
| GET | `/api/assets/stats` | Dashboard KPI counts |
| GET | `/api/assets/:id` | Single asset (e.g. `/api/assets/A-03`) |
| GET | `/api/pipeline/incidents` | All historical incidents |
| POST | `/api/pipeline/run` | Re-run full pipeline, refresh MongoDB |
| POST | `/api/advisor/ask` | `{ question }` → `{ answer }` |

## Python ↔ JavaScript Parity

Every Python engine is faithfully ported with identical logic:

| Python file | JS equivalent |
|---|---|
| `generate_data.py` | `pipeline/generateData.js` — same seed, same distributions |
| `risk_engine.py` | `pipeline/riskEngine.js` — same `scale()`, same 8 factors, same dominant-cause grouping |
| `priority_engine.py` | `pipeline/priorityEngine.js` — same multipliers, same `priority_score = expected_loss / cost` |
| `recommend.py` | `pipeline/recommendEngine.js` — same action table, same risk bands, same safety note |
| `advisor.py` | `services/advisor.js` — same ID detection, same summary/compare templates, same safety reminder |

## Safety

All recommendations are advisory only. No recommendation authorises live-line work, switching,
or excavation. Every response from the Advisor includes the full safety note from `recommend.py`.
