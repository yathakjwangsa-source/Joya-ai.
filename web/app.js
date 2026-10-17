const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
const state = {
  lessons: [],
  activeTest: null,
  timer: null,
  toastTimer: null,
  userName: "Learner",
};

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.method && options.method !== "GET"
        ? { "X-CSRF-Token": $('meta[name="csrf-token"]').content }
        : {}),
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function notify(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
}

function showView(name) {
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${name}`));
  $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
  const labels = { home: "Overview", chat: "Ask Joya", learn: "Explore concepts", jee: "JEE practice", notes: "My notes" };
  $("#page-label").textContent = labels[name] || "Overview";
  $(".sidebar").classList.remove("open");
  if (name === "notes") loadNotes();
  if (name === "home") loadOverview();
}

function greet() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  $("#greeting").textContent = `${greeting}, ${state.userName}.`;
}

function setCsrfToken(token) {
  if (token) $('meta[name="csrf-token"]').content = token;
}

async function setAuthenticated(user) {
  const authScreen = $("#auth-screen");
  const appShell = $("#app-shell");
  if (!user.authenticated) {
    authScreen.classList.remove("hidden");
    appShell.classList.add("hidden");
    return;
  }

  setCsrfToken(user.csrf_token);
  state.userName = user.name || "Learner";
  $("#user-name").value = state.userName;
  greet();
  authScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
  await Promise.all([loadOverview(), loadLessons()]);
  try {
    const status = await api("/api/status");
    setAiStatus(status.available, status.message);
  } catch (error) {
    setAiStatus(false, error.message);
  }
}

async function submitAuthentication(event, action) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  const message = $("#auth-message");
  message.textContent = "";
  const submit = $('button[type="submit"]', form);
  submit.disabled = true;
  try {
    const user = await api(`/api/auth/${action}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setCsrfToken(user.csrf_token);
    form.reset();
    await setAuthenticated(user);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

async function loadOverview() {
  try {
    const data = await api("/api/bootstrap");
    $("#stat-lessons").textContent = data.lessons;
    $("#stat-notes").textContent = data.notes;
    $("#stat-tests").textContent = data.jee_tests;
    $("#stat-correct").textContent = data.jee_correct;
  } catch (error) {
    notify(error.message, true);
  }
}

function setAiStatus(available, message) {
  const status = $("#ai-status");
  const dot = $(".status-dot");
  status.textContent = available ? "Joya AI ready" : "AI needs setup";
  dot.classList.toggle("online", available);
  $("#chat-availability").textContent = message;
}

function appendMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "assistant" ? "J" : (localStorage.getItem("joya-name") || "Y").slice(0, 1).toUpperCase();
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.append(avatar, bubble);
  $("#chat-messages").append(row);
  row.scrollIntoView({ block: "nearest" });
  return bubble;
}

async function sendChat(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const prompt = input.value.trim();
  if (!prompt) return;
  appendMessage("user", prompt);
  const answerBubble = appendMessage("assistant", "Joya is thinking…");
  input.value = "";
  const button = $("#chat-form button");
  button.disabled = true;
  button.textContent = "Thinking…";
  let answer = "";
  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": $('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || "Joya could not answer that question.");
    }
    if (!response.body) throw new Error("This browser does not support streamed answers.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let warning = "";
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line.startsWith("data: ")) continue;
        const eventData = JSON.parse(line.slice(6));
        if (eventData.error) throw new Error(eventData.error);
        if (eventData.warning) warning = eventData.warning;
        if (eventData.token) {
          answer += eventData.token;
          answerBubble.textContent = answer;
          answerBubble.scrollIntoView({ block: "nearest" });
        }
      }
      if (done) break;
    }
    if (!answer) throw new Error("Joya returned an empty answer. Please try again.");
    if (warning) notify(warning, true);
  } catch (error) {
    answerBubble.textContent = answer
      ? `${answer}\n\nJoya’s response was interrupted: ${error.message}`
      : `I couldn't complete that request. ${error.message}`;
    notify(error.message, true);
  } finally {
    button.disabled = false;
    button.innerHTML = "Send <span>↑</span>";
    input.focus();
  }
}

async function loadLessons() {
  try {
    state.lessons = await api("/api/lessons");
    renderLessons(state.lessons);
  } catch (error) {
    $("#lesson-grid").textContent = error.message;
  }
}

function subjectFor(topic) {
  const text = topic.toLowerCase();
  if (/equation|fraction|percentage|geometry|probability|math/.test(text)) return "Mathematics";
  if (/atom|element|compound|chemical|acid|base|photosynthesis/.test(text)) return "Chemistry & Biology";
  if (/force|motion|energy|gravity|rocket|satellite|black hole|star|universe|galax|mars|solar|light-year|exoplanet|cosmic/.test(text)) return "Physics & Space";
  if (/continent|ocean|united nations|latitude|climate/.test(text)) return "Global knowledge";
  if (/python|computer|data|artificial intelligence|machine learning|neural|robot/.test(text)) return "Technology";
  return "Explore";
}

function renderLessons(lessons) {
  const grid = $("#lesson-grid");
  grid.replaceChildren();
  if (!lessons.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No concepts match that search. Try another keyword.";
    grid.append(empty);
    return;
  }
  for (const lesson of lessons) {
    const card = document.createElement("article");
    card.className = "lesson-card";
    const tag = document.createElement("span");
    tag.className = "lesson-subject";
    tag.textContent = subjectFor(lesson.topic);
    const title = document.createElement("h3");
    title.textContent = lesson.topic;
    const content = document.createElement("p");
    content.textContent = lesson.content;
    card.append(tag, title, content);
    grid.append(card);
  }
}

async function calculateExpression(expression) {
  try {
    const result = await api("/api/calculate", { method: "POST", body: JSON.stringify({ expression }) });
    return `Joya’s calculation:\n${result.expression} = ${result.answer}`;
  } catch (error) {
    return error.message;
  }
}

async function startTest(level) {
  clearInterval(state.timer);
  state.activeTest = null;
  $("#results-panel").classList.add("hidden");
  $("#jee-start-panel").classList.add("hidden");
  $("#test-panel").classList.remove("hidden");
  $("#question-list").textContent = "Preparing your questions…";
  $("#test-title").textContent = level === "mock" ? "Mixed mock test" : `JEE ${level === "main" ? "Main" : "Advanced"} practice`;
  $("#test-kind").textContent = level === "mock" ? "MIXED PRACTICE PAPER" : `JEE ${level.toUpperCase()} STYLE`;
  $("#test-timer").classList.toggle("hidden", level !== "mock");
  try {
    const test = await api(`/api/jee/questions?level=${encodeURIComponent(level)}`);
    state.activeTest = test;
    renderQuestions(test.questions);
    if (test.duration_seconds) startTimer(test.duration_seconds);
    $("#test-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    $("#test-panel").classList.add("hidden");
    $("#jee-start-panel").classList.remove("hidden");
    notify(error.message, true);
  }
}

function renderQuestions(questions) {
  const list = $("#question-list");
  list.replaceChildren();
  questions.forEach((question, index) => {
    const card = document.createElement("section");
    card.className = "question-card";
    const meta = document.createElement("div");
    meta.className = "question-meta";
    meta.textContent = `Question ${index + 1} · ${question.subject} · ${question.level}`;
    const title = document.createElement("h3");
    title.textContent = question.question;
    card.append(meta, title);
    question.options.forEach((option, optionIndex) => {
      const label = document.createElement("label");
      label.className = "option-row";
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = `question-${index}`;
      radio.value = "abcd"[optionIndex];
      const text = document.createElement("span");
      text.textContent = option;
      label.append(radio, text);
      card.append(label);
    });
    list.append(card);
  });
}

function startTimer(seconds) {
  const timer = $("#test-timer");
  let remaining = seconds;
  const update = () => {
    const minutes = Math.floor(remaining / 60).toString().padStart(2, "0");
    const secs = (remaining % 60).toString().padStart(2, "0");
    timer.textContent = `${minutes}:${secs}`;
    if (remaining <= 0) {
      clearInterval(state.timer);
      submitTest();
    }
    remaining -= 1;
  };
  update();
  state.timer = setInterval(update, 1000);
}

async function submitTest(event) {
  if (event) event.preventDefault();
  if (!state.activeTest) return;
  clearInterval(state.timer);
  const answers = state.activeTest.questions.map((_, index) => {
    return $(`input[name="question-${index}"]:checked`)?.value || "";
  });
  const submit = $(".submit-test");
  submit.disabled = true;
  try {
    const result = await api("/api/jee/grade", {
      method: "POST",
      body: JSON.stringify({ test_id: state.activeTest.test_id, answers }),
    });
    state.activeTest = null;
    renderResults(result);
    await loadOverview();
  } catch (error) {
    notify(error.message, true);
  } finally {
    submit.disabled = false;
  }
}

function renderResults(result) {
  $("#test-panel").classList.add("hidden");
  const panel = $("#results-panel");
  panel.replaceChildren();
  panel.classList.remove("hidden");
  const percent = result.maximum_score ? Math.max(0, Math.round(result.score / result.maximum_score * 100)) : 0;
  const summary = document.createElement("div");
  summary.className = "result-summary";
  const ring = document.createElement("div");
  ring.className = "score-ring";
  ring.textContent = `${percent}%`;
  const detail = document.createElement("div");
  const title = document.createElement("h2");
  title.textContent = "Your practice results";
  const stats = document.createElement("p");
  stats.textContent = `Score ${result.score}/${result.maximum_score} · ${result.correct} correct · ${result.incorrect} incorrect · ${result.skipped} skipped`;
  detail.append(title, stats);
  summary.append(ring, detail);
  panel.append(summary);
  result.results.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "result-item";
    const heading = document.createElement("strong");
    heading.textContent = `Question ${index + 1}: ${item.outcome} · Correct answer ${item.correct.toUpperCase()}`;
    const explanation = document.createElement("p");
    explanation.textContent = item.explanation;
    row.append(heading, explanation);
    panel.append(row);
  });
  const again = document.createElement("button");
  again.type = "button";
  again.className = "button button-primary";
  again.textContent = "Choose another practice test";
  again.addEventListener("click", () => {
    panel.classList.add("hidden");
    $("#jee-start-panel").classList.remove("hidden");
    $("#jee-start-panel").scrollIntoView({ behavior: "smooth" });
  });
  panel.append(again);
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadNotes() {
  try {
    const notes = await api("/api/notes");
    const list = $("#notes-list");
    list.replaceChildren();
    if (!notes.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No notes saved yet. Add your first learning note.";
      list.append(empty);
      return;
    }
    [...notes].reverse().forEach((note) => {
      const card = document.createElement("article");
      card.className = "note-card";
      const head = document.createElement("div");
      head.className = "note-card-head";
      const title = document.createElement("h3");
      title.textContent = note.title || "Untitled note";
      const remove = document.createElement("button");
      remove.className = "delete-note";
      remove.type = "button";
      remove.textContent = "Delete";
      remove.addEventListener("click", () => deleteNote(note.id));
      head.append(title, remove);
      const date = document.createElement("time");
      date.textContent = note.created_at ? new Date(note.created_at).toLocaleString() : "";
      const content = document.createElement("p");
      content.textContent = note.content || "";
      card.append(head, date, content);
      list.append(card);
    });
  } catch (error) {
    notify(error.message, true);
  }
}

async function saveNote(event) {
  event.preventDefault();
  const title = $("#note-title").value.trim();
  const content = $("#note-content").value.trim();
  try {
    await api("/api/notes", { method: "POST", body: JSON.stringify({ title, content }) });
    $("#note-form").reset();
    notify("Your note is saved.");
    await loadNotes();
    await loadOverview();
  } catch (error) {
    notify(error.message, true);
  }
}

async function deleteNote(id) {
  try {
    await api(`/api/notes/${id}`, { method: "DELETE" });
    notify("Note deleted.");
    await loadNotes();
    await loadOverview();
  } catch (error) {
    notify(error.message, true);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js").catch((error) => {
      console.error("Joya service worker registration failed:", error);
    });
  }

  const nameInput = $("#user-name");
  nameInput.value = "Learner";
  state.userName = nameInput.value;
  greet();
  nameInput.addEventListener("input", () => {
    state.userName = nameInput.value.trim() || "Learner";
    greet();
  });
  nameInput.addEventListener("change", async () => {
    try {
      const profile = await api("/api/me", {
        method: "PATCH",
        body: JSON.stringify({ name: nameInput.value.trim() }),
      });
      state.userName = profile.name;
      greet();
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#login-form").addEventListener("submit", (event) => submitAuthentication(event, "login"));
  $("#register-form").addEventListener("submit", (event) => submitAuthentication(event, "register"));
  $("#guest-button").addEventListener("click", async () => {
    const button = $("#guest-button");
    const message = $("#auth-message");
    button.disabled = true;
    message.textContent = "";
    try {
      const user = await api("/api/auth/guest", {
        method: "POST",
        body: JSON.stringify({}),
      });
      setCsrfToken(user.csrf_token);
      await setAuthenticated(user);
    } catch (error) {
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  $("#show-register").addEventListener("click", () => {
    $("#login-form").classList.add("hidden");
    $("#register-form").classList.remove("hidden");
    $("#auth-title").textContent = "Make Joya your own.";
    $("#auth-description").textContent = "Create an account to save your notes and keep your learning progress private.";
    $("#auth-message").textContent = "";
  });
  $("#show-login").addEventListener("click", () => {
    $("#register-form").classList.add("hidden");
    $("#login-form").classList.remove("hidden");
    $("#auth-title").textContent = "Welcome back.";
    $("#auth-description").textContent = "Sign in to keep your learning private and pick up where you left off.";
    $("#auth-message").textContent = "";
  });
  $("#logout-button").addEventListener("click", async () => {
    try {
      await api("/api/auth/logout", { method: "POST", body: JSON.stringify({}) });
      const user = await api("/api/me");
      setCsrfToken(user.csrf_token);
      await setAuthenticated(user);
    } catch (error) {
      notify(error.message, true);
    }
  });

  $$("[data-view]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  $("#mobile-menu").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
  $("#chat-form").addEventListener("submit", sendChat);
  $("#clear-chat").addEventListener("click", () => {
    $("#chat-messages").replaceChildren();
    appendMessage("assistant", "Conversation cleared. What would you like to learn next?");
  });
  $$(".prompt-suggestion").forEach((button) => button.addEventListener("click", () => {
    $("#chat-input").value = button.textContent.trim();
    $("#chat-input").focus();
  }));
  $("#lesson-search").addEventListener("input", (event) => {
    const query = event.target.value.trim().toLowerCase();
    renderLessons(state.lessons.filter((lesson) => `${lesson.topic} ${lesson.content} ${subjectFor(lesson.topic)}`.toLowerCase().includes(query)));
  });
  $$(".test-card").forEach((button) => button.addEventListener("click", () => startTest(button.dataset.level)));
  $("#jee-form").addEventListener("submit", submitTest);
  $("#cancel-test").addEventListener("click", () => {
    clearInterval(state.timer);
    state.activeTest = null;
    $("#test-panel").classList.add("hidden");
    $("#jee-start-panel").classList.remove("hidden");
  });
  $("#note-form").addEventListener("submit", saveNote);

  try {
    const user = await api("/api/me");
    setCsrfToken(user.csrf_token);
    await setAuthenticated(user);
  } catch (error) {
    $("#auth-message").textContent = error.message;
    $("#auth-screen").classList.remove("hidden");
  }
});
