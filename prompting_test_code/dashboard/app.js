const SCENARIO_FILES = {
  1: "../results/scenario1_results.json",
  2: "../results/scenario2_results.json",
  3: "../results/scenario3_results.json",
};

let currentScenarioId = 1;
let currentScenarioData = null;
let currentIndex = 0;
let isPlaying = false;
let playTimeout = null;
let baseDelaySeconds = 2;

const chatWindow = document.getElementById("chat-window");
const chatEmptyState = document.getElementById("chat-empty-state");
const toolStatusList = document.getElementById("tool-status-list");
const safetyStatus = document.getElementById("safety-status");
const safetyLoading = document.getElementById("safety-loading");
const currentTurnLabel = document.getElementById("current-turn-label");
const expectedLabel = document.getElementById("expected-label");
const timelineProgress = document.getElementById("timeline-progress");
const timelinePercent = document.getElementById("timeline-percent");
const timelineLabels = document.getElementById("timeline-labels");
const scenarioMeta = document.getElementById("scenario-meta");
const etaLabel = document.getElementById("eta-label");

const playBtn = document.getElementById("play-btn");
const pauseBtn = document.getElementById("pause-btn");
const resetBtn = document.getElementById("reset-btn");
const exportBtn = document.getElementById("export-btn");
const speedSelect = document.getElementById("speed-select");

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function setPlaying(playing) {
  isPlaying = playing;
  playBtn.disabled = playing;
  pauseBtn.disabled = !playing;
}

function clearChat() {
  chatWindow.innerHTML = "";
  if (chatEmptyState) {
    chatEmptyState.classList.remove("hidden");
  }
}

function appendMessage(role, payload) {
  if (chatEmptyState) {
    chatEmptyState.classList.add("hidden");
  }

  const text = payload.message ?? payload.text;
  const { user, type, part } = payload;
  const ai_response = payload.ai_response ?? payload.api_results?.groq?.response ?? "";
  const container = document.createElement("div");
  container.className = `chat-message ${role === "user" ? "user" : "ai"} flex`;

  const isAttack = type === "attack" || part === "failure";
  const bubble = document.createElement("div");
  bubble.className =
    "chat-bubble rounded-lg border px-3 py-2 text-xs shadow-sm " +
    (role === "user" ? "user" : "ai");

  const meta = document.createElement("div");
  meta.className = "flex items-center justify-between mb-1";

  const nameSpan = document.createElement("span");
  nameSpan.className = "font-semibold text-[11px] text-slate-200";
  nameSpan.textContent = role === "user" ? user || "User" : "AI (Groq)";

  const tagSpan = document.createElement("span");
  tagSpan.className = "attack-badge inline-flex items-center gap-1";
  if (role === "user" && isAttack) {
    tagSpan.innerHTML =
      '<span class="mr-1">🚨</span><span class="text-[10px] text-rose-300 uppercase tracking-wide">Escalating</span>';
  } else {
    tagSpan.innerHTML =
      '<span class="text-[10px] text-slate-500 uppercase tracking-wide">' +
      (role === "user" ? (part || type || "User") : "AI Response") +
      "</span>";
  }

  meta.appendChild(nameSpan);
  meta.appendChild(tagSpan);

  const body = document.createElement("div");
  body.className = "text-slate-100 leading-relaxed";
  body.innerHTML = escapeHtml(role === "user" ? (text || "") : (ai_response || ""));

  bubble.appendChild(meta);
  bubble.appendChild(body);
  container.appendChild(bubble);

  chatWindow.appendChild(container);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function getToolColor(detected) {
  return detected === true
    ? "bg-rose-500/20 text-rose-300 border-rose-500/60"
    : detected === "warning"
    ? "bg-amber-500/20 text-amber-200 border-amber-500/60"
    : "bg-emerald-500/15 text-emerald-200 border-emerald-400/60";
}

function updateToolStatus(turnObj, summary) {
  toolStatusList.innerHTML = "";
  if (!turnObj || !turnObj.api_results) {
    return;
  }

  const api = turnObj.api_results;
  const tools = [
    ["Claude", api.claude, summary ? summary.claude_detection_turn : null],
    ["Groq", api.groq, summary ? summary.groq_detection_turn : null],
    ["Gemini", api.gemini, summary ? summary.gemini_detection_turn : null],
  ];

  tools.forEach(([label, res, firstDetect]) => {
    if (!res) return;
    const detected =
      res.detected || res.flagged || res.refused
        ? true
        : turnObj.part === "edge"
        ? "warning"
        : false;
    const colorClass = getToolColor(detected);

    const el = document.createElement("div");
    el.className =
      "flex items-center justify-between rounded-md border px-2.5 py-1.5 " +
      colorClass;

    const left = document.createElement("div");
    left.className = "flex flex-col";
    const title = document.createElement("span");
    title.className = "api-pill font-semibold uppercase";
    title.textContent = label;
    const detail = document.createElement("span");
    detail.className = "text-[10px] text-slate-200/80";

    if (label === "Claude" || label === "Groq" || label === "Gemini") {
      detail.textContent = res.refused || res.detected
        ? "Refused / blocked"
        : "Responded normally";
    }

    left.appendChild(title);
    left.appendChild(detail);

    const right = document.createElement("div");
    right.className = "text-[10px] text-slate-100 font-mono";
    right.textContent =
      detected === true ? "DETECTED" : detected === "warning" ? "RISK" : "CLEAR";

    if (firstDetect && turnObj.turn === firstDetect) {
      const badge = document.createElement("div");
      badge.className =
        "mt-1 text-[9px] text-emerald-200 uppercase tracking-wide";
      badge.textContent = "First detection";
      left.appendChild(badge);
    }

    el.appendChild(left);
    el.appendChild(right);
    toolStatusList.appendChild(el);
  });
}

function updateTimeline(turnIndex) {
  if (!currentScenarioData) return;
  const total = currentScenarioData.total_turns || currentScenarioData.results.length;
  const currentTurn =
    currentScenarioData.results[Math.min(turnIndex, total - 1)].turn;
  const percent = Math.round((currentTurn / total) * 100);

  timelineProgress.style.width = `${percent}%`;
  timelinePercent.textContent = `${percent}%`;
  timelineLabels.textContent = `Turn ${currentTurn}/${total}`;
}

function formatExpected(summary) {
  const c = summary.claude_expected;
  const g = summary.groq_expected;
  const ge = summary.gemini_expected;
  if (c != null || g != null || ge != null) {
    const parts = [];
    if (c != null) parts.push(`C:${c}`);
    if (g != null) parts.push(`G:${g}`);
    if (ge != null) parts.push(`Ge:${ge}`);
    return parts.join(" ");
  }
  return "-";
}

function updateSafetyHeader(turnObj) {
  if (!currentScenarioData || !turnObj) return;
  const summary = currentScenarioData.summary || {};
  currentTurnLabel.textContent = `Turn ${turnObj.turn}`;
  expectedLabel.textContent = formatExpected(summary);

  if (turnObj.type === "attack" || turnObj.part === "failure") {
    safetyStatus.classList.remove("border-slate-800");
    safetyStatus.classList.add("border-rose-500/70");
  } else {
    safetyStatus.classList.remove("border-rose-500/70");
    safetyStatus.classList.add("border-slate-800");
  }
}

function updateEta() {
  if (!currentScenarioData) {
    etaLabel.textContent = "ETA: -";
    return;
  }
  const remaining =
    currentScenarioData.results.length -
    (currentIndex ? Math.min(currentIndex, currentScenarioData.results.length) : 0);
  const speed = parseFloat(speedSelect.value || "2");
  const seconds = remaining * speed;
  if (!Number.isFinite(seconds) || seconds <= 0) {
    etaLabel.textContent = "ETA: Done";
    return;
  }

  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  etaLabel.textContent =
    "ETA: " + (mins > 0 ? `${mins}m ${secs}s` : `${secs}s`) + "";
}

async function loadScenario(id) {
  currentScenarioId = id;
  setPlaying(false);
  clearTimeout(playTimeout);
  currentIndex = 0;
  clearChat();
  toolStatusList.innerHTML = "";
  timelineProgress.style.width = "0%";
  timelinePercent.textContent = "0%";
  currentTurnLabel.textContent = "-";

  const path = SCENARIO_FILES[id];
  try {
    const res = await fetch(path);
    if (!res.ok) {
      throw new Error(`Failed to load scenario results: ${res.status}`);
    }
    currentScenarioData = await res.json();

    scenarioMeta.textContent = `${currentScenarioData.scenario_name} · ${currentScenarioData.total_turns} turns`;

    const summary = currentScenarioData.summary || {};
    expectedLabel.textContent = formatExpected(summary);
    updateEta();
  } catch (err) {
    console.error(err);
    scenarioMeta.textContent = "Failed to load scenario data.";
  }
}

function stepPlayback() {
  if (!currentScenarioData) return;
  const results = currentScenarioData.results;
  if (!results || currentIndex >= results.length) {
    setPlaying(false);
    updateEta();
    return;
  }

  const turnObj = results[currentIndex];
  const summary = currentScenarioData.summary || {};

  appendMessage("user", turnObj);
  updateSafetyHeader(turnObj);
  updateTimeline(currentIndex);
  updateEta();

  safetyLoading.classList.remove("hidden");

  const speed = parseFloat(speedSelect.value || "2");
  const halfDelay = (speed * 1000) / 2;

  playTimeout = setTimeout(() => {
    appendMessage("ai", turnObj);
    safetyLoading.classList.add("hidden");
    updateToolStatus(turnObj, summary);

    currentIndex += 1;

    if (isPlaying) {
      playTimeout = setTimeout(() => {
        stepPlayback();
      }, halfDelay);
    } else {
      updateEta();
    }
  }, halfDelay);
}

function handlePlay() {
  if (!currentScenarioData) return;
  if (isPlaying) return;
  setPlaying(true);
  stepPlayback();
}

function handlePause() {
  setPlaying(false);
  clearTimeout(playTimeout);
  updateEta();
}

function handleReset() {
  setPlaying(false);
  clearTimeout(playTimeout);
  currentIndex = 0;
  clearChat();
  toolStatusList.innerHTML = "";
  timelineProgress.style.width = "0%";
  timelinePercent.textContent = "0%";
  currentTurnLabel.textContent = "-";
  safetyLoading.classList.add("hidden");
  updateEta();
}

function handleExport() {
  if (!currentScenarioData) return;
  const blob = new Blob([JSON.stringify(currentScenarioData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `scenario${currentScenarioId}_results_export.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

document.querySelectorAll(".scenario-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const id = Number(btn.dataset.scenario);
    document.querySelectorAll(".scenario-btn").forEach((b) => {
      b.classList.remove("active");
    });
    btn.classList.add("active");
    loadScenario(id);
  });
});

playBtn.addEventListener("click", handlePlay);
pauseBtn.addEventListener("click", handlePause);
resetBtn.addEventListener("click", handleReset);
exportBtn.addEventListener("click", handleExport);
speedSelect.addEventListener("change", () => {
  updateEta();
});

loadScenario(currentScenarioId);

