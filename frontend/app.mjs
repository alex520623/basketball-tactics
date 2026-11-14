import { validateManifest, validateClip, frameAtTime, pointFor, trailSegments,
  courtTransform, clockText, elapsedText } from "/model.mjs";

const byId = id => document.getElementById(id);
const canvas = byId("court"), ctx = canvas.getContext("2d");
const state = { manifest: null, clip: null, cursor: 0, playing: false, selected: null, raf: 0,
  lastTick: null, loadId: 0, controller: null, colors: new Map(), rows: new Map(), playerTeams: new Map() };
const palette = ["#177953", "#8054b5", "#52788b", "#ad7155"];
const controls = ["show-trails", "flip-y", "timeline", "reset", "previous", "play", "next", "speed", "trail-window", "clear-selection"];
const colorFor = id => state.colors.get(id) ?? "#758180";
const nameFor = p => [p.first_name, p.last_name].filter(Boolean).join(" ") || p.player_id;
const warningNames = { OUT_OF_COURT: "場外位置", MISSING_BALL: "缺少球位置", PLAYER_COUNT: "球員資料不完整",
  INVALID_COORDINATE: "位置資料異常", TIME_GAP: "時間間隙", TIMESTAMP_ROLLBACK: "時間回退" };

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setEnabled(enabled) {
  for (const id of controls) byId(id).disabled = !enabled;
  if (enabled && state.clip?.timeline.duration_ms === 0) byId("play").disabled = true;
}

function pause() {
  state.playing = false;
  state.lastTick = null;
  cancelAnimationFrame(state.raf);
  byId("play").textContent = "▶ 播放";
}

function setTime(time, shouldPause = true) {
  if (!state.clip) return;
  if (shouldPause) pause();
  state.cursor = Math.max(0, Math.min(time, state.clip.timeline.duration_ms));
  render();
}

function tick(now) {
  if (!state.playing) return;
  const delta = state.lastTick === null ? 0 : now - state.lastTick;
  state.lastTick = now;
  setTime(state.cursor + delta * Number(byId("speed").value), false);
  if (state.cursor >= state.clip.timeline.duration_ms) pause();
  else state.raf = requestAnimationFrame(tick);
}

function togglePlay() {
  if (!state.clip || state.clip.timeline.duration_ms === 0) return;
  if (state.playing) return pause();
  if (state.cursor >= state.clip.timeline.duration_ms) state.cursor = 0;
  state.playing = true;
  state.lastTick = null;
  byId("play").textContent = "❚❚ 暫停";
  state.raf = requestAnimationFrame(tick);
}

function buildRoster() {
  const clip = state.clip;
  state.rows.clear();
  const roster = byId("roster"); roster.replaceChildren();
  const firstTeam = new Map();
  for (const frame of clip.frames) for (const p of frame.players) if (!firstTeam.has(p.player_id)) firstTeam.set(p.player_id, p.team_id);
  state.playerTeams = firstTeam;
  const groups = new Map(clip.teams.map(t => [t.team_id, { team: t, players: [] }]));
  for (const player of clip.players) {
    const tid = firstTeam.get(player.player_id);
    if (!groups.has(tid)) groups.set(tid, { team: { team_id: tid, abbreviation: tid ?? "未知", side: null }, players: [] });
    groups.get(tid).players.push(player);
  }
  const legend = byId("team-legend"); legend.replaceChildren();
  for (const { team, players } of groups.values()) {
    const color = colorFor(team.team_id);
    const label = element("span"); const dot = element("i"); dot.style.background = color;
    label.append(dot, document.createTextNode(team.abbreviation || team.team_id)); legend.append(label);
    const group = element("div", "team-group"), heading = element("div", "team-heading"), mark = element("i"); mark.style.background = color;
    heading.append(mark, document.createTextNode(team.side === "home" ? "主隊" : team.side === "visitor" ? "客隊" : "隊伍未知"), element("strong", "", team.abbreviation || team.team_id));
    group.append(heading);
    players.sort((a, b) => (Number(a.jersey) || 0) - (Number(b.jersey) || 0));
    for (const player of players) {
      const button = element("button", "player-row"); button.type = "button";
      button.setAttribute("aria-pressed", "false"); button.setAttribute("aria-label", `選取 ${nameFor(player)}，球衣 ${player.jersey ?? "未知"}`);
      const jersey = element("span", "jersey", player.jersey ?? "?"); jersey.style.background = color;
      const text = element("span"), name = element("span", "player-name", nameFor(player)), coordinates = element("span", "player-coordinates", "—");
      text.append(name, coordinates); button.append(jersey, text, element("span", "player-position", player.position ?? "—"));
      button.addEventListener("click", () => { state.selected = state.selected === player.player_id ? null : player.player_id; render(); });
      group.append(button); state.rows.set(player.player_id, { button, jersey, coordinates });
    }
    roster.append(group);
  }
  const ballLegend = element("span"), ballDot = element("i"); ballDot.style.background = "#df8d36";
  ballLegend.append(ballDot, document.createTextNode("球")); legend.append(ballLegend);
}

function buildWarnings() {
  const warnings = state.clip.quality?.warnings ?? [];
  byId("warnings-stat").textContent = String(warnings.length);
  byId("quality-description").textContent = warnings.length ? "場外與缺漏等觀測已保留紀錄。場外位置不自動夾回球場，也不推斷原因。" : "此片段沒有 Backend 品質警告；仍需核對來源方向與畫面。";
  byId("quality-summary").textContent = `查看 ${warnings.length} 筆警告紀錄`;
  const list = byId("warning-list"); list.replaceChildren();
  for (const warning of warnings) {
    const local = Number.isInteger(warning.frame_index) && warning.frame_index >= 0 && warning.frame_index < state.clip.frames.length;
    const button = element("button", "warning-row", `${local ? `影格 ${warning.frame_index + 1}` : "來源事件"} · ${warningNames[warning.code] ?? warning.code}${warning.player_id ? ` · ID ${warning.player_id}` : ""}`);
    button.type = "button"; button.title = warning.message; button.disabled = !local;
    if (local) button.addEventListener("click", () => setTime(state.clip.frames[warning.frame_index].t_ms));
    list.append(button);
  }
}

function drawCourt(transform) {
  const court = state.clip?.coordinate_system ?? { court_length: 94, court_width: 50 };
  const topLeft = transform.map(0, byId("flip-y").checked ? court.court_width : 0);
  ctx.save(); ctx.translate(topLeft.x, topLeft.y); ctx.scale(transform.scale, transform.scale);
  ctx.fillStyle = "#f0e6d0"; ctx.fillRect(0, 0, court.court_length, court.court_width);
  ctx.strokeStyle = "#dcccae"; ctx.lineWidth = 0.08;
  for (let x = 0; x < court.court_length; x += 4) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, court.court_width); ctx.stroke(); }
  ctx.strokeStyle = "#aa987a"; ctx.lineWidth = 0.16; ctx.strokeRect(0, 0, court.court_length, court.court_width);
  if (court.court_length === 94 && court.court_width === 50) {
    ctx.beginPath(); ctx.moveTo(47, 0); ctx.lineTo(47, 50); ctx.stroke();
    ctx.beginPath(); ctx.arc(47, 25, 6, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(47, 25, 2, 0, Math.PI * 2); ctx.stroke();
    for (const mirrored of [false, true]) {
      ctx.save(); if (mirrored) { ctx.translate(94, 0); ctx.scale(-1, 1); }
      ctx.fillStyle = "#e5dac0"; ctx.fillRect(0, 17, 19, 16); ctx.strokeRect(0, 17, 19, 16);
      ctx.beginPath(); ctx.arc(19, 25, 6, -Math.PI / 2, Math.PI / 2); ctx.stroke();
      ctx.setLineDash([0.6, 0.6]); ctx.beginPath(); ctx.arc(19, 25, 6, Math.PI / 2, Math.PI * 1.5); ctx.stroke(); ctx.setLineDash([]);
      const angle = Math.asin(22 / 23.75), join = 5.25 + Math.sqrt(23.75 ** 2 - 22 ** 2);
      ctx.beginPath(); ctx.moveTo(0, 3); ctx.lineTo(join, 3); ctx.arc(5.25, 25, 23.75, -angle, angle); ctx.lineTo(0, 47); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(4, 22); ctx.lineTo(4, 28); ctx.stroke();
      ctx.strokeStyle = "#c58648"; ctx.beginPath(); ctx.arc(5.25, 25, 0.75, 0, Math.PI * 2); ctx.stroke(); ctx.strokeStyle = "#aa987a";
      ctx.beginPath(); ctx.arc(5.25, 25, 4, -Math.PI / 2, Math.PI / 2); ctx.stroke();
      ctx.restore();
    }
  }
  ctx.restore();
  ctx.fillStyle = "#a79e86"; ctx.font = '10px "Segoe UI", sans-serif'; ctx.textAlign = "center";
  for (const x of [0, court.court_length / 2, court.court_length]) { const p = transform.map(x, byId("flip-y").checked ? -3 : court.court_width + 3); ctx.fillText(`${x} ft`, p.x, p.y); }
}

function draw(frameIndex) {
  const box = canvas.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = box.width, height = box.height;
  const pixelWidth = Math.round(width * dpr), pixelHeight = Math.round(height * dpr);
  if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) { canvas.width = pixelWidth; canvas.height = pixelHeight; }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, width, height);
  const court = state.clip?.coordinate_system ?? { court_length: 94, court_width: 50 };
  const transform = courtTransform(width, height, court, byId("flip-y").checked);
  drawCourt(transform);
  if (!state.clip) return;
  const frame = state.clip.frames[frameIndex];
  if (byId("show-trails").checked) {
    const windowMs = byId("trail-window").value === "all" ? state.clip.timeline.duration_ms + 1 : Number(byId("trail-window").value);
    for (const track of state.clip.trajectories) {
      const current = pointFor(frame, track.entity_type, track.entity_id);
      const color = track.entity_type === "ball" ? "#df8d36" : colorFor(current?.team_id ?? state.playerTeams.get(track.entity_id));
      ctx.strokeStyle = color; ctx.lineWidth = state.selected === track.entity_id ? 2.8 : 1.6;
      ctx.globalAlpha = state.selected && track.entity_type === "player" && state.selected !== track.entity_id ? 0.12 : 0.45;
      for (const path of trailSegments(state.clip, track, frameIndex, windowMs)) {
        ctx.beginPath(); path.forEach((point, index) => { const p = transform.map(point.x, point.y); index ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); }); ctx.stroke();
      }
    }
  }
  ctx.globalAlpha = 1;
  for (const point of frame.players) {
    const p = transform.map(point.x, point.y), meta = state.clip.players.find(row => row.player_id === point.player_id);
    const selected = state.selected === point.player_id, radius = Math.max(6, transform.scale * 1.15);
    ctx.globalAlpha = state.selected && !selected ? 0.55 : 1;
    if (selected) { ctx.strokeStyle = colorFor(point.team_id); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(p.x, p.y, radius + 4, 0, Math.PI * 2); ctx.stroke(); }
    ctx.fillStyle = colorFor(point.team_id); ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.8;
    ctx.beginPath(); ctx.arc(p.x, p.y, radius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "white"; ctx.font = `600 ${Math.max(9, radius * 1.05)}px "Segoe UI", sans-serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(meta?.jersey ?? "?", p.x, p.y + 0.5);
  }
  ctx.globalAlpha = 1;
  if (frame.ball) { const p = transform.map(frame.ball.x, frame.ball.y); ctx.fillStyle = "#e58b31"; ctx.strokeStyle = "white"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(4, transform.scale * 0.65), 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
  ctx.textBaseline = "alphabetic";
}

function render() {
  if (!state.clip) return draw(0);
  const index = frameAtTime(state.clip.frames, state.cursor), frame = state.clip.frames[index];
  byId("timeline").value = String(state.cursor); byId("elapsed").textContent = elapsedText(state.cursor);
  byId("frame-counter").textContent = `影格 ${index + 1} / ${state.clip.frames.length}`;
  byId("period-label").textContent = frame.period <= 4 ? `Q${frame.period}` : `OT${frame.period - 4}`;
  byId("game-clock").textContent = clockText(frame.game_clock_s);
  byId("shot-clock").textContent = Number.isFinite(frame.shot_clock_s) ? frame.shot_clock_s.toFixed(2) : "—";
  byId("previous").disabled = index === 0; byId("next").disabled = index === state.clip.frames.length - 1;
  byId("orientation-note").textContent = `來源方向${state.clip.coordinate_system.display_orientation === "unconfirmed" ? "未確認" : "依 metadata"} · ${byId("flip-y").checked ? "y 向上" : "y 向下"}檢視`;
  for (const [pid, row] of state.rows) {
    const point = frame.players.find(p => p.player_id === pid);
    row.button.setAttribute("aria-pressed", String(state.selected === pid));
    row.coordinates.textContent = point ? `x ${point.x.toFixed(1)} · y ${point.y.toFixed(1)} ft` : "此影格缺少位置";
    if (point) row.jersey.style.background = colorFor(point.team_id);
  }
  byId("ball-info").textContent = frame.ball ? `x ${frame.ball.x.toFixed(1)} · y ${frame.ball.y.toFixed(1)} ft` : "此影格缺少位置";
  const count = (state.clip.quality?.warnings ?? []).filter(w => w.frame_index === index).length;
  byId("current-quality").textContent = count ? `此影格 ${count} 則` : "目前無警告";
  byId("current-quality").classList.toggle("warning", count > 0);
  draw(index);
}

async function fetchJson(url, signal) {
  const response = await fetch(url, { cache: "no-store", signal });
  if (!response.ok) throw new Error(`無法載入片段資料（HTTP ${response.status}）。`);
  return response.json();
}

async function loadClip(clipId) {
  pause(); state.controller?.abort(); state.controller = new AbortController();
  const loadId = ++state.loadId; const status = byId("load-status");
  status.hidden = false; status.className = "load-status"; status.textContent = "正在載入真實片段…";
  setEnabled(false);
  try {
    const entry = state.manifest.clips.find(row => row.clip_id === clipId);
    const clip = validateClip(await fetchJson(new URL(entry.path, new URL("/data/manifest.json", location.href)), state.controller.signal), entry);
    if (loadId !== state.loadId) return;
    state.clip = clip; state.cursor = 0; state.selected = null;
    state.colors = new Map(clip.teams.map((team, index) => [team.team_id, palette[index % palette.length]]));
    const home = clip.teams.find(t => t.side === "home"), away = clip.teams.find(t => t.side === "visitor");
    byId("match-title").textContent = `${away?.abbreviation ?? "客隊"} @ ${home?.abbreviation ?? "主隊"}`;
    byId("match-description").textContent = `${clip.game?.game_date ?? "日期未知"} · event ${clip.source_event?.event_id ?? "—"} · 真實追蹤片段`;
    byId("duration-stat").textContent = `${(entry.duration_ms / 1000).toFixed(2)} s`;
    byId("frames-stat").textContent = String(clip.frames.length); byId("players-stat").textContent = `${clip.players.length} 位球員 · 球位置依觀測顯示`;
    byId("timeline").max = String(clip.timeline.duration_ms); byId("total-time").textContent = elapsedText(clip.timeline.duration_ms);
    buildRoster(); buildWarnings(); setEnabled(true); render(); status.hidden = true;
  } catch (error) {
    if (error.name === "AbortError" || loadId !== state.loadId) return;
    state.clip = null; state.rows.clear(); byId("roster").replaceChildren(); draw(0);
    status.hidden = false; status.className = "load-status error"; status.textContent = `${error.message} 請確認本機匯出資料與 JSON 0.2.0 規格。`;
  }
}

byId("play").addEventListener("click", togglePlay);
byId("reset").addEventListener("click", () => setTime(0));
byId("previous").addEventListener("click", () => { if (state.clip) setTime(state.clip.frames[Math.max(0, frameAtTime(state.clip.frames, state.cursor) - 1)].t_ms); });
byId("next").addEventListener("click", () => { if (state.clip) setTime(state.clip.frames[Math.min(state.clip.frames.length - 1, frameAtTime(state.clip.frames, state.cursor) + 1)].t_ms); });
byId("timeline").addEventListener("input", event => setTime(Number(event.target.value)));
for (const id of ["show-trails", "flip-y", "trail-window"]) byId(id).addEventListener("change", render);
byId("speed").addEventListener("change", () => { state.lastTick = null; });
byId("clear-selection").addEventListener("click", () => { state.selected = null; render(); });
byId("clip-select").addEventListener("change", event => loadClip(event.target.value));
document.addEventListener("visibilitychange", () => { if (document.hidden) pause(); });
document.addEventListener("keydown", event => { if (event.code === "Space" && [document.body, canvas].includes(event.target)) { event.preventDefault(); togglePlay(); } });
canvas.addEventListener("click", event => {
  if (!state.clip) return;
  const box = canvas.getBoundingClientRect(), transform = courtTransform(box.width, box.height, state.clip.coordinate_system, byId("flip-y").checked);
  const frame = state.clip.frames[frameAtTime(state.clip.frames, state.cursor)];
  const nearest = frame.players.map(p => { const screen = transform.map(p.x, p.y); return { point: p, distance: Math.hypot(screen.x - (event.clientX - box.left), screen.y - (event.clientY - box.top)) }; }).sort((a, b) => a.distance - b.distance)[0];
  state.selected = nearest && nearest.distance <= Math.max(12, transform.scale * 1.5) ? nearest.point.player_id : null; render();
});
new ResizeObserver(render).observe(canvas);

try {
  state.manifest = validateManifest(await fetchJson("/data/manifest.json"));
  const select = byId("clip-select"); select.replaceChildren();
  for (const entry of state.manifest.clips) { const option = element("option", "", entry.label); option.value = entry.clip_id; select.append(option); }
  select.disabled = false; await loadClip(select.value);
} catch (error) {
  const status = byId("load-status"); status.hidden = false; status.className = "load-status error";
  status.textContent = `${error.message} 請先準備 Backend 匯出的片段資料。`; draw(0);
}
