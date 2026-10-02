# BeyondTrip

AI-powered group travel optimizer + hidden gems discovery. Built for a hackathon demo.

## Core features
- Multi-modal comparison (car/bus/train/flight) with an explainable, continuously-adjustable score
- True trip cost engine (travel + hotel + food + local transport + activities + shopping + 5% buffer)
- Hidden-gem discovery scored against the group's interests, with a dynamic search radius
- Destination split into themed zones instead of one flat attraction list
- Tourist trap detector with star ratings and an exact ₹ savings figure
- A Groq-powered chat assistant for free-form trip questions

## New: 10 group-intelligence features
1. **Group Consensus Engine** — each traveler's top priority is checked against the recommended
   mode; shows "Train satisfies 4/5 travelers' highest-priority preferences."
2. **Budget Negotiator AI** — auto-splits the total budget into transport/stay/food/activities/
   shopping/emergency, then rebalances when you ask for more in one category (or grows the total).
3. **Trip Trade-Off Simulator** — four live sliders (Budget↔Comfort, Savings↔Speed, Popular↔Hidden,
   Activities↔Shopping) that recompute the recommendation and gem ranking in real time.
4. **Hidden Gem Confidence Score** — every gem shows a factor breakdown (interest match, budget
   match, crowd level, distance, experience), not just a single number.
5. **Tourist Trap Detector** — unchanged core idea, now with ★ ratings on both sides and an exact
   rupee-savings line.
6. **Crowd-Aware Itinerary** — hidden gems scheduled at their quiet early-morning time, popular
   attractions pushed to late afternoon to dodge peak crowds.
7. **Dynamic Radius Discovery** — a 5 / 10 / 20 km selector that re-scores and, if too few gems
   fall inside a tight radius, says so and shows the closest ones anyway.
8. **Last-Minute Replanner** — simulate a delay (minutes) and the itinerary shifts Day 1's times;
   past 2 hours it also drops the highest-crowd stop and explains why.
9. **Group Packing & Prep AI** — a packing list generated from the chosen interests and trip
   length, round-robin assigned across the named travelers.
10. **Per-Person Expense Balancer** — enter what each traveler has already spent and get a
    settlement: who owes whom, simplified to the fewest transactions.

## New: judge-facing upgrades
- **AI Decision Summary (top of results)** — one glance tells you the recommended mode, total /
  per-person cost, hours, how far under/over budget, why it won, what you sacrifice, what you
  gain, and the best alternative with its exact trade-off — no scrolling required.
- **BeyondTrip Score (0–100)** — a composite score ring with a visible, explainable breakdown:
  budget fit, time efficiency, group satisfaction, comfort, experience, and hidden-gem potential.
- **Hidden gems with group-match %** — each gem now shows "Why your group: x/y travelers prefer
  photography/history," tying the score directly to the people you've added.
- **"What Changed?" simulator** — one-click presets (+₹5,000 budget, no flight, +₹5,000 shopping,
  "we need it 2h faster") show an instant before → after: mode, total, per-person, comfort, hidden
  gems shown, and BeyondTrip Score.
- **Group Preference Map** — an emoji grid of every traveler's priorities, with an "↓ AI CONSENSUS
  ↓" arrow into the recommended mode and its group-satisfaction percentage — built for a live demo.
- **Trip-aware chatbot** — the assistant is handed the live decision summary and trip score as
  context on every message, so it answers from the actual current plan instead of acting like a
  generic, disconnected chatbot.

## New: AI recommendation engine v2
- **Per-mode AI Score** — every travel mode (not just the winner) now gets a transparent 0–100
  AI Score built from five weighted components: its trade-off score (cost/time/comfort from the
  sliders), full-trip budget fit, group-priority alignment, comfort, and travel time. Each mode
  card shows the score ring plus the breakdown (Budget Fit, Group Alignment, Full Trip Cost, Cost
  Per Person) so the pick is explainable, not a black box.
- **BeyondTrip AI Briefing** — a panel right under the decision summary that explains, in four
  short parts, why the mode was picked, what factors drove it, the main trade-off, and a practical
  next action. Uses Groq when a key is configured; otherwise falls back to a deterministic briefing
  built straight from the AI Score breakdown — this panel never shows an error or breaks.
- **Chatbot v2** — every message now carries a fully structured context (trip details →
  recommendation → all transport options → budget/expense → group preferences → consensus →
  hidden gems → itinerary → tourist traps → sliders → trip score) plus the last few conversation
  turns, so "why train?" followed by "what if we have ₹5,000 more?" is handled as one continuous
  conversation. Without a Groq key, a rule-based fallback still answers from the live trip data
  instead of refusing.

## Run it locally

```bash
cd beyondtrip
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env already exists with a placeholder — open it and paste your real Groq key
# (get one free at https://console.groq.com/keys)

python app.py
```

Open http://localhost:5000 — hard refresh (Ctrl+Shift+R) the first time so the browser doesn't
reuse a cached, unstyled version.

Everything except the free-form chat assistant is pure Python logic with no external API calls,
so the demo never breaks on stage even with no internet. Add the Groq key only to light up chat.

## Deploying on Render

This repo already includes what Render needs:
- `Procfile` → `web: gunicorn app:app`
- `requirements.txt` includes `gunicorn`
- `app.py` reads the `PORT` environment variable Render provides

On render.com: **New → Web Service** → connect the GitHub repo → Build command
`pip install -r requirements.txt` → Start command `gunicorn app:app`. Add `GROQ_API_KEY` and
`GROQ_MODEL` as environment variables in the Render dashboard — never commit your real key to
GitHub (`.gitignore` already excludes `.env`).

## Project structure

```
beyondtrip/
├── app.py                 # Flask app + every feature's logic + Groq chat endpoint
├── requirements.txt
├── Procfile                # for Render
├── .gitignore
├── .env                     # put your real Groq key here (not committed)
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/
        ├── particles.js    # animated network background
        └── app.js          # form handling, rendering, sliders, negotiator, replanner, etc.
```

## Notes for the demo
- The mock data set is richest for **Jaipur** (matches Delhi → Jaipur, 5 people, ₹30,000). Any
  other destination falls back to a generic but still-populated data set.
- Distance, ticket costs, and gem data are rule-based seed values — wire in Google Maps Distance
  Matrix / IRCTC / RedBus / airline APIs in `compute_modes()` and `DESTINATIONS` for live numbers.
