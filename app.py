"""
BeyondTrip — AI-Powered Group Travel Optimizer & Hidden Gems Discovery
Flask backend
"""
import os
import json
import copy
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ---------------------------------------------------------------------------
# Mock knowledge base.
# ---------------------------------------------------------------------------

BASE_MODES = {
    "car":    {"label": "Car",    "speed_kmph": 55,  "cost_per_km_group": 11, "comfort": 3, "meal_cost_pp": 250},
    "bus":    {"label": "Bus",    "speed_kmph": 48,  "cost_per_km_group": 7,  "comfort": 2, "meal_cost_pp": 250},
    "train":  {"label": "Train",  "speed_kmph": 62,  "cost_per_km_group": 8,  "comfort": 3, "meal_cost_pp": 250},
    "flight": {"label": "Flight", "speed_kmph": 480, "cost_per_km_group": 55, "comfort": 5, "meal_cost_pp": 150},
}

DESTINATIONS = {
    "jaipur": {
        "distance_km": 280,
        "zones": [
            {"name": "Heritage Quarter", "theme": "Forts, hidden viewpoints, local thalis",
             "tags": ["history", "photography", "food"]},
            {"name": "Local Culture Lane", "theme": "Artisan markets, cafés, budget shopping",
             "tags": ["shopping", "food"]},
            {"name": "Nature Fringe", "theme": "Viewpoints, quiet trails, golden-hour spots",
             "tags": ["photography", "adventure"]},
        ],
        "gems": [
            {"name": "Nahargarh Backwall Viewpoint", "distance_km": 8, "cost_pp": 50,
             "crowd": 2, "best_time": "6:30 AM", "tags": {"photography": 5, "history": 3, "food": 1, "shopping": 1},
             "why": "a quiet ledge above the city with almost none of the crowd the main fort gets"},
            {"name": "Sireh Deori Bazaar Food Row", "distance_km": 5, "cost_pp": 200,
             "crowd": 3, "best_time": "7:00 PM", "tags": {"photography": 2, "history": 2, "food": 5, "shopping": 3},
             "why": "where locals actually eat, not the tourist-facing stalls near the palace"},
            {"name": "Panna Meena ka Kund (early morning)", "distance_km": 12, "cost_pp": 30,
             "crowd": 2, "best_time": "6:00 AM", "tags": {"photography": 5, "history": 4, "food": 1, "shopping": 1},
             "why": "a stepwell that's an Instagram staple by 10am but empty and free to feel at dawn"},
            {"name": "Johari Bazaar Back Lanes", "distance_km": 3, "cost_pp": 0,
             "crowd": 2, "best_time": "11:00 AM", "tags": {"photography": 2, "history": 2, "food": 3, "shopping": 5},
             "why": "the workshops behind the main jewellery street where the actual making happens"},
        ],
        "tourist_traps": [
            {"popular": "Chokhi Dhani (peak season)", "popular_cost": 1200, "popular_rating": 4.0,
             "alternative": "Local village-stay dinner near Chandwaji", "alt_cost": 250, "alt_rating": 4.5,
             "alt_distance_km": 22, "note": "same folk-culture experience, a fraction of the price, far fewer buses of tourists"},
            {"popular": "Hawa Mahal front-row photo stalls", "popular_cost": 300, "popular_rating": 3.8,
             "alternative": "Tattoo Café rooftop across the road", "alt_cost": 150, "alt_rating": 4.4,
             "alt_distance_km": 0.1, "note": "the same iconic shot, a coffee instead of a queue"},
        ],
    },
}

GENERIC_DESTINATION = {
    "distance_km": 300,
    "zones": [
        {"name": "Old Town Core", "theme": "History, architecture, local street food",
         "tags": ["history", "photography", "food"]},
        {"name": "Market District", "theme": "Artisan shops, cafés, bazaars",
         "tags": ["shopping", "food"]},
        {"name": "Green Belt", "theme": "Parks, viewpoints, quieter trails",
         "tags": ["photography", "adventure"]},
    ],
    "gems": [
        {"name": "Unmarked hilltop viewpoint", "distance_km": 9, "cost_pp": 0,
         "crowd": 2, "best_time": "6:30 AM", "tags": {"photography": 5, "history": 2, "food": 1, "shopping": 1},
         "why": "locals go, tour buses don't"},
        {"name": "Back-street food lane", "distance_km": 4, "cost_pp": 180,
         "crowd": 3, "best_time": "7:30 PM", "tags": {"photography": 2, "history": 2, "food": 5, "shopping": 2},
         "why": "the food stretch that never makes the top-10 blog lists"},
        {"name": "Old quarter workshop row", "distance_km": 6, "cost_pp": 20,
         "crowd": 2, "best_time": "11:00 AM", "tags": {"photography": 3, "history": 5, "food": 1, "shopping": 4},
         "why": "watch the craft actually get made, not just sold"},
    ],
    "tourist_traps": [
        {"popular": "The headline landmark's front-gate vendors", "popular_cost": 800, "popular_rating": 3.9,
         "alternative": "Side-street version 2km away", "alt_cost": 200, "alt_rating": 4.3,
         "alt_distance_km": 2, "note": "near-identical experience, far less footfall"},
    ],
}


def get_destination(name: str):
    key = (name or "").strip().lower()
    return DESTINATIONS.get(key, GENERIC_DESTINATION)


PRIORITY_KEYS = ["budget", "comfort", "food", "shopping", "adventure", "photography", "history"]
GEM_TAG_KEYS = ["photography", "history", "food", "shopping", "adventure"]
WEIGHT_MAP = {"low": 1, "medium": 2, "high": 3}
CATEGORY_EMOJI = {"budget": "💰", "comfort": "🛋️", "food": "🍜", "shopping": "🛍️",
                  "adventure": "⚡", "photography": "📸", "history": "🏛️"}
CATEGORY_TO_MODE_ATTR = {
    "budget": "cost_score", "food": "cost_score", "shopping": "cost_score",
    "comfort": "comfort_score",
    "adventure": "time_score", "photography": "time_score", "history": "time_score",
}


# ---------------------------------------------------------------------------
# 1. Multi-modal comparison + Trip Trade-Off Simulator (continuous sliders)
# ---------------------------------------------------------------------------

def compute_modes(distance_km, travelers, food_budget_pp, local_transport_total, sliders):
    bc = sliders.get("budget_comfort", 50)
    ss = sliders.get("speed_savings", 50)

    raw_cost = (100 - bc) + (100 - ss)
    raw_time = ss
    raw_comfort = bc
    raw_sum = max(raw_cost + raw_time + raw_comfort, 1)
    w_cost, w_time, w_comfort = raw_cost / raw_sum, raw_time / raw_sum, raw_comfort / raw_sum

    options = {}
    for key, m in BASE_MODES.items():
        hours = round(distance_km / m["speed_kmph"], 1)
        travel_cost = round(distance_km * m["cost_per_km_group"])
        meals_needed = 1 if hours > 4 else 0
        food_cost = food_budget_pp * travelers if food_budget_pp else m["meal_cost_pp"] * travelers * meals_needed
        total = travel_cost + food_cost + local_transport_total
        options[key] = {
            "label": m["label"], "hours": hours, "travel_cost": travel_cost,
            "food_cost": round(food_cost), "local_transport": local_transport_total,
            "comfort": m["comfort"], "total": round(total),
        }

    costs = [o["total"] for o in options.values()]
    times = [o["hours"] for o in options.values()]
    min_c, max_c = min(costs), max(costs)
    min_t, max_t = min(times), max(times)

    for key, o in options.items():
        cost_score = 1 - ((o["total"] - min_c) / (max_c - min_c) if max_c > min_c else 0)
        time_score = 1 - ((o["hours"] - min_t) / (max_t - min_t) if max_t > min_t else 0)
        comfort_score = o["comfort"] / 5
        o["cost_score"], o["time_score"], o["comfort_score"] = round(cost_score, 3), round(time_score, 3), round(comfort_score, 3)
        o["score"] = round((cost_score * w_cost + time_score * w_time + comfort_score * w_comfort) * 100)

    best_overall = max(options, key=lambda k: options[k]["score"])
    budget_winner = min(options, key=lambda k: options[k]["total"])
    fastest = min(options, key=lambda k: options[k]["hours"])
    best_for_group = max(options, key=lambda k: (options[k]["comfort"], -options[k]["total"] / max(travelers, 1)))

    flight_total = options["flight"]["total"]
    bus_hours = options["bus"]["hours"]
    best = options[best_overall]
    explanation = (
        f"Saves ₹{flight_total - best['total']:,} compared with flight" if best_overall != "flight" else
        f"Cuts travel time to {best['hours']}h — the fastest way to get the group there"
    )
    if best_overall != "flight":
        diff = abs(round(bus_hours - best["hours"], 1))
        explanation += f" while taking {diff}h {'less' if best['hours'] < bus_hours else 'more'} than the bus."

    return {
        "options": options, "best_overall": best_overall, "budget_winner": budget_winner,
        "fastest": fastest, "best_for_group": best_for_group, "explanation": explanation,
        "weights": {"cost": round(w_cost, 2), "time": round(w_time, 2), "comfort": round(w_comfort, 2)},
    }


def compute_expense_engine(travelers, days, mode_total_cost, food_budget_pp, shopping_budget_pp,
                            local_transport_total, hotel_cost_pn_pp, sliders):
    sa = sliders.get("shopping_activities", 50)
    travel = mode_total_cost
    hotel = hotel_cost_pn_pp * travelers * max(days - 1, 1)
    food = food_budget_pp * travelers * days
    local_transport = local_transport_total
    combined_pool = 300 * travelers * days + shopping_budget_pp * travelers
    shopping = round(combined_pool * (sa / 100))
    activities = combined_pool - shopping
    subtotal = travel + hotel + food + local_transport + activities + shopping
    buffer = round(subtotal * 0.05)
    total = subtotal + buffer
    return {
        "travel": round(travel), "hotel": round(hotel), "food": round(food),
        "local_transport": round(local_transport), "activities": round(activities),
        "shopping": round(shopping), "buffer": buffer, "total": round(total),
        "per_person": round(total / max(travelers, 1)),
    }


# ---------------------------------------------------------------------------
# AI Recommendation Engine — per-mode AI Score
#
# Each mode is scored on five explainable components: its existing travel
# trade-off score (cost/time/comfort from the sliders), how well its FULL
# trip cost (not just the ticket) fits the stated budget, how well it aligns
# with what the group actually prioritized, comfort, and travel time. The
# mode with the highest AI Score becomes the recommendation.
# ---------------------------------------------------------------------------

AI_SCORE_WEIGHTS = {
    "trade_off": 0.25, "budget_fit": 0.25, "group_alignment": 0.25,
    "comfort": 0.10, "time_efficiency": 0.15,
}


def _budget_fit_score(full_trip_total, total_budget, fallback_cost_score):
    if total_budget <= 0:
        return round(fallback_cost_score * 100)
    ratio = full_trip_total / total_budget
    if ratio <= 1:
        return round(100 - (1 - ratio) * 40)
    return round(max(0, 100 - (ratio - 1) * 150))


def _mode_group_alignment(people, mode_options, mode):
    """Same logic as the Group Consensus Engine, but for an arbitrary candidate
    mode rather than only the one already chosen — lets every mode be scored
    on group fit, not just the slider-based winner."""
    if not people:
        return None
    satisfied, considered = 0, 0
    for p in people:
        levels = {k: WEIGHT_MAP.get((p.get(k) or "").lower(), 0) for k in PRIORITY_KEYS if k in CATEGORY_TO_MODE_ATTR}
        if not any(levels.values()):
            continue
        top_cat = max(levels, key=lambda k: levels[k])
        considered += 1
        attr = CATEGORY_TO_MODE_ATTR[top_cat]
        scores = {m: o[attr] for m, o in mode_options.items()}
        max_score = max(scores.values()) if scores else 0
        chosen_score = scores.get(mode, 0)
        if max_score <= 0 or chosen_score >= 0.85 * max_score:
            satisfied += 1
    if considered == 0:
        return None
    return round(satisfied / considered * 100)


def compute_ai_scores(modes, travelers, days, food_budget_pp, shopping_budget_pp,
                       local_transport_total, hotel_cost_pn_pp, sliders, people, total_budget):
    """Scores every surviving mode, attaches the breakdown to each option, and
    sets modes['best_overall'] to the highest AI Score. Returns the full
    (whole-trip, not just travel) expense dict for every mode so the caller
    can reuse the chosen mode's numbers without recomputing them."""
    full_trip_by_mode = {}
    for key, o in modes["options"].items():
        full_trip_by_mode[key] = compute_expense_engine(
            travelers, days, o["travel_cost"], food_budget_pp, shopping_budget_pp,
            local_transport_total, hotel_cost_pn_pp, sliders,
        )

    for key, o in modes["options"].items():
        full = full_trip_by_mode[key]
        budget_fit = _budget_fit_score(full["total"], total_budget, o["cost_score"])
        alignment = _mode_group_alignment(people, modes["options"], key)
        if alignment is None:
            alignment = round(o["score"])  # neutral fallback: no travelers added yet
        comfort_pct = round(o["comfort_score"] * 100)
        time_pct = round(o["time_score"] * 100)
        trade_off = round(o["score"])
        ai_score = round(
            trade_off * AI_SCORE_WEIGHTS["trade_off"] + budget_fit * AI_SCORE_WEIGHTS["budget_fit"] +
            alignment * AI_SCORE_WEIGHTS["group_alignment"] + comfort_pct * AI_SCORE_WEIGHTS["comfort"] +
            time_pct * AI_SCORE_WEIGHTS["time_efficiency"]
        )
        o.update({
            "ai_score": ai_score, "trade_off_score": trade_off, "budget_fit": budget_fit,
            "group_alignment": alignment, "full_trip_cost": full["total"], "cost_per_person": full["per_person"],
        })

    if modes["options"]:
        modes["best_overall"] = max(modes["options"], key=lambda k: modes["options"][k]["ai_score"])
    modes["ai_score_weights"] = AI_SCORE_WEIGHTS

    best = modes["options"][modes["best_overall"]]
    flight_total = modes["options"].get("flight", {}).get("total", best["total"])
    bus_hours = modes["options"].get("bus", {}).get("hours", best["hours"])
    explanation = (
        f"Saves ₹{flight_total - best['total']:,} compared with flight" if modes["best_overall"] != "flight" else
        f"Cuts travel time to {best['hours']}h — the fastest way to get the group there"
    )
    if modes["best_overall"] != "flight" and "bus" in modes["options"]:
        diff = abs(round(bus_hours - best["hours"], 1))
        explanation += f" while taking {diff}h {'less' if best['hours'] < bus_hours else 'more'} than the bus."
    explanation += (f" It also wins on AI Score ({best['ai_score']}/100) — the best overall blend of trade-off fit, "
                     f"budget fit, group alignment, comfort, and travel time.")
    modes["explanation"] = explanation

    return full_trip_by_mode


# ---------------------------------------------------------------------------
# Hidden Gem Confidence Score + Dynamic Radius + Group Match
# ---------------------------------------------------------------------------

def score_hidden_gems(gems, interests, radius_km, popular_hidden):
    interests = interests or ["photography", "history", "food", "shopping"]
    ph = popular_hidden / 100.0
    in_radius = [g for g in gems if g["distance_km"] <= radius_km]
    pool = in_radius if in_radius else gems
    expanded = len(in_radius) < len(gems) and radius_km < 20

    interest_w = 0.55 - 0.15 * ph
    crowd_w = 0.15 + 0.25 * ph
    cost_w = 0.2
    dist_w = 1 - interest_w - crowd_w - cost_w

    scored = []
    for g in pool:
        tag_scores = g["tags"]
        relevant = [tag_scores.get(i, 1) for i in interests] or [1]
        interest_score = sum(relevant) / (len(relevant) * 5)
        crowd_score = (5 - g["crowd"]) / 5
        cost_score = max(0, 1 - g["cost_pp"] / 500)
        distance_score = max(0, 1 - g["distance_km"] / max(radius_km, 1))
        final = round((interest_score * interest_w + crowd_score * crowd_w +
                        cost_score * cost_w + distance_score * dist_w) * 100)
        factors = {
            "group_interest_match": round(interest_score * 100),
            "budget_match": round(cost_score * 100),
            "distance": round(distance_score * 100),
            "crowd_level": round(crowd_score * 100),
            "experience": round(((interest_score + crowd_score + cost_score) / 3) * 100),
        }
        scored.append({**g, "discovery_score": final, "factors": factors})

    return sorted(scored, key=lambda x: -x["discovery_score"]), expanded, len(in_radius)


def attach_group_match(gems, people):
    top_cats = []
    for p in people:
        levels = {c: WEIGHT_MAP.get((p.get(c) or "").lower(), 0) for c in GEM_TAG_KEYS}
        if any(levels.values()):
            top_cats.append(max(levels, key=lambda c: levels[c]))
    n = len(top_cats)
    for g in gems:
        top_tags = sorted(g["tags"], key=lambda t: -g["tags"][t])[:2]
        g["group_match"] = (
            {"count": sum(1 for c in top_cats if c in top_tags), "of": n, "tags": top_tags}
            if n > 0 else None
        )
    return gems


# ---------------------------------------------------------------------------
# Group Consensus Engine + Group Preference Map
# ---------------------------------------------------------------------------

def compute_group_consensus(people, mode_options, chosen_mode):
    if not people:
        return None
    satisfied, considered, details = 0, 0, []
    for p in people:
        name = p.get("name") or "Traveler"
        levels = {k: WEIGHT_MAP.get((p.get(k) or "").lower(), 0) for k in PRIORITY_KEYS if k in CATEGORY_TO_MODE_ATTR}
        if not any(levels.values()):
            continue
        top_cat = max(levels, key=lambda k: levels[k])
        considered += 1
        attr = CATEGORY_TO_MODE_ATTR[top_cat]
        scores = {m: o[attr] for m, o in mode_options.items()}
        max_score = max(scores.values()) if scores else 0
        chosen_score = scores.get(chosen_mode, 0)
        ok = max_score <= 0 or chosen_score >= 0.85 * max_score
        if ok:
            satisfied += 1
        details.append({"name": name, "top_priority": top_cat, "satisfied": ok})
    if considered == 0:
        return None
    pct = round(satisfied / considered * 100)
    return {
        "score": pct, "satisfied": satisfied, "considered": considered, "details": details,
        "explanation": f"{BASE_MODES[chosen_mode]['label']} was selected because it satisfies "
                        f"{satisfied}/{considered} travelers' highest-priority preferences.",
    }


def aggregate_group_preferences(people):
    keys = PRIORITY_KEYS
    totals = {k: 0 for k in keys}
    max_possible = {k: 0 for k in keys}
    for person in people:
        for k in keys:
            v = WEIGHT_MAP.get((person.get(k) or "").lower(), 0)
            totals[k] += v
            max_possible[k] += 3
    return {k: round((totals[k] / max_possible[k]) * 100) if max_possible[k] else 0 for k in keys}


def build_preference_map(people):
    rows = []
    for p in people:
        cells = []
        for cat in PRIORITY_KEYS:
            lvl = WEIGHT_MAP.get((p.get(cat) or "").lower(), 0)
            if lvl > 0:
                cells.append({"category": cat, "emoji": CATEGORY_EMOJI.get(cat, ""), "count": lvl})
        rows.append({"name": p.get("name") or "Traveler", "cells": cells})
    return rows


# ---------------------------------------------------------------------------
# Trip Score (explainable composite)
# ---------------------------------------------------------------------------

TRIP_SCORE_WEIGHTS = {
    "budget_fit": 0.20, "time_efficiency": 0.15, "group_satisfaction": 0.25,
    "comfort": 0.15, "experience": 0.10, "hidden_gem_potential": 0.15,
}


def compute_trip_score(modes, chosen_mode, consensus, gems, total_budget, expense_total):
    # Reuses the AI Score engine's already-computed per-mode fields (budget_fit,
    # group_alignment) so the Trip Score and the AI Score panel never disagree
    # on what "budget fit" or "group alignment" means for this mode.
    opt = modes["options"][chosen_mode]
    time_efficiency = round(opt["time_score"] * 100)
    comfort = round(opt["comfort_score"] * 100)
    budget_fit = opt.get("budget_fit")
    if budget_fit is None:
        budget_fit = _budget_fit_score(expense_total, total_budget, opt["cost_score"])

    group_satisfaction = consensus["score"] if consensus else opt.get("group_alignment", round(opt["score"]))

    if gems:
        experience = round(sum(g["factors"]["experience"] for g in gems) / len(gems))
        hidden_gem_potential = round(sum(g["discovery_score"] for g in gems) / len(gems))
    else:
        experience = 0
        hidden_gem_potential = 0

    factors = {
        "budget_fit": max(0, min(100, budget_fit)),
        "time_efficiency": time_efficiency,
        "group_satisfaction": group_satisfaction,
        "comfort": comfort,
        "experience": experience,
        "hidden_gem_potential": hidden_gem_potential,
    }
    overall = round(sum(factors[k] * w for k, w in TRIP_SCORE_WEIGHTS.items()))
    return {"overall": overall, "factors": factors, "weights": TRIP_SCORE_WEIGHTS}


# ---------------------------------------------------------------------------
# AI Decision Summary
# ---------------------------------------------------------------------------

def compute_decision_summary(modes, chosen_mode, expense, total_budget, travelers, consensus):
    opt = modes["options"][chosen_mode]
    others = {k: v for k, v in modes["options"].items() if k != chosen_mode}

    sacrifices, gains = [], []
    fastest_key, cheapest_key = modes.get("fastest"), modes.get("budget_winner")
    if fastest_key and fastest_key != chosen_mode and fastest_key in modes["options"]:
        diff_h = round(opt["hours"] - modes["options"][fastest_key]["hours"], 1)
        if diff_h > 0:
            sacrifices.append(f"{diff_h}h slower than {BASE_MODES[fastest_key]['label']}")
    if cheapest_key and cheapest_key != chosen_mode and cheapest_key in modes["options"]:
        diff_c = opt["total"] - modes["options"][cheapest_key]["total"]
        if diff_c > 0:
            sacrifices.append(f"₹{diff_c:,} pricier than {BASE_MODES[cheapest_key]['label']}")

    if modes["options"]:
        most_expensive_key = max(modes["options"], key=lambda k: modes["options"][k]["total"])
        if most_expensive_key != chosen_mode:
            save = modes["options"][most_expensive_key]["total"] - opt["total"]
            if save > 0:
                gains.append(f"₹{save:,} cheaper than {BASE_MODES[most_expensive_key]['label']}")
        slowest_key = max(modes["options"], key=lambda k: modes["options"][k]["hours"])
        if slowest_key != chosen_mode:
            timesave = round(modes["options"][slowest_key]["hours"] - opt["hours"], 1)
            if timesave > 0:
                gains.append(f"{timesave}h faster than {BASE_MODES[slowest_key]['label']}")
    gains.append(f"Comfort level {opt['comfort']}/5")

    alternative = None
    if others:
        alt_key = max(others, key=lambda k: others[k]["score"])
        alt = modes["options"][alt_key]
        cost_diff = alt["total"] - opt["total"]
        time_diff = round(alt["hours"] - opt["hours"], 1)
        alternative = {
            "mode": alt_key, "label": BASE_MODES[alt_key]["label"],
            "total": alt["total"], "hours": alt["hours"],
            "tradeoff": (f"{BASE_MODES[alt_key]['label']} costs ₹{abs(cost_diff):,} "
                         f"{'more' if cost_diff > 0 else 'less'} and takes {abs(time_diff)}h "
                         f"{'more' if time_diff > 0 else 'less'}."),
        }

    budget_delta = (total_budget - expense["total"]) if total_budget > 0 else None
    match_line = f"Best match for {travelers} travelers based on budget, comfort, and interests."
    if consensus:
        match_line = (f"Best match for {travelers} travelers — satisfies "
                       f"{consensus['satisfied']}/{consensus['considered']} top group priorities.")

    return {
        "headline": f"Recommended for your group: {BASE_MODES[chosen_mode]['label']}",
        "metrics_line": f"₹{expense['total']:,} total · ₹{expense['per_person']:,}/person · {opt['hours']}h",
        "budget_line": (f"₹{abs(round(budget_delta)):,} {'under' if budget_delta >= 0 else 'over'} budget"
                         if budget_delta is not None else ""),
        "match_line": match_line,
        "why_this_won": modes["explanation"],
        "sacrifices": sacrifices or ["No major trade-offs at this budget and group size."],
        "gains": gains,
        "alternative": alternative,
    }


# ---------------------------------------------------------------------------
# Budget Negotiator AI
# ---------------------------------------------------------------------------

NEGOTIATE_WEIGHTS = {
    "budget":   {"transport": 0.22, "stay": 0.24, "food": 0.18, "activities": 0.10, "shopping": 0.12, "emergency": 0.14},
    "balanced": {"transport": 0.22, "stay": 0.26, "food": 0.16, "activities": 0.10, "shopping": 0.14, "emergency": 0.12},
    "comfort":  {"transport": 0.20, "stay": 0.32, "food": 0.16, "activities": 0.10, "shopping": 0.12, "emergency": 0.10},
}


def negotiate_budget(total_budget, comfort_pref):
    w = NEGOTIATE_WEIGHTS.get(comfort_pref, NEGOTIATE_WEIGHTS["balanced"])
    alloc = {k: round(total_budget * v) for k, v in w.items()}
    drift = total_budget - sum(alloc.values())
    alloc["emergency"] = max(0, round(alloc["emergency"] + drift))
    return alloc


def reallocate_budget(allocation, category, delta, mode):
    allocation = dict(allocation)
    if category not in allocation:
        return allocation, "Unknown category."
    allocation[category] = round(allocation[category] + delta)
    delta_i = round(delta)
    if mode == "increase":
        return allocation, f"Total budget increased by ₹{abs(delta_i):,} to cover {category}."
    others = [k for k in allocation if k != category]
    remaining_sum = sum(allocation[k] for k in others)
    if remaining_sum > 0:
        for k in others:
            share = allocation[k] / remaining_sum
            allocation[k] = max(0, round(allocation[k] - delta * share))
    verb = "added to" if delta >= 0 else "removed from"
    return allocation, f"₹{abs(delta_i):,} {verb} {category}, rebalanced proportionally from the rest of the budget."


# ---------------------------------------------------------------------------
# Crowd-Aware Itinerary + Last-Minute Replanner
# ---------------------------------------------------------------------------

def build_crowd_itinerary(days, gems, tourist_traps):
    popular_spots = [t["popular"] for t in tourist_traps] or ["Main landmark"]
    schedule = []
    for i in range(days):
        stops = []
        if gems:
            g = gems[i % len(gems)]
            stops.append({"time": g["best_time"], "place": g["name"], "crowd": "Low",
                          "note": f"{g['distance_km']} km away — go early for the light and the quiet"})
        stops.append({"time": "1:00 PM", "place": "Local food street", "crowd": "Medium", "note": "Lunch window"})
        p = popular_spots[i % len(popular_spots)]
        stops.append({"time": "4:30 PM", "place": p, "crowd": "High", "note": "Visit later in the day to avoid peak crowd"})
        schedule.append({"day": i + 1, "stops": stops})
    return schedule


def _parse_time(t):
    try:
        return datetime.strptime(t, "%I:%M %p")
    except ValueError:
        return None


def replan_for_delay(itinerary, delay_minutes):
    if not itinerary:
        return itinerary, "No itinerary to adjust."
    revised = json.loads(json.dumps(itinerary))
    day1 = revised[0]
    dropped = None
    for stop in day1["stops"]:
        parsed = _parse_time(stop["time"])
        if parsed:
            stop["time"] = (parsed + timedelta(minutes=delay_minutes)).strftime("%I:%M %p").lstrip("0")
    if delay_minutes >= 120 and len(day1["stops"]) > 1:
        idx = max(range(len(day1["stops"])), key=lambda i: {"Low": 0, "Medium": 1, "High": 2}[day1["stops"][i]["crowd"]])
        dropped = day1["stops"].pop(idx)
    if dropped:
        msg = (f"Your ride was delayed {delay_minutes} min, so Day 1's plan shifted later and "
               f"\"{dropped['place']}\" was dropped to keep the rest of the day realistic.")
    else:
        msg = f"Your ride was delayed {delay_minutes} min — Day 1's stop times have been pushed back to match."
    return revised, msg


# ---------------------------------------------------------------------------
# Group Packing & Preparation AI
# ---------------------------------------------------------------------------

def generate_packing_list(interests, days, people):
    items = ["Comfortable walking shoes", "Water bottle", "Power bank", "Basic first-aid kit", "ID proof / documents"]
    if "photography" in interests:
        items.append("Camera or spare phone storage")
    if "adventure" in interests:
        items.append("Light rain protection")
    if "shopping" in interests:
        items.append("Extra foldable bag for shopping")
    if days >= 3:
        items.append("Change of clothes for each day")
    names = [p.get("name") for p in people if p.get("name")] or ["Group"]
    return [{"item": item, "assigned_to": names[i % len(names)]} for i, item in enumerate(items)]


# ---------------------------------------------------------------------------
# Per-Person Expense Balancer
# ---------------------------------------------------------------------------

def compute_settlement(people):
    spenders = [(p.get("name") or f"Traveler {i+1}", float(p.get("spent") or 0)) for i, p in enumerate(people)]
    spenders = [s for s in spenders if s[1] > 0]
    if len(spenders) < 2:
        return None
    total = sum(amt for _, amt in spenders)
    n = len(spenders)
    share = total / n
    balances = {name: round(amt - share) for name, amt in spenders}

    creditors = sorted([[name, bal] for name, bal in balances.items() if bal > 0], key=lambda x: -x[1])
    debtors = sorted([[name, bal] for name, bal in balances.items() if bal < 0], key=lambda x: x[1])
    transactions = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d, c = debtors[i], creditors[j]
        amt = min(-d[1], c[1])
        if amt >= 1:
            transactions.append({"from": d[0], "to": c[0], "amount": round(amt)})
            d[1] += amt
            c[1] -= amt
        if abs(d[1]) < 1:
            i += 1
        if c[1] < 1:
            j += 1
    return {"total_spent": round(total), "share_per_person": round(share), "balances": balances, "settlement": transactions}


# ---------------------------------------------------------------------------
# Core plan computation (shared by /api/plan and /api/whatif)
# ---------------------------------------------------------------------------

def compute_plan(data):
    travelers = max(int(data.get("travelers", 1)), 1)
    destination = data.get("destination", "Jaipur")
    days = max(int(data.get("days", 3)), 1)
    total_budget = float(data.get("budget", 0) or 0)
    food_budget_pp = float(data.get("food_budget_pp", 500) or 500)
    shopping_budget_pp = float(data.get("shopping_budget_pp", 1000) or 1000)
    local_transport_total = float(data.get("local_transport_total", 2000) or 2000)
    hotel_cost_pn_pp = float(data.get("hotel_pp_per_night", 1500) or 1500)
    interests = data.get("interests", ["photography", "history", "food"])
    excluded_modes = set(data.get("exclude_modes", []))
    people = data.get("people", [])
    radius_km = int(data.get("radius_km", 20) or 20)
    sliders = dict(data.get("sliders") or {})
    for k in ("budget_comfort", "speed_savings", "popular_hidden", "shopping_activities"):
        sliders.setdefault(k, 50)

    dest = get_destination(destination)
    distance_km = float(data.get("distance_km") or dest["distance_km"])

    modes = compute_modes(distance_km, travelers, food_budget_pp, local_transport_total, sliders)
    for m in list(modes["options"].keys()):
        if m in excluded_modes:
            del modes["options"][m]
    if excluded_modes and modes["options"]:
        modes["budget_winner"] = min(modes["options"], key=lambda k: modes["options"][k]["total"])
        modes["fastest"] = min(modes["options"], key=lambda k: modes["options"][k]["hours"])
        modes["best_for_group"] = max(modes["options"], key=lambda k: (modes["options"][k]["comfort"], -modes["options"][k]["total"] / max(travelers, 1)))

    # AI Recommendation Engine: scores every surviving mode on trade-off fit,
    # full-trip budget fit, group alignment, comfort, and time — then picks
    # the winner by AI Score rather than the trade-off score alone.
    full_trip_by_mode = compute_ai_scores(modes, travelers, days, food_budget_pp, shopping_budget_pp,
                                           local_transport_total, hotel_cost_pn_pp, sliders, people, total_budget)
    recommended_mode = modes["best_overall"]
    expense = full_trip_by_mode[recommended_mode]

    gems, radius_expanded, gems_in_radius = score_hidden_gems(dest["gems"], interests, radius_km, sliders["popular_hidden"])
    gems = attach_group_match(gems, people)[:4]

    group_pref = aggregate_group_preferences(people) if people else None
    consensus = compute_group_consensus(people, modes["options"], recommended_mode)
    preference_map = build_preference_map(people)

    over_budget = total_budget > 0 and expense["total"] > total_budget

    crowd_itinerary = build_crowd_itinerary(days, gems, dest["tourist_traps"])
    packing_list = generate_packing_list(interests, days, people)
    settlement = compute_settlement(people)
    budget_allocation = negotiate_budget(total_budget, "balanced") if total_budget > 0 else None
    trip_score = compute_trip_score(modes, recommended_mode, consensus, gems, total_budget, expense["total"])
    decision_summary = compute_decision_summary(modes, recommended_mode, expense, total_budget, travelers, consensus)

    return {
        "modes": modes,
        "recommended_mode": recommended_mode,
        "expense": expense,
        "over_budget": over_budget,
        "budget_gap": round(expense["total"] - total_budget) if over_budget else 0,
        "gems": gems,
        "radius_km": radius_km,
        "radius_expanded": radius_expanded,
        "gems_in_radius": gems_in_radius,
        "zones": dest["zones"],
        "tourist_traps": dest["tourist_traps"],
        "group_preferences": group_pref,
        "preference_map": preference_map,
        "consensus": consensus,
        "itinerary": crowd_itinerary,
        "packing_list": packing_list,
        "settlement": settlement,
        "budget_allocation": budget_allocation,
        "trip_score": trip_score,
        "decision_summary": decision_summary,
        "destination": destination,
        "distance_km": distance_km,
        "sliders": sliders,
        "travelers": travelers,
        "days": days,
        "budget": total_budget,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/plan", methods=["POST"])
def api_plan():
    data = request.get_json(force=True) or {}
    return jsonify(compute_plan(data))


@app.route("/api/whatif", methods=["POST"])
def api_whatif():
    """What-Changed? simulator: compares the current plan against one hypothetical change."""
    data = request.get_json(force=True) or {}
    base = data.get("base", {}) or {}
    change = data.get("change", {}) or {}
    ctype = change.get("type")
    label = change.get("label", "Change")

    after_payload = copy.deepcopy(base)
    after_payload["sliders"] = dict(base.get("sliders") or {})
    after_payload["exclude_modes"] = list(base.get("exclude_modes") or [])

    if ctype == "budget_delta":
        after_payload["budget"] = float(base.get("budget", 0) or 0) + float(change.get("value", 0))
    elif ctype == "exclude_mode":
        m = change.get("mode")
        if m and m not in after_payload["exclude_modes"]:
            after_payload["exclude_modes"].append(m)
    elif ctype == "shopping_delta":
        travelers = max(int(base.get("travelers", 1)), 1)
        after_payload["shopping_budget_pp"] = float(base.get("shopping_budget_pp", 0) or 0) + float(change.get("value", 0)) / travelers
    elif ctype == "maximize_speed":
        after_payload["sliders"]["speed_savings"] = 100

    before = compute_plan(base)
    after = compute_plan(after_payload)

    diff = {
        "label": label,
        "mode": {"before": before["recommended_mode"], "after": after["recommended_mode"]},
        "mode_label": {"before": BASE_MODES[before["recommended_mode"]]["label"],
                        "after": BASE_MODES[after["recommended_mode"]]["label"]},
        "total": {"before": before["expense"]["total"], "after": after["expense"]["total"]},
        "per_person": {"before": before["expense"]["per_person"], "after": after["expense"]["per_person"]},
        "comfort": {"before": before["modes"]["options"][before["recommended_mode"]]["comfort"] * 20,
                    "after": after["modes"]["options"][after["recommended_mode"]]["comfort"] * 20},
        "hidden_gems_count": {"before": len(before["gems"]), "after": len(after["gems"])},
        "trip_score": {"before": before["trip_score"]["overall"], "after": after["trip_score"]["overall"]},
    }
    return jsonify({"diff": diff})


@app.route("/api/budget/negotiate", methods=["POST"])
def api_budget_negotiate():
    data = request.get_json(force=True) or {}
    total_budget = float(data.get("budget", 0) or 0)
    comfort_pref = data.get("comfort", "balanced")
    allocation = negotiate_budget(total_budget, comfort_pref)
    return jsonify({"allocation": allocation, "total": total_budget})


@app.route("/api/budget/reallocate", methods=["POST"])
def api_budget_reallocate():
    data = request.get_json(force=True) or {}
    allocation = data.get("allocation", {})
    category = data.get("category")
    delta = float(data.get("delta", 0) or 0)
    mode = data.get("mode", "reallocate")
    new_allocation, message = reallocate_budget(allocation, category, delta, mode)
    return jsonify({"allocation": new_allocation, "message": message, "total": sum(new_allocation.values())})


@app.route("/api/replan", methods=["POST"])
def api_replan():
    data = request.get_json(force=True) or {}
    itinerary = data.get("itinerary", [])
    delay_minutes = int(data.get("delay_minutes", 0) or 0)
    revised, message = replan_for_delay(itinerary, delay_minutes)
    return jsonify({"itinerary": revised, "message": message})


def build_structured_context(result):
    """Serializes the live plan in the fixed order the trip-aware chatbot and
    the AI briefing both rely on: trip details, current recommendation, every
    transport option, budget/expense, group preferences, consensus, hidden
    gems, itinerary, tourist traps, sliders, trip score."""
    if not result:
        return "No trip has been generated yet — ask the user to fill in the form and click Generate."

    lines = []
    lines.append(f"TRIP DETAILS: {result.get('travelers', '?')} travelers, {result.get('days', '?')} days to "
                  f"{result.get('destination', '?')}, stated budget ₹{result.get('budget', 0):,.0f}.")

    ds = result.get("decision_summary") or {}
    lines.append(f"CURRENT RECOMMENDATION: {ds.get('headline', '')}. {ds.get('metrics_line', '')}. "
                  f"{ds.get('budget_line', '')}. {ds.get('match_line', '')}")

    modes = (result.get("modes") or {}).get("options", {})
    mode_bits = []
    for k, o in modes.items():
        mode_bits.append(f"{k}: AI score {o.get('ai_score', '?')}/100 (budget fit {o.get('budget_fit', '?')}, "
                          f"group alignment {o.get('group_alignment', '?')}), full trip ₹{o.get('full_trip_cost', '?')}, "
                          f"₹{o.get('cost_per_person', '?')}/person, {o.get('hours', '?')}h, comfort {o.get('comfort', '?')}/5")
    lines.append("ALL TRANSPORT OPTIONS: " + (" | ".join(mode_bits) if mode_bits else "none"))

    e = result.get("expense") or {}
    lines.append(f"BUDGET + EXPENSE BREAKDOWN: total ₹{e.get('total', 0):,}, per person ₹{e.get('per_person', 0):,}, "
                  f"travel ₹{e.get('travel', 0):,}, hotel ₹{e.get('hotel', 0):,}, food ₹{e.get('food', 0):,}, "
                  f"local transport ₹{e.get('local_transport', 0):,}, activities ₹{e.get('activities', 0):,}, "
                  f"shopping ₹{e.get('shopping', 0):,}, buffer ₹{e.get('buffer', 0):,}.")

    gp = result.get("group_preferences")
    lines.append(f"GROUP PREFERENCES (0-100 each): {gp}" if gp else "GROUP PREFERENCES: no travelers added yet.")

    c = result.get("consensus")
    lines.append(f"GROUP CONSENSUS: {c.get('explanation')}" if c else "GROUP CONSENSUS: no travelers added yet.")

    gems = result.get("gems") or []
    lines.append("HIDDEN GEMS: " + ("; ".join(f"{g['name']} ({g['discovery_score']}% match)" for g in gems) if gems else "none scored yet."))

    itinerary = result.get("itinerary") or []
    lines.append(f"ITINERARY: {len(itinerary)} day(s) planned, crowd-aware (hidden gems early, popular spots late afternoon).")

    traps = result.get("tourist_traps") or []
    lines.append("TOURIST TRAPS: " + ("; ".join(f"{t['popular']} (₹{t['popular_cost']}) → {t['alternative']} (₹{t['alt_cost']})" for t in traps) if traps else "none for this destination."))

    lines.append(f"SLIDERS (0-100): {result.get('sliders', {})}")

    ts = result.get("trip_score") or {}
    lines.append(f"TRIP SCORE: {ts.get('overall', 'n/a')}/100, factors: {ts.get('factors', {})}")

    return "\n".join(lines)


def fallback_chat_answer(message, result):
    """Rule-based answers used when no Groq key is configured, so the
    chatbot still works from the live trip data rather than refusing."""
    if not result or not result.get("decision_summary"):
        return "Generate a plan first (fill in the form above and click \"Generate the plan\") and I'll be able to answer from it."

    msg = (message or "").lower()
    ds = result["decision_summary"]

    if any(w in msg for w in ["why", "reason"]) and any(w in msg for w in ["train", "bus", "car", "flight", "mode", "recommend", "chose", "chosen", "pick"]):
        return f"{ds.get('why_this_won', '')} {ds.get('metrics_line', '')}".strip()
    if any(w in msg for w in ["budget", "cost", "expense", "spend", "price"]):
        e = result.get("expense", {})
        return (f"Total estimated cost is ₹{e.get('total', 0):,} (₹{e.get('per_person', 0):,}/person). "
                f"{ds.get('budget_line', '')}").strip()
    if any(w in msg for w in ["gem", "hidden", "secret"]):
        gems = result.get("gems", [])
        return (f"Top hidden gems right now: " + ", ".join(g["name"] for g in gems[:3]) + "."
                if gems else "No hidden gems scored yet — generate a plan first.")
    if any(w in msg for w in ["consensus", "group", "everyone", "satisf"]):
        c = result.get("consensus")
        return c["explanation"] if c else "Add travelers in the Group Preference Voting panel to see a consensus score."
    if any(w in msg for w in ["itinerary", "schedule", "day 1", "plan for"]):
        itinerary = result.get("itinerary", [])
        if itinerary:
            stops = "; ".join(f"{s['time']} {s['place']} ({s['crowd']} crowd)" for s in itinerary[0]["stops"])
            return f"Day 1: {stops}."
        return "No itinerary generated yet."
    if "score" in msg:
        ts = result.get("trip_score", {})
        return f"BeyondTrip Score is {ts.get('overall', 'n/a')}/100. Factors: {ts.get('factors', {})}"
    if any(w in msg for w in ["sacrifice", "trade", "give up", "downside"]):
        return "Trade-offs: " + "; ".join(ds.get("sacrifices", [])) + ". Gains: " + "; ".join(ds.get("gains", []))
    if "alternative" in msg or "instead" in msg:
        alt = ds.get("alternative")
        return f"{alt['label']} — {alt['tradeoff']}" if alt else "No meaningful alternative at this group size."

    return ("I can answer from your current plan — try asking about the recommended mode, budget, hidden gems, "
            "group consensus, itinerary, trade-offs, or trip score. Add a GROQ_API_KEY to .env for open-ended "
            "what-if questions and natural follow-ups.")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Trip-aware chat assistant (v2), backed by Groq with conversation memory.
    Falls back to rule-based answers from the live trip data when no key is set."""
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    context = data.get("context", {})
    history = data.get("history", []) or []
    result = context.get("result") or {}

    if not GROQ_API_KEY:
        return jsonify({"reply": fallback_chat_answer(message, result), "configured": False})

    structured_context = build_structured_context(result)
    system_prompt = (
        "You are the BeyondTrip assistant, embedded directly inside a group-travel planning dashboard for trips "
        "within India — you are not a generic chatbot, you ARE this specific trip's assistant. You already know "
        "the full current plan from the structured context below; answer using it directly instead of asking the "
        "user to repeat details they've already entered. Use the recent conversation turns for continuity — for "
        "example if the user just asked \"why train?\" and now asks \"what if we have ₹5,000 more?\", treat it as "
        "a continuation of the same topic. Be concise and concrete. Speak in INR. Frame any numbers you did not "
        "get from the context as estimates.\n\n"
        f"STRUCTURED TRIP CONTEXT:\n{structured_context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-6:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)[:1000]})
    messages.append({"role": "user", "content": message})

    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.5, "max_tokens": 500},
            timeout=20,
        )
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply, "configured": True})
    except Exception as e:
        return jsonify({"reply": f"Chat service error: {e}", "configured": True}), 200


# ---------------------------------------------------------------------------
# BeyondTrip AI Briefing — a short, Groq-written explanation of the optimizer
# result (why/factors/trade-off/next action). Falls back to a deterministic,
# template-based briefing built straight from the AI Score breakdown when
# Groq isn't configured or the call fails, so this panel never breaks.
# ---------------------------------------------------------------------------

def deterministic_briefing(result):
    mode = result.get("recommended_mode")
    opt = (result.get("modes") or {}).get("options", {}).get(mode, {})
    ds = result.get("decision_summary") or {}
    factor_values = [
        ("Budget fit", opt.get("budget_fit", 0)), ("Group alignment", opt.get("group_alignment", 0)),
        ("Trade-off score", opt.get("trade_off_score", 0)), ("Comfort", round(opt.get("comfort_score", 0) * 100)),
        ("Time efficiency", round(opt.get("time_score", 0) * 100)),
    ]
    top = sorted(factor_values, key=lambda x: -x[1])[:3]
    factors_line = ", ".join(f"{name} ({val}/100)" for name, val in top)
    label = BASE_MODES.get(mode, {}).get("label", mode)
    return {
        "why": ds.get("why_this_won", f"{label} had the highest AI Score among the available options."),
        "factors": f"Driven mainly by {factors_line}.",
        "tradeoff": ds.get("sacrifices", ["No major trade-off at this budget and group size."])[0],
        "next_action": f"Lock in {label} and review the itinerary and packing list below.",
        "source": "deterministic",
    }


@app.route("/api/briefing", methods=["POST"])
def api_briefing():
    data = request.get_json(force=True) or {}
    result = data.get("result", {}) or {}

    if not result.get("decision_summary"):
        return jsonify({"why": "Generate a plan first.", "factors": "", "tradeoff": "", "next_action": "", "source": "none"})

    if not GROQ_API_KEY:
        return jsonify(deterministic_briefing(result))

    structured_context = build_structured_context(result)
    prompt = (
        "Using ONLY the trip context below, write a short briefing as a JSON object with exactly these four string "
        "keys: \"why\" (why this travel mode was selected), \"factors\" (what factors drove the decision, naming the "
        "actual AI Score components and numbers), \"tradeoff\" (the single main trade-off of this choice), and "
        "\"next_action\" (one practical next step for the group). Output ONLY the JSON object, no markdown, no "
        "commentary.\n\n" + structured_context
    )
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 400,
            },
            timeout=20,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(text)
        for key in ("why", "factors", "tradeoff", "next_action"):
            parsed.setdefault(key, "")
        parsed["source"] = "groq"
        return jsonify(parsed)
    except Exception:
        fallback = deterministic_briefing(result)
        fallback["source"] = "deterministic-fallback"
        return jsonify(fallback)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
