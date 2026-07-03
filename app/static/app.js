const state = {
  messages: [],
  latestChat: null,
  latestProfile: null,
  latestReport: null,
};

const elements = {
  errorBanner: document.getElementById("errorBanner"),
  userIdInput: document.getElementById("userIdInput"),
  conversationIdInput: document.getElementById("conversationIdInput"),
  messageForm: document.getElementById("messageForm"),
  messageInput: document.getElementById("messageInput"),
  messageList: document.getElementById("messageList"),
  sendButton: document.getElementById("sendButton"),
  clearButton: document.getElementById("clearButton"),
  riskSummary: document.getElementById("riskSummary"),
  suggestedActions: document.getElementById("suggestedActions"),
  followUpQuestions: document.getElementById("followUpQuestions"),
  profileButton: document.getElementById("profileButton"),
  profilePanel: document.getElementById("profilePanel"),
  reportButton: document.getElementById("reportButton"),
  reportPanel: document.getElementById("reportPanel"),
};

const riskLabels = [
  ["depression_risk", "抑郁"],
  ["anxiety_risk", "焦虑"],
  ["sleep_risk", "睡眠"],
  ["crisis_level", "危机"],
  ["function_impairment_level", "功能受损"],
];

function getIdentity() {
  return {
    userId: elements.userIdInput.value.trim(),
    conversationId: elements.conversationIdInput.value.trim(),
  };
}

function showError(message) {
  elements.errorBanner.textContent = message;
  elements.errorBanner.hidden = false;
}

function clearError() {
  elements.errorBanner.textContent = "";
  elements.errorBanner.hidden = true;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `请求失败：${response.status}`);
  }

  return response.json();
}

function setButtonLoading(button, loading, label) {
  if (loading) {
    button.dataset.label = button.textContent;
    button.textContent = label;
    button.disabled = true;
    return;
  }

  button.textContent = button.dataset.label || button.textContent;
  button.disabled = false;
}

function appendMessage(role, text, crisisLevel = "s0") {
  state.messages.push({ role, text, crisisLevel });
  renderMessages();
}

function renderMessages() {
  const initial = state.messages.length === 0
    ? [{
      role: "assistant",
      text: "你好，我可以陪你梳理最近的压力、情绪和睡眠情况。你可以从一句真实感受开始。",
      crisisLevel: "s0",
    }]
    : state.messages;

  elements.messageList.innerHTML = initial.map((message) => {
    const crisisClass = message.role === "assistant" && ["s2", "s3", "s4"].includes(message.crisisLevel)
      ? " crisis"
      : "";
    const roleLabel = message.role === "user" ? "你" : "助手";
    return `
      <article class="message ${message.role}${crisisClass}">
        <span>${roleLabel}</span>
        <p>${escapeHtml(message.text)}</p>
      </article>
    `;
  }).join("");
  elements.messageList.scrollTop = elements.messageList.scrollHeight;
}

function renderRisk(summary = {}) {
  elements.riskSummary.innerHTML = riskLabels.map(([key, label]) => {
    const value = summary[key] || "unknown";
    const alertClass = key === "crisis_level" && ["s2", "s3", "s4"].includes(value)
      ? " class=\"crisis-alert\""
      : "";
    return `<div${alertClass}><dt>${label}</dt><dd>${escapeHtml(value)}</dd></div>`;
  }).join("");
}

function renderList(element, items, emptyText) {
  const values = Array.isArray(items) && items.length > 0 ? items : [emptyText];
  element.innerHTML = values.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderChatStatus(response) {
  renderRisk(response.risk_summary);
  renderList(elements.suggestedActions, response.suggested_actions, "暂无建议行动。");
  renderList(elements.followUpQuestions, response.follow_up_questions, "暂无追问问题。");
}

function renderProfile(profile) {
  const categories = Object.entries(profile.profile || {})
    .filter(([, values]) => Array.isArray(values) && values.length > 0)
    .map(([key, values]) => `<li><strong>${escapeHtml(key)}</strong>: ${escapeHtml(values.join("、"))}</li>`)
    .join("");

  elements.profilePanel.innerHTML = `
    <p><strong>摘要：</strong>${escapeHtml(profile.latest_summary || "暂无摘要。")}</p>
    ${categories ? `<ul>${categories}</ul>` : "<p>暂无分类画像。</p>"}
  `;
}

function renderReport(report) {
  const evidence = renderInlineList(report.evidence_summary, "暂无证据摘要。");
  const interventions = renderInlineList(report.recommended_interventions, "暂无干预建议。");
  const offlineHelp = report.offline_help_recommended ? "是" : "否";

  elements.reportPanel.innerHTML = `
    <p><strong>摘要：</strong>${escapeHtml(report.profile_summary || "暂无摘要。")}</p>
    <p><strong>线下求助建议：</strong>${offlineHelp}</p>
    <p><strong>证据：</strong></p>${evidence}
    <p><strong>干预：</strong></p>${interventions}
  `;

  if (report.risk_summary) {
    renderRisk(report.risk_summary);
  }
}

function renderInlineList(items, emptyText) {
  const values = Array.isArray(items) && items.length > 0 ? items : [emptyText];
  return `<ul>${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

async function sendMessage(event) {
  event.preventDefault();
  clearError();

  const { userId, conversationId } = getIdentity();
  const message = elements.messageInput.value.trim();
  if (!userId || !conversationId) {
    showError("请先填写用户 ID 和会话 ID。");
    return;
  }
  if (!message) {
    showError("请输入一条消息。");
    return;
  }

  appendMessage("user", message);
  elements.messageInput.value = "";
  setButtonLoading(elements.sendButton, true, "发送中");

  try {
    const response = await requestJson("/api/chat/messages", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        conversation_id: conversationId,
        message,
      }),
    });
    state.latestChat = response;
    appendMessage("assistant", response.assistant_message, response.risk_summary.crisis_level);
    renderChatStatus(response);
  } catch (error) {
    showError(`发送失败：${error.message}`);
  } finally {
    setButtonLoading(elements.sendButton, false);
  }
}

async function refreshProfile() {
  clearError();
  const { userId } = getIdentity();
  if (!userId) {
    showError("请先填写用户 ID。");
    return;
  }

  setButtonLoading(elements.profileButton, true, "刷新中");
  try {
    const profile = await requestJson(`/api/profile/${encodeURIComponent(userId)}`);
    state.latestProfile = profile;
    renderProfile(profile);
  } catch (error) {
    showError(`画像刷新失败：${error.message}`);
  } finally {
    setButtonLoading(elements.profileButton, false);
  }
}

async function generateReport() {
  clearError();
  const { userId } = getIdentity();
  if (!userId) {
    showError("请先填写用户 ID。");
    return;
  }

  setButtonLoading(elements.reportButton, true, "生成中");
  try {
    const report = await requestJson(`/api/report/${encodeURIComponent(userId)}/generate`, {
      method: "POST",
    });
    state.latestReport = report;
    renderReport(report);
  } catch (error) {
    showError(`报告生成失败：${error.message}`);
  } finally {
    setButtonLoading(elements.reportButton, false);
  }
}

function clearConversation() {
  state.messages = [];
  state.latestChat = null;
  clearError();
  renderMessages();
  renderRisk();
  renderList(elements.suggestedActions, [], "发送消息后显示后端建议。");
  renderList(elements.followUpQuestions, [], "发送消息后显示后端追问。");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

elements.messageForm.addEventListener("submit", sendMessage);
elements.profileButton.addEventListener("click", refreshProfile);
elements.reportButton.addEventListener("click", generateReport);
elements.clearButton.addEventListener("click", clearConversation);

renderRisk();
