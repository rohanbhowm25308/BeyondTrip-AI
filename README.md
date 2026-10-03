#  BeyondTrip AI

### **Plan past the obvious. Travel smarter. Discover what others miss.**

> **BeyondTrip AI** is an AI-powered group travel optimization platform that helps travelers make smarter decisions by comparing travel modes, calculating the **true cost of a trip**, understanding group preferences, discovering hidden gems, and providing **trip-aware AI recommendations**.
> 
---

### Project Links

🚀 Live Demo

https://beyondtrip-ai.onrender.com

💻 GitHub Repository

https://github.com/rohanbhowm25308/BeyondTrip-AI

---

##  Why BeyondTrip?

Planning a group trip is rarely just:

**“Which transport is cheapest?”**

A real decision involves:

*  Budget
*  Travel time
*  Comfort
*  Different preferences within the group
*  Food
*  Shopping
*  Accommodation
*  Local transportation
*  Activities
*  Places worth discovering
*  Tourist traps
*  Unexpected delays or changes

**BeyondTrip brings these factors together into one intelligent travel decision engine.**

Instead of simply showing options, it answers:

> **“What makes the most sense for our entire group?”**

---

## ✨ What Makes BeyondTrip Different?

###  AI-Powered Travel Decisions

BeyondTrip evaluates multiple travel modes and produces an explainable recommendation instead of simply displaying a list of prices.

Each option receives an **AI Score** based on factors such as:

* Trade-off preferences
* Budget fit
* Group-priority alignment
* Comfort
* Travel time
* Full-trip expenditure

This makes the recommendation transparent rather than a black box.

---

#  Core Features

##  Multi-Modal Travel Optimizer

Compare:

*  Car
*  Bus
*  Train
*  Flight

The system evaluates each option using travel time, cost, comfort, group preferences, and the user's selected trade-offs.

---

##  True Trip Cost Engine

BeyondTrip goes beyond the ticket price.

### Total trip expenditure can include:

```text
Transportation
+ Accommodation
+ Food
+ Local Transport
+ Activities
+ Shopping
+ Emergency Buffer
--------------------------------
= True Trip Cost
```

This gives travelers a more realistic picture of what their trip will actually cost.

---

##  Group Consensus Engine

Different travelers want different things.

One person may prioritize:

>  Budget

Another:

>  Photography

Another:

>  Comfort

BeyondTrip combines these preferences and determines how well each travel option satisfies the group.

The result is a recommendation designed around **group consensus rather than a single traveler**.

---

##  Hidden Gem Discovery

Why visit only the places everyone already knows?

BeyondTrip discovers lesser-known destinations based on:

* Group interests
* Budget
* Distance
* Crowd level
* Experience
* Discovery preferences

Each hidden gem receives a confidence/match score with an explainable factor breakdown.

---

##  Destination Zones

Instead of showing one huge attraction list, BeyondTrip divides destinations into meaningful zones based on what they offer.

Examples:

*  Photography
*  History
*  Food
*  Shopping
*  Adventure

This makes destination exploration more personalized.

---

##  Tourist Trap Detector

Popular does not always mean better value.

BeyondTrip compares popular attractions with nearby alternatives and shows:

*  Ratings
*  Cost difference
*  Alternative experience
*  Exact potential savings

Helping travelers discover when a lesser-known option may provide better value.

---

#  AI-Powered Intelligence

##  BeyondTrip AI Briefing

After generating a plan, BeyondTrip provides a concise explanation of:

**Why it won**

**What drove the decision**

**What you sacrifice**

**What you gain**

**What to do next**

The system can use Groq for natural-language generation while maintaining a deterministic fallback so the core travel planner remains functional.

---

##  Trip-Aware AI Chatbot

Unlike a generic chatbot, the BeyondTrip assistant receives the **current trip context**.

Its context can include:

```text
Trip Details
      ↓
Recommended Transport
      ↓
All Transport Options
      ↓
Budget & Expenses
      ↓
Group Preferences
      ↓
Group Consensus
      ↓
Hidden Gems
      ↓
Itinerary
      ↓
Tourist Traps
      ↓
Trade-Off Sliders
      ↓
BeyondTrip Score
```

This allows conversations such as:

> **User:** Why did you recommend train?

> **AI:** Train provides the strongest balance between your group's budget, comfort preferences and travel time.

Then:

> **User:** What if we have ₹5,000 more?

The assistant can reason using the **same active trip context** instead of starting from scratch.

---

#  Intelligent Trip Simulator

BeyondTrip includes live trade-off controls:

### Budget ↔ Comfort

Choose between saving money and increasing comfort.

### Savings ↔ Speed

Decide whether time or cost matters more.

### Popular ↔ Hidden

Control how adventurous your destination discovery should be.

### Activities ↔ Shopping

Shift the trip budget between experiences and shopping.

The recommendation and hidden-gem rankings update accordingly.

---

#  What-If Planning

Explore alternative scenarios instantly.

### Example:

**+₹5,000 Budget**

See how the recommendation changes.

**No Flights**

Recalculate without flights.

**+₹5,000 Shopping**

Rebalance the trip.

**Need It 2 Hours Faster**

Prioritize speed.

The simulator shows the **Before → After** impact on the trip.

---

#  Budget Negotiator AI

BeyondTrip automatically distributes the available budget across:

* Transportation
* Accommodation
* Food
* Activities
* Shopping
* Emergency buffer

If the group wants more spending in one category, the system can rebalance the remaining budget.

---

#  Crowd-Aware Itinerary

BeyondTrip considers crowd patterns while building the itinerary.

For example:

```text
 Morning
Hidden Gem
↓
 Afternoon
Food / Local Experience
↓
 Evening
Popular Attraction
```

Hidden locations can be scheduled during quieter periods while popular attractions are pushed toward more suitable times.

---

#  Last-Minute Replanner

Plans can change.

Simulate a delay and BeyondTrip can adjust the itinerary.

For larger delays, the system can remove a high-crowd stop and explain the change.

---

#  Group Packing & Preparation

Generate a group-oriented preparation list based on:

* Trip duration
* Interests
* Destination activities

Items can be distributed across travelers so one person doesn't end up carrying everything.

---

#  Per-Person Expense Balancer

Enter how much each traveler has already spent.

BeyondTrip calculates a simplified settlement showing:

```text
Who owes whom
        ↓
How much
        ↓
Fewest practical transactions
```

Making group expense settlement easier after the trip.

---

#  BeyondTrip Score

The recommended plan receives a **0–100 BeyondTrip Score** based on multiple dimensions, including:

| Factor                  | What it represents                  |
| ----------------------- | ----------------------------------- |
|  Budget Fit           | How well the option fits the budget |
|  Time Efficiency      | Travel-time suitability             |
|  Group Satisfaction   | Preference alignment                |
|  Comfort             | Comfort level                       |
|  Experience           | Overall experience potential        |
|  Hidden-Gem Potential | Discovery opportunities             |

The score is designed to be **explainable**, not just a number.

---

#  How BeyondTrip Works

```text
              USER INPUT
                  │
                  ▼
        ┌──────────────────┐
        │ Trip Information │
        │ Budget / Group   │
        │ Interests / Days │
        └────────┬─────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │ Travel Mode Engine  │
       │ Car / Bus / Train   │
       │ Flight              │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ True Cost Engine    │
       │ Stay + Food + Local │
       │ Activities + Buffer │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ Group Intelligence  │
       │ Preferences +       │
       │ Consensus           │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ AI Recommendation   │
       │ Score + Explanation │
       └──────────┬──────────┘
                  │
          ┌───────┴────────┐
          ▼                ▼
   Hidden Gems        AI Assistant
   Itinerary          Trip-Aware Chat
   What-If            Replanning
```

---

#  Tech Stack

### Backend

*  Python
*  Flask
*  Groq API
*  Rule-based optimization engine

### Frontend

* HTML5
* CSS3
* JavaScript
* Responsive UI
* Interactive sliders
* Animated particle/network background

### Deployment

*  Render
*  GitHub
*  Gunicorn

---

#  Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/rohanbhowm25308/BeyondTrip-AI.git
cd BeyondTrip-AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file based on `.env.example`.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_model_name
```

Keep your real API key private and **never commit `.env` to GitHub**.

### 6. Run the application

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

#  Deployment on Render

BeyondTrip includes a `Procfile` configured for Gunicorn.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

Add the required environment variables in Render:

```text
GROQ_API_KEY
GROQ_MODEL
```

---

#  Current Data Architecture

The current hackathon version uses **seeded/rule-based travel and destination data** for the core calculations.

The richest demonstration dataset is currently based around:

**Delhi → Jaipur · 5 travelers · ₹30,000**

Other destinations use a generic populated fallback dataset.

The architecture can later be connected to live services such as:

* Maps / routing APIs
* Railway APIs
* Bus APIs
* Airline APIs
* Hotel APIs
* Live weather/crowd data

This would allow BeyondTrip to move from a hackathon optimization engine toward a production-grade travel intelligence platform.

---

# 👨‍💻 Developer

### **Rohan Bhowmik**

B.Tech CSE Student | AI/ML & Generative AI Enthusiast

Building intelligent applications around:

**Artificial Intelligence • Machine Learning • Generative AI • Agentic AI • Data Science • Python • Web Development**

---

<p align="center">

###  BeyondTrip AI

**Plan past the obvious.**

⭐ If you find this project interesting, consider giving the repository a star!

</p>
