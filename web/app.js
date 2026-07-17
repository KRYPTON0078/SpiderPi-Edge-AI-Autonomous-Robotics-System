(function () {
  const els = {
    robotIp: document.getElementById("robot-ip"),
    apiStatus: document.getElementById("api-status"),
    cameraStatus: document.getElementById("camera-status"),
    missionStatus: document.getElementById("mission-status"),
    lastCommand: document.getElementById("last-command"),
    voiceStatus: document.getElementById("voice-status"),
    voiceText: document.getElementById("voice-text"),
    speed: document.getElementById("speed"),
    voicePermission: document.getElementById("voice-permission"),
    voiceToggle: document.getElementById("voice-toggle"),
    cameraRefresh: document.getElementById("camera-refresh"),
    cameraFeed: document.getElementById("camera-feed"),
    missionPrompt: document.getElementById("mission-prompt"),
    missionPlan: document.getElementById("mission-plan"),
    missionStart: document.getElementById("mission-start"),
    missionStop: document.getElementById("mission-stop"),
    missionPlanView: document.getElementById("mission-plan-view"),
    missionLogView: document.getElementById("mission-log-view"),
  };

  const robotHost = window.location.hostname;
  els.robotIp.textContent = robotHost || "unknown";
  const localSnapshotBase = "/api/camera.jpg?t=";
  let cameraTimer = null;

  function refreshCameraFrame() {
    els.cameraFeed.src = localSnapshotBase + Date.now();
  }

  function startCameraLoop() {
    if (cameraTimer) {
      window.clearInterval(cameraTimer);
    }
    refreshCameraFrame();
    cameraTimer = window.setInterval(refreshCameraFrame, 700);
  }

  els.cameraFeed.addEventListener("error", () => {
    els.cameraStatus.textContent = "offline";
  });
  els.cameraFeed.addEventListener("load", () => {
    els.cameraStatus.textContent = "ok";
  });

  async function apiCommand(command) {
    const payload = {
      command: command,
      speed: els.speed.value || "low",
    };
    try {
      const resp = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      els.lastCommand.textContent = command;
      if (!resp.ok || !data.ok) {
        els.apiStatus.textContent = "error";
        console.error("command failed", data);
      } else {
        els.apiStatus.textContent = "ok";
      }
    } catch (err) {
      els.apiStatus.textContent = "offline";
      console.error(err);
    }
  }

  let plannedMission = null;

  async function postJson(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const data = await resp.json();
    return { resp, data };
  }

  function renderPlan(plan) {
    if (!plan) {
      els.missionPlanView.textContent = "No plan generated yet.";
      return;
    }
    els.missionPlanView.textContent = JSON.stringify(plan, null, 2);
  }

  function renderMissionLogs(mission) {
    if (!mission || !mission.logs || !mission.logs.length) {
      els.missionLogView.textContent = "Mission logs will appear here.";
      return;
    }
    els.missionLogView.textContent = mission.logs.join("\n");
  }

  async function planMission() {
    const prompt = (els.missionPrompt.value || "").trim();
    if (!prompt) {
      els.missionStatus.textContent = "enter a mission prompt first";
      return;
    }
    els.missionStatus.textContent = "planning...";
    try {
      const { resp, data } = await postJson("/api/mission/plan", { prompt });
      if (!resp.ok || !data.ok) {
        els.missionStatus.textContent = "plan error";
        els.missionLogView.textContent = JSON.stringify(data, null, 2);
        return;
      }
      plannedMission = data.plan;
      renderPlan(plannedMission);
      els.missionStatus.textContent = "planned (" + data.planner + ")";
    } catch (err) {
      els.missionStatus.textContent = "plan offline";
    }
  }

  async function startMission() {
    if (!plannedMission) {
      els.missionStatus.textContent = "no planned mission";
      return;
    }
    els.missionStatus.textContent = "starting mission...";
    try {
      const { resp, data } = await postJson("/api/mission/start", { plan: plannedMission });
      if (!resp.ok || !data.ok) {
        els.missionStatus.textContent = "start error";
        els.missionLogView.textContent = JSON.stringify(data, null, 2);
        return;
      }
      els.missionStatus.textContent = "running";
      renderMissionLogs(data.mission);
    } catch (err) {
      els.missionStatus.textContent = "start offline";
    }
  }

  async function stopMission() {
    try {
      const { data } = await postJson("/api/mission/stop", {});
      if (data && data.ok) {
        els.missionStatus.textContent = "stop requested";
        renderMissionLogs(data.mission);
      }
    } catch (err) {
      els.missionStatus.textContent = "stop failed";
    }
  }

  function normalizeVoiceCommand(text) {
    const t = text.toLowerCase();
    if (t.includes("move right") || t.includes("right")) return "right";
    if (t.includes("move left") || t.includes("left")) return "left";
    if (t.includes("forward") || t.includes("go ahead")) return "forward";
    if (t.includes("back") || t.includes("reverse")) return "back";
    if (t.includes("stop")) return "stop";
    if (t.includes("stand")) return "stand";
    if (t.includes("wave")) return "wave";
    if (t.includes("dance")) return "dance";
    if (t.includes("kick")) return "kick";
    if (t.includes("patrol")) return "patrol";
    if (t.includes("auto avoid") || t.includes("avoidance")) return "autoavoid";
    return null;
  }

  async function checkHealth() {
    try {
      const resp = await fetch("/api/health");
      const data = await resp.json();
      els.apiStatus.textContent = data.ok ? "ok" : "error";
    } catch (err) {
      els.apiStatus.textContent = "offline";
    }
  }

  async function pollMissionStatus() {
    try {
      const resp = await fetch("/api/mission/status");
      const data = await resp.json();
      if (!resp.ok || !data.ok) return;
      const mission = data.mission;
      if (mission.running) {
        els.missionStatus.textContent = "running: " + mission.current_step_name;
      } else {
        els.missionStatus.textContent = mission.last_result || "idle";
      }
      renderMissionLogs(mission);
    } catch (err) {
      // Keep silent to avoid UI noise.
    }
  }

  async function ensureMode() {
    try {
      await fetch("/api/ensure_mode");
    } catch (err) {
      console.error("ensure mode failed", err);
    }
  }

  function addPressHandler(element, handler) {
    if (!element) return;
    let touchHandled = false;
    element.addEventListener("touchstart", (event) => {
      touchHandled = true;
      event.preventDefault();
      handler();
    }, { passive: false });
    element.addEventListener("click", (event) => {
      if (touchHandled) {
        touchHandled = false;
        event.preventDefault();
        return;
      }
      handler();
    });
  }

  document.querySelectorAll("button[data-cmd]").forEach((btn) => {
    addPressHandler(btn, () => {
      apiCommand(btn.dataset.cmd);
    });
  });

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let voiceRunning = false;

  async function requestMicPermission() {
    try {
      // Some mobile browsers expose SpeechRecognition but not mediaDevices.
      // In that case, try recognition start directly on user gesture.
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (recognition) {
          els.voiceStatus.textContent = "mic api unavailable, trying direct voice start";
          return true;
        }
        els.voiceStatus.textContent = "mic api unavailable";
        return false;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      els.voiceStatus.textContent = "mic permission granted";
      return true;
    } catch (err) {
      els.voiceStatus.textContent = "mic denied: " + (err && err.name ? err.name : "error");
      return false;
    }
  }

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      voiceRunning = true;
      els.voiceStatus.textContent = "listening";
      els.voiceToggle.textContent = "Stop Voice";
    };

    recognition.onend = () => {
      voiceRunning = false;
      els.voiceStatus.textContent = "idle";
      els.voiceToggle.textContent = "Start Voice";
    };

    recognition.onerror = (e) => {
      els.voiceStatus.textContent = "error: " + (e.error || "unknown");
    };

    recognition.onresult = (event) => {
      const last = event.results[event.results.length - 1];
      if (!last || !last[0]) return;
      const transcript = last[0].transcript.trim();
      els.voiceText.textContent = transcript;
      const cmd = normalizeVoiceCommand(transcript);
      if (cmd) apiCommand(cmd);
    };
  } else {
    els.voiceStatus.textContent = "unsupported in this browser";
    els.voiceToggle.disabled = true;
  }

  addPressHandler(els.voicePermission, () => {
    requestMicPermission();
  });

  addPressHandler(els.cameraRefresh, () => {
    refreshCameraFrame();
  });

  addPressHandler(els.missionPlan, () => {
    planMission();
  });

  addPressHandler(els.missionStart, () => {
    startMission();
  });

  addPressHandler(els.missionStop, () => {
    stopMission();
  });

  addPressHandler(els.voiceToggle, async () => {
    if (!recognition) return;
    if (voiceRunning) {
      recognition.stop();
    } else {
      const ok = await requestMicPermission();
      if (!ok) return;
      recognition.start();
    }
  });

  checkHealth();
  pollMissionStatus();
  ensureMode();
  startCameraLoop();
  window.setInterval(checkHealth, 5000);
  window.setInterval(pollMissionStatus, 1500);
})();
