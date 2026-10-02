(function () {
  const planForm = document.getElementById("plan-form");
  const resultsSection = document.getElementById("plan");
  const interestChips = document.getElementById("interest-chips");
  const personForm = document.getElementById("person-form");
  const peopleList = document.getElementById("people-list");
  const prefBars = document.getElementById("pref-bars");

  let people = [];
  let chatHistory = [];
  let lastFormData = null;
  let lastResult = null;
  let excludedModes = new Set();
  let currentAllocation = null;

  const money = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
  const MODE_LABELS = { car: "🚗 Car", bus: "🚌 Bus", train: "🚆 Train", flight: "✈️ Flight" };
  const CATEGORY_LABEL = { budget: "Budget", comfort: "Comfort", food: "Food", shopping: "Shopping",
                            adventure: "Adventure", photography: "Photography", history: "History" };

  interestChips.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    btn.classList.toggle("active");
  });

  function selectedInterests() {
    return Array.from(interestChips.querySelectorAll(".chip.active")).map((b) => b.dataset.value);
  }

  function sliderValues() {
    return {
      budget_comfort: Number(document.getElementById("slider-budget-comfort").value),
      speed_savings: Number(document.getElementById("slider-speed-savings").value),
      popular_hidden: Number(document.getElementById("slider-popular-hidden").value),
      shopping_activities: Number(document.getElementById("slider-shopping-activities").value),
    };
  }

  function collectFormData() {
    const fd = new FormData(planForm);
    return {
      source: fd.get("source"),
      destination: fd.get("destination"),
      travelers: Number(fd.get("travelers")),
      days: Number(fd.get("days")),
      budget: Number(fd.get("budget")),
      food_budget_pp: Number(fd.get("food_budget_pp")),
      shopping_budget_pp: Number(fd.get("shopping_budget_pp")),
      hotel_pp_per_night: Number(fd.get("hotel_pp_per_night")),
      interests: selectedInterests(),
      people,
      exclude_modes: Array.from(excludedModes),
      radius_km: Number(document.getElementById("radius-select").value),
      sliders: sliderValues(),
    };
  }

  async function requestPlan(payload) {
    const res = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  planForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    excludedModes = new Set();
    const payload = collectFormData();
    lastFormData = payload;
    const result = await requestPlan(payload);
    lastResult = result;
    renderAll(payload, result);
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  });

  function renderAll(payload, result) {
    renderDecisionSummary(result);
    renderModes(result);
    renderConsensus(result);
    renderZones(result, payload.destination);
    renderGems(result);
    renderTraps(result);
    renderItinerary(result.itinerary);
    renderExpense(result, payload.budget);
    renderNegotiator(result.budget_allocation);
    renderPeople();
    renderPrefBars(result.group_preferences);
    renderPreferenceMap(result);
    renderSettlement(result.settlement);
    renderPacking(result.packing_list);
    document.getElementById("whatif-result").classList.add("hidden");
    fetchBriefing(result);
  }

  // ---- BeyondTrip AI Briefing ----
  async function fetchBriefing(result) {
    const body = document.getElementById("briefing-body");
    const sourceEl = document.getElementById("briefing-source");
    body.innerHTML = `<p class="muted">Generating briefing…</p>`;
    sourceEl.textContent = "";
    try {
      const res = await fetch("/api/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result }),
      });
      const b = await res.json();
      body.innerHTML = `
        <div class="briefing-card"><h4>Why this mode</h4><p>${b.why || ""}</p></div>
        <div class="briefing-card"><h4>What drove it</h4><p>${b.factors || ""}</p></div>
        <div class="briefing-card"><h4>Main trade-off</h4><p>${b.tradeoff || ""}</p></div>
        <div class="briefing-card"><h4>Next action</h4><p>${b.next_action || ""}</p></div>
      `;
      sourceEl.textContent = b.source === "groq" ? "· AI-generated" : "· built from the optimizer (add a Groq key for AI-written wording)";
    } catch (err) {
      body.innerHTML = `<p class="muted">Briefing unavailable right now — the decision summary above still covers why this mode was picked.</p>`;
    }
  }

  // ---- 2 & 3. AI Decision Summary + Trip Score ----
  function renderDecisionSummary(result) {
    const s = result.decision_summary;
    const ts = result.trip_score;
    document.getElementById("decision-mode-icon").textContent =
      { car: "🚗", bus: "🚌", train: "🚆", flight: "✈️" }[result.recommended_mode] || "🧭";
    document.getElementById("decision-headline").textContent = s.headline;
    document.getElementById("decision-metrics").textContent = s.metrics_line;
    document.getElementById("decision-budget").textContent = s.budget_line;
    document.getElementById("decision-match").textContent = s.match_line;
    document.getElementById("decision-why").textContent = s.why_this_won;
    document.getElementById("decision-sacrifice").innerHTML = s.sacrifices.map((x) => `<li>${x}</li>`).join("");
    document.getElementById("decision-gain").innerHTML = s.gains.map((x) => `<li>${x}</li>`).join("");
    document.getElementById("decision-alternative").textContent = s.alternative
      ? `${s.alternative.label} — ${s.alternative.tradeoff}`
      : "No meaningful alternative at this group size.";

    document.getElementById("trip-score-ring").style.setProperty("--pct", ts.overall);
    document.getElementById("trip-score-number").textContent = ts.overall + "/100";

    const labels = {
      budget_fit: "Budget fit", time_efficiency: "Time efficiency", group_satisfaction: "Group satisfaction",
      comfort: "Comfort", experience: "Experience", hidden_gem_potential: "Hidden-gem potential",
    };
    const breakdown = document.getElementById("trip-score-breakdown");
    breakdown.innerHTML = "";
    Object.entries(ts.factors).forEach(([k, v]) => breakdown.appendChild(barRow(labels[k] || k, v, 100)));
  }

  // ---- Modes ----
  function renderModes(result) {
    const grid = document.getElementById("modes-grid");
    grid.innerHTML = "";
    const opts = result.modes.options;
    Object.entries(opts).forEach(([key, o]) => {
      const isBest = key === result.modes.best_overall;
      const card = document.createElement("div");
      card.className = "mode-card" + (isBest ? " crown" : "");
      const aiScoreHtml = (o.ai_score !== undefined) ? `
        <div class="mode-ai-score">
          <div class="mode-ai-ring" style="--pct:${o.ai_score}"><span>${o.ai_score}</span></div>
          <div class="mode-ai-breakdown">
            <div class="mode-ai-row"><span>Budget fit</span><b>${o.budget_fit}</b></div>
            <div class="mode-ai-row"><span>Group alignment</span><b>${o.group_alignment}</b></div>
            <div class="mode-ai-row"><span>Full trip cost</span><b>${money(o.full_trip_cost)}</b></div>
            <div class="mode-ai-row"><span>Cost / person</span><b>${money(o.cost_per_person)}</b></div>
          </div>
        </div>
      ` : "";
      card.innerHTML = `
        ${isBest ? '<span class="badge">🏆 Best overall</span>' : ""}
        <div class="mode-name">${MODE_LABELS[key] || o.label}</div>
        ${aiScoreHtml}
        <div class="mode-stat"><span>Travel time</span><b>${o.hours}h</b></div>
        <div class="mode-stat"><span>Travel cost</span><b>${money(o.travel_cost)}</b></div>
        <div class="mode-stat"><span>Comfort</span><b>${o.comfort}/5</b></div>
        <div class="mode-total">${money(o.total)} <small>(travel-only estimate)</small></div>
      `;
      grid.appendChild(card);
    });
    document.getElementById("modes-explain").textContent = result.modes.explanation;
    document.getElementById("modes-legend").innerHTML = `
      <div>💰 Budget winner: <b>${MODE_LABELS[result.modes.budget_winner]}</b></div>
      <div>⚡ Fastest: <b>${MODE_LABELS[result.modes.fastest]}</b></div>
      <div>👥 Best for group: <b>${MODE_LABELS[result.modes.best_for_group]}</b></div>
    `;
  }

  // ---- 1. Group Consensus Engine ----
  function renderConsensus(result) {
    const body = document.getElementById("consensus-body");
    const c = result.consensus;
    if (!c) {
      body.innerHTML = `<p class="muted">Add at least one traveler's priorities below, then regenerate the plan.</p>`;
      return;
    }
    const listItems = c.details.map(
      (d) => `<li class="${d.satisfied ? "ok" : "no"}">${d.name} · ${CATEGORY_LABEL[d.top_priority]} ${d.satisfied ? "✓" : "✗"}</li>`
    ).join("");
    body.innerHTML = `
      <div class="consensus-score" style="--pct:${c.score}"><span>${c.score}%</span></div>
      <div class="consensus-details">
        <p>${c.explanation}</p>
        <ul class="consensus-list">${listItems}</ul>
      </div>
    `;
  }

  // ---- Zones ----
  function renderZones(result, destination) {
    document.getElementById("dest-name-zones").textContent = destination || "the destination";
    const grid = document.getElementById("zones-grid");
    grid.innerHTML = "";
    result.zones.forEach((z) => {
      const card = document.createElement("div");
      card.className = "zone-card";
      card.innerHTML = `
        <h3>${z.name}</h3>
        <p>${z.theme}</p>
        <div class="zone-tags">${z.tags.map((t) => `<span class="tag-pill">${t}</span>`).join("")}</div>
      `;
      grid.appendChild(card);
    });
  }

  // ---- 3. Hidden Gem Confidence Score + Dynamic Radius ----
  function factorRow(label, value) {
    return `
      <div class="gem-factor-row">
        <span>${label}</span>
        <div class="gem-factor-track"><div class="gem-factor-fill" style="width:${value}%"></div></div>
        <span>${value}</span>
      </div>
    `;
  }

  function renderGems(result) {
    const grid = document.getElementById("gems-grid");
    grid.innerHTML = "";
    const explainEl = document.getElementById("gems-explain");
    let note = `Scored against the interests and sliders above, within ${result.radius_km} km — not popularity.`;
    if (result.radius_expanded) {
      note += ` Only ${result.gems_in_radius} spot(s) fell inside that radius, so a few just outside are shown too.`;
    }
    explainEl.textContent = note;

    const TAG_ICON = { photography: "📸", history: "🏛️", food: "🍜", shopping: "🛍️", adventure: "⚡" };

    result.gems.forEach((g) => {
      const f = g.factors;
      const gm = g.group_match;
      const matchLine = gm
        ? `<div class="gem-match">Why your group: ${gm.count}/${gm.of} travelers prefer ${gm.tags.map((t) => t).join("/")}.</div>`
        : "";
      const topTags = (gm ? gm.tags : Object.keys(g.tags).sort((a, b) => g.tags[b] - g.tags[a]).slice(0, 2));
      const tagsRow = `<div class="gem-tags-row">${topTags.map((t) => `<span class="tag-pill">${TAG_ICON[t] || ""} ${t}</span>`).join("")}</div>`;
      const card = document.createElement("div");
      card.className = "gem-card";
      card.innerHTML = `
        <div class="gem-top">
          <div class="gem-name">${g.name}</div>
          <div class="gem-score" style="--score:${g.discovery_score}"><span>${g.discovery_score}%</span></div>
        </div>
        <div class="gem-why">Recommended because ${g.why}.</div>
        <div class="gem-meta">
          <span>${g.distance_km} km away</span>
          <span>${g.cost_pp === 0 ? "Free" : money(g.cost_pp) + "/person"}</span>
          <span>Best: ${g.best_time}</span>
        </div>
        ${tagsRow}
        ${matchLine}
        <div class="gem-factors">
          ${factorRow("Interest match", f.group_interest_match)}
          ${factorRow("Budget match", f.budget_match)}
          ${factorRow("Crowd level", f.crowd_level)}
          ${factorRow("Distance", f.distance)}
          ${factorRow("Experience", f.experience)}
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // ---- Tourist traps ----
  function stars(rating) {
    const full = Math.round(rating);
    return "★".repeat(full) + "☆".repeat(5 - full) + ` ${rating.toFixed(1)}`;
  }

  function renderTraps(result) {
    const list = document.getElementById("traps-list");
    list.innerHTML = "";
    result.tourist_traps.forEach((t) => {
      const savings = t.popular_cost - t.alt_cost;
      const row = document.createElement("div");
      row.className = "trap-row";
      row.innerHTML = `
        <div class="trap-side popular">
          <h4>${t.popular}</h4>
          <div class="price">${money(t.popular_cost)}</div>
          <div class="stars">${stars(t.popular_rating)}</div>
        </div>
        <div class="trap-arrow">→</div>
        <div class="trap-side alt">
          <h4>${t.alternative}</h4>
          <div class="price">${money(t.alt_cost)}</div>
          <div class="stars">${stars(t.alt_rating)}</div>
        </div>
        <div class="trap-note">${t.alt_distance_km} km away — similar experience, an estimated ${money(savings)} lower spend. ${t.note}.</div>
      `;
      list.appendChild(row);
    });
  }

  // ---- 6 & 7. Crowd-aware itinerary + Last-minute replanner ----
  function renderItinerary(itinerary) {
    const el = document.getElementById("itinerary-timeline");
    el.innerHTML = "";
    itinerary.forEach((day) => {
      const dayDiv = document.createElement("div");
      dayDiv.className = "itinerary-day";
      const stopsHtml = day.stops.map((s) => {
        const crowdClass = "crowd-" + s.crowd.toLowerCase();
        return `
          <div class="itinerary-stop ${crowdClass}">
            <span>${s.time}</span>
            <span class="dot"></span>
            <span>
              <span class="place">${s.place}</span>
              <span class="crowd-tag ${crowdClass}">${s.crowd} crowd</span>
              <div class="note">${s.note}</div>
            </span>
          </div>
        `;
      }).join("");
      dayDiv.innerHTML = `<h4>Day ${day.day}</h4>${stopsHtml}`;
      el.appendChild(dayDiv);
    });
  }

  document.getElementById("replan-run").addEventListener("click", async () => {
    if (!lastResult) return;
    const delay = Number(document.getElementById("replan-delay").value || 0);
    const res = await fetch("/api/replan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ itinerary: lastResult.itinerary, delay_minutes: delay }),
    });
    const data = await res.json();
    lastResult.itinerary = data.itinerary;
    renderItinerary(data.itinerary);
    document.getElementById("replan-msg").textContent = data.message;
  });

  // ---- Expense ----
  function barRow(label, value, max) {
    const pct = max > 0 ? Math.round((value / max) * 100) : 0;
    const row = document.createElement("div");
    row.className = "expense-bar-row";
    row.innerHTML = `
      <span>${label}</span>
      <div class="expense-bar-track"><div class="expense-bar-fill" style="width:${pct}%"></div></div>
      <span>${money(value)}</span>
    `;
    return row;
  }

  function renderExpense(result, budget) {
    const e = result.expense;
    const bars = document.getElementById("expense-bars");
    bars.innerHTML = "";
    const max = Math.max(e.travel, e.hotel, e.food, e.local_transport, e.activities, e.shopping, 1);
    bars.appendChild(barRow("Travel", e.travel, max));
    bars.appendChild(barRow("Hotel", e.hotel, max));
    bars.appendChild(barRow("Food", e.food, max));
    bars.appendChild(barRow("Local transport", e.local_transport, max));
    bars.appendChild(barRow("Activities", e.activities, max));
    bars.appendChild(barRow("Shopping", e.shopping, max));
    bars.appendChild(barRow("Buffer (5%)", e.buffer, max));

    document.getElementById("expense-total").innerHTML = `
      <div class="grand">${money(e.total)}</div>
      <div class="per-person">${money(e.per_person)} / person</div>
    `;

    const warn = document.getElementById("budget-warning");
    if (result.over_budget) {
      warn.classList.remove("hidden");
      warn.textContent = `⚠️ This plan runs ${money(result.budget_gap)} over the stated budget — try the sliders or the Budget Negotiator below.`;
    } else {
      warn.classList.add("hidden");
    }
  }

  // ---- 5. Budget Negotiator AI ----
  function renderNegotiator(allocation) {
    currentAllocation = allocation;
    const bars = document.getElementById("negotiator-bars");
    bars.innerHTML = "";
    document.getElementById("negotiate-msg").textContent = "";
    if (!allocation) {
      bars.innerHTML = `<p class="muted">Enter a total budget above to see an automatic category split.</p>`;
      return;
    }
    const max = Math.max(...Object.values(allocation), 1);
    const labels = { transport: "Transport", stay: "Stay", food: "Food", activities: "Activities", shopping: "Shopping", emergency: "Emergency" };
    Object.entries(allocation).forEach(([k, v]) => bars.appendChild(barRow(labels[k] || k, v, max)));
  }

  document.getElementById("negotiate-run").addEventListener("click", async () => {
    if (!currentAllocation) return;
    const category = document.getElementById("negotiate-category").value;
    const amount = Number(document.getElementById("negotiate-amount").value || 0);
    const mode = document.getElementById("negotiate-mode").value;
    const res = await fetch("/api/budget/reallocate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ allocation: currentAllocation, category, delta: amount, mode }),
    });
    const data = await res.json();
    renderNegotiator(data.allocation);
    document.getElementById("negotiate-msg").textContent = data.message;
  });

  // ---- Voting / people ----
  function renderPeople() {
    peopleList.innerHTML = "";
    people.forEach((p) => {
      const li = document.createElement("li");
      li.textContent = p.name + (p.spent > 0 ? ` (₹${p.spent} spent)` : "");
      peopleList.appendChild(li);
    });
  }

  function renderPrefBars(groupPref) {
    prefBars.innerHTML = "";
    if (!groupPref) return;
    Object.entries(groupPref).forEach(([key, val]) => {
      prefBars.appendChild(barRow(CATEGORY_LABEL[key] || key, val, 100));
    });
  }

  personForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(personForm);
    people.push({
      name: fd.get("name"),
      budget: fd.get("budget"),
      comfort: fd.get("comfort"),
      food: fd.get("food"),
      shopping: fd.get("shopping"),
      adventure: fd.get("adventure"),
      photography: fd.get("photography"),
      spent: Number(fd.get("spent") || 0),
    });
    personForm.reset();
    renderPeople();
    if (lastFormData) {
      lastFormData.people = people;
      const result = await requestPlan(lastFormData);
      lastResult = result;
      renderDecisionSummary(result);
      renderModes(result);
      renderConsensus(result);
      renderPrefBars(result.group_preferences);
      renderPreferenceMap(result);
      renderSettlement(result.settlement);
      renderPacking(result.packing_list);
      fetchBriefing(result);
    }
  });

  // ---- 9. Per-Person Expense Balancer ----
  function renderSettlement(settlement) {
    const el = document.getElementById("settlement-body");
    if (!settlement) {
      el.innerHTML = `<p class="muted">Add at least two travelers with a spent amount above, then regenerate the plan.</p>`;
      return;
    }
    const rows = Object.entries(settlement.balances).map(
      ([name, bal]) => `<tr><td>${name}</td><td>${bal >= 0 ? "Overpaid" : "Owes"}</td><td>${money(Math.abs(bal))}</td></tr>`
    ).join("");
    const tx = settlement.settlement.map(
      (t) => `<li><b>${t.from}</b> pays <b>${t.to}</b> ${money(t.amount)}</li>`
    ).join("") || "<li>Everyone is already even.</li>";
    el.innerHTML = `
      <table class="settlement-table">
        <thead><tr><th>Traveler</th><th>Status</th><th>Amount</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="muted">Total spent so far: ${money(settlement.total_spent)} · fair share: ${money(settlement.share_per_person)}/person</p>
      <ul class="settlement-tx">${tx}</ul>
    `;
  }

  // ---- 8. Group Packing & Prep ----
  function renderPacking(list) {
    const el = document.getElementById("packing-list");
    el.innerHTML = "";
    (list || []).forEach((item) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${item.item}</span><span class="assignee">${item.assigned_to}</span>`;
      el.appendChild(li);
    });
  }

  // ---- 6. Group Preference Map ----
  function renderPreferenceMap(result) {
    const body = document.getElementById("prefmap-body");
    const rows = result.preference_map || [];
    if (!rows.length) {
      body.innerHTML = `<p class="muted">Add travelers above to see the map.</p>`;
      return;
    }
    const rowsHtml = rows.map((r) => {
      const cells = r.cells.map((c) => `<span class="prefmap-cell">${c.emoji.repeat(c.count)} ${CATEGORY_LABEL[c.category] || c.category}</span>`).join("");
      return `<div class="prefmap-row"><span class="prefmap-name">${r.name}</span><span class="prefmap-cells">${cells}</span></div>`;
    }).join("");

    let consensusHtml = "";
    if (result.consensus) {
      consensusHtml = `
        <div class="prefmap-consensus">
          <span class="arrow-down">↓ AI CONSENSUS ↓</span>
          <span class="mode-pill">${MODE_LABELS[result.recommended_mode]}</span>
          <span class="pct-pill">${result.consensus.score}% GROUP SATISFACTION</span>
        </div>
      `;
    }
    body.innerHTML = rowsHtml + consensusHtml;
  }

  // ---- 5. What Changed? simulator ----
  document.querySelectorAll(".whatif-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!lastFormData) return;
      const change = {
        type: btn.dataset.type,
        label: btn.dataset.label,
        value: btn.dataset.value ? Number(btn.dataset.value) : undefined,
        mode: btn.dataset.mode,
      };
      const res = await fetch("/api/whatif", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base: lastFormData, change }),
      });
      const data = await res.json();
      renderWhatIf(data.diff);
    });
  });

  function whatifRow(label, before, after, fmt) {
    const b = fmt ? fmt(before) : before;
    const a = fmt ? fmt(after) : after;
    return `<div class="whatif-row"><span>${label}</span><span class="before">${b}</span><span class="arrow">→</span><span class="after">${a}</span></div>`;
  }

  function renderWhatIf(diff) {
    const el = document.getElementById("whatif-result");
    el.classList.remove("hidden");
    el.innerHTML = `
      <h4>${diff.label}</h4>
      ${whatifRow("Travel mode", diff.mode_label.before, diff.mode_label.after)}
      ${whatifRow("Total cost", diff.total.before, diff.total.after, money)}
      ${whatifRow("Per person", diff.per_person.before, diff.per_person.after, money)}
      ${whatifRow("Comfort", diff.comfort.before, diff.comfort.after, (v) => v + "/100")}
      ${whatifRow("Hidden gems shown", diff.hidden_gems_count.before, diff.hidden_gems_count.after)}
      ${whatifRow("BeyondTrip Score", diff.trip_score.before, diff.trip_score.after, (v) => v + "/100")}
    `;
  }

  // ---- Chat ----
  const launcher = document.getElementById("chat-launcher");
  const panel = document.getElementById("chat-panel");
  const closeBtn = document.getElementById("chat-close");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");

  launcher.addEventListener("click", () => panel.classList.toggle("hidden"));
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));

  function addMsg(text, cls) {
    const div = document.createElement("div");
    div.className = "chat-msg " + cls;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;
    addMsg(msg, "user");
    chatInput.value = "";
    addMsg("…", "bot");
    const thinkingNode = chatMessages.lastChild;
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg,
          context: { form: lastFormData, result: lastResult },
          history: chatHistory.slice(-6),
        }),
      });
      const data = await res.json();
      thinkingNode.textContent = data.reply;
      // keep the last few turns so follow-ups like "what if we have ₹5,000 more?" stay continuous
      chatHistory.push({ role: "user", content: msg });
      chatHistory.push({ role: "assistant", content: data.reply });
      if (chatHistory.length > 12) chatHistory = chatHistory.slice(-12);
    } catch (err) {
      thinkingNode.textContent = "Something went wrong reaching the assistant.";
    }
  });

  // ---- Voice input for chat ----
  const micBtn = document.getElementById("chat-mic");
  const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognitionCtor) {
    micBtn.classList.add("unsupported");
    micBtn.title = "Voice input isn't supported in this browser — try Chrome or Edge.";
    micBtn.addEventListener("click", () => {
      addMsg("Voice input isn't supported in this browser — try Chrome or Edge, or just type your question.", "bot");
    });
  } else {
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    let listening = false;

    micBtn.addEventListener("click", () => {
      if (listening) {
        recognition.stop();
        return;
      }
      try {
        recognition.start();
      } catch (err) {
        // start() throws if called while already starting; ignore
      }
    });

    recognition.addEventListener("start", () => {
      listening = true;
      micBtn.classList.add("listening");
      panel.classList.remove("hidden");
    });

    recognition.addEventListener("end", () => {
      listening = false;
      micBtn.classList.remove("listening");
    });

    recognition.addEventListener("error", (e) => {
      listening = false;
      micBtn.classList.remove("listening");
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        addMsg("Microphone access was blocked — allow it in your browser's site settings to use voice input.", "bot");
      }
    });

    recognition.addEventListener("result", (e) => {
      const transcript = e.results[0][0].transcript;
      chatInput.value = transcript;
      // speak -> fill input -> auto-send, exactly like pressing Send
      chatForm.requestSubmit ? chatForm.requestSubmit() : chatForm.dispatchEvent(new Event("submit", { cancelable: true }));
    });
  }
})();
