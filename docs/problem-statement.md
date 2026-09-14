# docs/problem-statement.md — GridShield

## The Problem: Calendar-Based Maintenance Is Failing the Grid

### Who Is Affected

- **Grid operators and asset managers** at electric utilities who must decide which of hundreds or thousands of distribution assets to inspect or repair in any given week — with a fixed maintenance budget and incomplete condition visibility.
- **Maintenance crews** who are dispatched reactively after failures, often in dangerous weather conditions, rather than proactively while conditions are safe.
- **Downstream customers** — hospitals, water treatment plants, shelter facilities, and residential consumers — who lose power when a preventable failure occurs.
- **Utility finance and risk teams** who bear the cost of unplanned outages, emergency repairs, and regulatory penalties.

---

### The Core Gap

Most distribution utilities still schedule maintenance by **calendar cycle** — inspect every asset every N years regardless of condition. This approach was designed for a world where:

- Sensors were expensive or unavailable
- Weather events were less frequent and less severe
- The grid was simpler and more homogeneous

None of these assumptions hold today.

**What utilities have, but don't fully use:**

| Data source | What it tells you | Typically used for? |
|---|---|---|
| Transformer temperature sensors | Thermal overrun → insulation failure in weeks | Alarm dashboards only |
| Vibration monitors | Mechanical loosening, winding movement | Not integrated with maintenance scheduling |
| Partial discharge meters | Insulation degradation, arcing risk | Specialist inspection only, not fleet-wide |
| Oil quality samples | Dissolved gas → fault type | Scheduled sampling, not real-time |
| Weather forecast APIs | Storm paths, wind gusts, flood risk | Storm response only, not pre-positioning |
| Civil inspection records | Foundation tilt, erosion, drainage | Paper-based, not combined with sensor data |

These data streams exist in separate silos. No single system combines them to tell an engineer: *"This transformer is at 78/100 risk primarily due to partial-discharge anomalies, it serves a hospital, intervention costs $10,000, and if you act this week before the forecast storm you avoid an expected $350,000 outage."*

---

### Why It Matters Now

**Aging infrastructure:** In the UK, US, and most developed grids, a significant fraction of distribution transformers and substations are over 30 years old — approaching or exceeding their design life. Calendar maintenance misses the assets that are degrading faster than average.

**More frequent extreme weather:** The number of significant storms, heat events, and flood events affecting power infrastructure has increased sharply. Each event compounds the structural risk of assets that are already marginal on sensor health.

**Cost of failure is asymmetric:** A single transformer failure on a feeder serving a hospital or water treatment plant costs $1M+ per hour in outage penalties, emergency repair, and customer compensation — far exceeding the $8,500–$10,000 intervention cost for a proactive replacement.

**Crew pre-positioning is time-limited:** Once a storm is 48 hours away, staging crews and materials at the right locations can prevent dozens of failures. Without a ranked, evidence-based priority list, operators have no systematic way to decide where to position resources.

---

### Quantified Cost

| Event type | Illustrative cost |
|---|---|
| Transformer failure on hospital feeder (72h outage) | ~$3.6M in outage penalties + $45,000 emergency repair |
| Planned preventive replacement (insulation degradation) | $10,000–$15,000 |
| Storm response: reactive repair after 10 assets fail | ~$500,000 total, 4–6 days of crew time |
| Storm response: proactive intervention on top-5 priority assets | ~$30,000–$50,000, completed before the storm |

The economic case for a prioritised preventive queue is not subtle. The gap is the absence of a system that can produce that queue from first principles using available data.

---

### What GridShield Addresses

GridShield is a **proof of concept** that this gap is closeable with existing open-source tools, available data, and transparent rule-based engineering — no proprietary ML platform required. The 13-factor scoring model, the cost-aware priority formula, and the advisor grounding mechanism are all fully auditable by a non-specialist.

The goal for the hackathon is to demonstrate what the data fusion layer looks like in practice and to show that the safety constraints (advisory-only, engineer sign-off required) can be enforced at the data layer rather than relying on UI guidelines.

---

*GridShield Problem Statement · IBM Bob AI Hackathon 2026*
