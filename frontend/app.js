const API = window.APP_CONFIG?.apiBaseUrl || "http://localhost:8000";
const state = { data: [], summary: null, messages: [], conversationId: null, conversations: [] };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json", ...options.headers }, ...options });
  if (!response.ok) {
    let message = `요청 실패 (${response.status})`;
    try { message = (await response.json()).detail || message; } catch (_) {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function toast(message) {
  const el = $("#toast"); el.textContent = message; el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function formatNumber(value) { return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value ?? 0); }

async function loadAll() {
  try {
    [state.data, state.summary, state.conversations] = await Promise.all([
      request("/api/data"), request("/api/data/summary"), request("/api/conversations")
    ]);
    $(".status span").textContent = "API 연결됨";
    renderSummary(); renderTable(); renderHistory(); drawChart();
  } catch (error) {
    $(".status span").textContent = "API 연결 실패"; toast(error.message);
  }
}

function renderSummary() {
  const s = state.summary; if (!s) return;
  $("#metric-period").textContent = s.period;
  $("#metric-average").textContent = formatNumber(s.metrics.average);
  $("#metric-trend").textContent = s.trend.split(" (")[0];
  $("#metric-count").textContent = `${s.count}개 데이터 · ${s.trend}`;
  $("#chart-caption").textContent = s.count ? `전체 평균 ${formatNumber(s.metrics.average)}, 최고 ${formatNumber(s.metrics.max)}이며 최근 흐름은 ${s.trend}입니다.` : "데이터를 추가하면 추세를 분석해 드려요.";
}

function renderTable() {
  $("#table-count").textContent = `${state.data.length}개`;
  $("#data-table").innerHTML = [...state.data].reverse().map(row => `<tr><td>${row.date}</td><td>${formatNumber(row.value)}</td><td>${escapeHtml(row.memo || "—")}</td><td><div class="row-actions"><button data-edit="${row.id}">수정</button><button data-delete="${row.id}">삭제</button></div></td></tr>`).join("") || `<tr><td colspan="4" class="empty">아직 데이터가 없습니다.</td></tr>`;
}

function renderHistory() {
  $("#history-list").innerHTML = state.conversations.map(item => `<article class="history-card"><div class="history-content" data-load="${item.id}"><h3>${escapeHtml(item.title)}</h3><p>${new Date(item.updated_at).toLocaleString("ko-KR")} · ${item.messages.length}개 메시지</p></div><button data-remove-conversation="${item.id}" aria-label="대화 삭제">✕</button></article>`).join("") || `<div class="empty">저장된 대화가 없습니다.</div>`;
}

function renderMessages() {
  $("#messages").innerHTML = state.messages.map(m => `<div class="message ${m.role}">${m.role === "assistant" ? '<div class="avatar">IM</div>' : ""}<div class="bubble">${escapeHtml(m.content)}</div></div>`).join("");
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function escapeHtml(text) { const div = document.createElement("div"); div.textContent = String(text); return div.innerHTML; }

function drawChart() {
  const canvas = $("#trend-chart"), ctx = canvas.getContext("2d"), points = state.data.slice(-30);
  const rect = canvas.getBoundingClientRect(), scale = window.devicePixelRatio || 1;
  canvas.width = rect.width * scale; canvas.height = rect.height * scale; ctx.scale(scale, scale);
  const w = rect.width, h = rect.height, pad = 35; ctx.clearRect(0, 0, w, h);
  if (points.length < 2) { ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--muted"); ctx.fillText("그래프를 표시하려면 데이터가 2개 이상 필요합니다.", pad, h / 2); return; }
  const values = points.map(p => Number(p.value)), min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
  const coords = values.map((v, i) => ({ x: pad + i * (w - pad * 2) / (values.length - 1), y: h - pad - (v - min) / range * (h - pad * 2) }));
  const styles = getComputedStyle(document.documentElement), line = styles.getPropertyValue("--green").trim(), grid = styles.getPropertyValue("--line").trim();
  ctx.strokeStyle = grid; ctx.lineWidth = 1; for (let i=0;i<4;i++){const y=pad+i*(h-pad*2)/3;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke()}
  const gradient = ctx.createLinearGradient(0,pad,0,h); gradient.addColorStop(0,"rgba(112,172,128,.28)");gradient.addColorStop(1,"rgba(112,172,128,0)");
  ctx.beginPath(); coords.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y)); ctx.lineTo(coords.at(-1).x,h-pad);ctx.lineTo(coords[0].x,h-pad);ctx.closePath();ctx.fillStyle=gradient;ctx.fill();
  ctx.beginPath();coords.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle=line;ctx.lineWidth=2.5;ctx.stroke();
  ctx.fillStyle=line;[coords[0],coords.at(-1)].forEach(p=>{ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fill()});
}

async function sendChat(question) {
  const input = $("#chat-message"), submit = $("#chat-form button"); input.disabled = submit.disabled = true;
  state.messages.push({ role: "user", content: question }); renderMessages();
  $("#messages").insertAdjacentHTML("beforeend", `<div id="typing" class="message assistant"><div class="avatar">IM</div><div class="bubble typing"><i></i><i></i><i></i></div></div>`);
  try {
    const history = state.messages.slice(0, -1);
    const result = await request("/api/chat", { method: "POST", body: JSON.stringify({ message: question, conversation_id: state.conversationId, messages: history }) });
    state.messages.push({ role: "assistant", content: result.answer }); state.conversationId = result.conversation_id; state.summary = result.summary;
    renderMessages(); renderSummary(); state.conversations = await request("/api/conversations"); renderHistory();
  } catch (error) { state.messages.push({ role: "assistant", content: `요청을 처리하지 못했어요. ${error.message}` }); renderMessages(); }
  finally { input.disabled = submit.disabled = false; input.focus(); }
}

$("#chat-form").addEventListener("submit", e => { e.preventDefault(); const value = $("#chat-message").value.trim(); if (!value) return; $("#chat-message").value = ""; sendChat(value); });
$$('#suggestions button').forEach(button => button.addEventListener("click", () => sendChat(button.textContent)));
$("#new-chat").addEventListener("click", () => { state.messages = []; state.conversationId = null; renderMessages(); toast("새 대화를 시작합니다."); });

$("#data-form").addEventListener("submit", async e => {
  e.preventDefault(); const id = $("#edit-id").value; const payload = { date: $("#data-date").value, value: Number($("#data-value").value), memo: $("#data-memo").value.trim() };
  try { await request(id ? `/api/data/${id}` : "/api/data", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) }); resetDataForm(); await loadAll(); $("#form-feedback").textContent = id ? "수정되었습니다." : "저장되었습니다."; }
  catch (error) { $("#form-feedback").textContent = error.message; }
});

$("#data-table").addEventListener("click", async e => {
  const editId = e.target.dataset.edit, deleteId = e.target.dataset.delete;
  if (editId) { const row = state.data.find(item => item.id === editId); $("#edit-id").value=row.id;$("#data-date").value=row.date;$("#data-value").value=row.value;$("#data-memo").value=row.memo;$("#form-title").textContent="기록 수정";$("#cancel-edit").classList.remove("hidden"); }
  if (deleteId && confirm("이 기록을 삭제할까요?")) { try { await request(`/api/data/${deleteId}`, { method: "DELETE" }); await loadAll(); toast("삭제되었습니다."); } catch(error){toast(error.message);} }
});
function resetDataForm(){ $("#data-form").reset();$("#edit-id").value="";$("#form-title").textContent="새 기록 추가";$("#cancel-edit").classList.add("hidden");$("#data-date").valueAsDate=new Date(); }
$("#cancel-edit").addEventListener("click", resetDataForm);

$("#history-list").addEventListener("click", async e => {
  const loadId = e.target.closest("[data-load]")?.dataset.load, removeId = e.target.dataset.removeConversation;
  if (loadId) { try { const item=await request(`/api/conversations/${loadId}`);state.messages=item.messages;state.conversationId=item.id;renderMessages();showView("chat"); } catch(error){toast(error.message);} }
  if (removeId && confirm("이 대화를 삭제할까요?")) { try{await request(`/api/conversations/${removeId}`,{method:"DELETE"});state.conversations=await request("/api/conversations");renderHistory();toast("대화를 삭제했습니다.");}catch(error){toast(error.message);} }
});

function showView(name){ $$(".view").forEach(v=>v.classList.toggle("active",v.id===`${name}-view`));$$('.nav-item').forEach(n=>n.classList.toggle("active",n.dataset.view===name));$("#page-title").textContent={chat:"오늘의 데이터, 더 명확하게",data:"기록을 쌓아 인사이트로",history:"지난 인사이트 다시 보기"}[name]; }
$$('.nav-item').forEach(button=>button.addEventListener("click",()=>showView(button.dataset.view)));
$("#refresh-button").addEventListener("click",loadAll);
$("#theme-toggle").addEventListener("click",()=>{const dark=document.documentElement.dataset.theme!=="dark";document.documentElement.dataset.theme=dark?"dark":"";localStorage.setItem("theme",dark?"dark":"light");$("#theme-toggle").textContent=dark?"☀ 라이트 모드":"☾ 다크 모드";drawChart();});
if(localStorage.getItem("theme")==="dark") $("#theme-toggle").click();
$("#export-button").addEventListener("click",()=>{const rows=[["date","value","memo"],...state.data.map(r=>[r.date,r.value,r.memo])];const csv="\ufeff"+rows.map(row=>row.map(v=>`"${String(v??"").replaceAll('"','""')}"`).join(",")).join("\n");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));a.download="insight-data.csv";a.click();URL.revokeObjectURL(a.href);});
window.addEventListener("resize",drawChart); resetDataForm(); loadAll();
