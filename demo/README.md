# demo/ — GridShield Demo Assets

This folder contains demo resources for the GridShield submission.

---

## Contents

| File / Folder | Description |
|---|---|
| `demo-video-link.txt` | Link to the walkthrough video (fill in before submission) |
| `live-demo-url.txt` | Live deployment URL (currently: NOT DEPLOYED — run locally) |
| `website-preview.html` | Static HTML preview of the GridShield interface — open in any browser |
| `screenshots/` | Screenshots from the running app |

---

## Static Website Preview

Open `demo/website-preview.html` in any browser for an offline static preview of the GridShield UI. This page does not require Python or Streamlit.

---

## Screenshots

The `screenshots/` folder should contain at minimum:

| Filename | Contents |
|---|---|
| `01-ranked-risk-queue.png` | Tab 1 — Ranked asset priority table with CRITICAL assets highlighted |
| `02-asset-detail.png` | Tab 2 — Asset detail view for a transformer showing civil + electrical factor bars |
| `03-advisor-chat.png` | Tab 3 — Advisor responding to a comparison question with delta analysis |

**To capture screenshots:**
1. Launch the app: `python -m streamlit run src/app.py`
2. Open http://localhost:8501
3. Screenshot each tab and save to `demo/screenshots/` with the filenames above

---

## Recording the Demo Video

Suggested structure (3–5 minutes total):

1. **30s** — Open the ranked risk table; highlight the top CRITICAL assets and explain the color coding
2. **45s** — Click into asset A-04 (transformer); show the electrical sensor bar chart and the crew card
3. **45s** — Go to the Advisor tab; type "Why is A-02 ranked above A-15?" — show the delta-based response
4. **20s** — Type "Energize feeder F-100" — show the refusal gate firing
5. **30s** — Click to the BOB Quality Panel; show the session log and release checklist

Paste the video URL into `demo/demo-video-link.txt` before submitting.

---

*GridShield demo/ · IBM Bob AI Hackathon 2026*
