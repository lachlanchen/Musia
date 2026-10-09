const $ = (id) => document.getElementById(id);
const icons = () => window.lucide?.createIcons();
const form = $("brief-form");
let capabilities,
  account = null,
  tab = "create",
  song = null,
  busy = false,
  accountEpoch = 0;
let songRequest = 0,
  libraryRequest = 0;
const DRAFT = "musia.creator.draft.v1",
  PENDING = "musia.creator.pending.v1";
function read(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}
function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {}
}
function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function button(text, icon, action, cls = "") {
  const b = element("button", undefined, cls);
  if (icon) {
    const i = element("i");
    i.dataset.lucide = icon;
    b.append(i);
  }
  b.append(element("span", text));
  b.addEventListener("click", () => guard(action));
  return b;
}
function notice(text) {
  $("notice").textContent = text;
  $("notice").hidden = !text;
}
const errors = {
  sign_in_required: "Sign in to continue.",
  reconnect_account: "Please reconnect your account.",
  sign_in_unavailable: "LazyingArt sign-in is not connected yet.",
  accept_creator_terms: "Please accept the creator terms first.",
  creator_invitation_required: "Redeem a creator invitation in your account.",
  monthly_generation_limit:
    "Your monthly render allowance is used. Listening and sharing stay free.",
  finish_current_job: "Finish or review your current render first.",
  generation_not_connected: "The generation worker is not connected yet.",
  agent_not_connected: "The song agent is not connected yet.",
  daily_limit_reached: "Today’s limit is reached. Please try again tomorrow.",
  invitation_invalid: "This invitation is invalid or has expired.",
  agent_response_unavailable:
    "The agent could not finish. Your draft is preserved.",
  job_already_started: "This render has already started.",
  song_not_found: "This song is private or unavailable.",
  same_origin_request_required: "Reload this page before trying again.",
};
async function api(path, data, method, key) {
  const options = {
    credentials: "same-origin",
    headers: {},
    signal: AbortSignal.timeout(105000),
  };
  if (data !== undefined) {
    options.method = method || "POST";
    options.headers = {
      "Content-Type": "application/json",
      "X-Musia-Request": "1",
    };
    options.body = JSON.stringify(data);
  }
  if (key) options.headers["Idempotency-Key"] = key;
  const response = await fetch("/creator" + path, options);
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(
      errors[result.detail] ||
        "The request could not finish. Please try again.",
    );
    error.status = response.status;
    throw error;
  }
  return result;
}
async function guard(action) {
  try {
    await action();
  } catch (e) {
    notice(e.message || "Connection unavailable. Your draft is preserved.");
  }
}
function brief() {
  const data = Object.fromEntries(new FormData(form));
  data.duration = Number(data.duration);
  data.bpm = Number(data.bpm);
  return data;
}
function fill(data) {
  for (const [k, v] of Object.entries(data || {})) {
    const field = form.elements.namedItem(k);
    if (!field) continue;
    if (
      field.tagName === "SELECT" &&
      !Array.from(field.options).some((o) => o.value === String(v))
    )
      field.add(new Option(String(v), String(v)));
    field.value = v;
  }
  save(DRAFT, brief());
}
function authRequired() {
  if (!account) {
    openAccount();
    return false;
  }
  if (!account.termsAccepted) {
    $("terms-dialog").showModal();
    return false;
  }
  return true;
}
function refreshControls() {
  const pending = read(PENDING);
  $("send").disabled = busy || !capabilities?.agent;
  $("generate").disabled = busy || !capabilities?.generation;
  $("generate").querySelector("span").textContent = pending
    ? "Recover pending render"
    : "Create song · 1 render";
  $("account-name").textContent = account?.name || "Sign in";
  $("usage").textContent = account
    ? `${account.usage.remaining} of ${account.usage.limit} renders left`
    : "Free listening";
  $("usage-period").textContent = account
    ? `${account.usage.period} · ${account.usage.tier}`
    : "Public songs are open to everyone.";
  $("connection").textContent = capabilities?.generation
    ? "Creator pilot"
    : "Creator preview · service not connected";
  $("generation-status").textContent = pending
    ? "Your previous request will be recovered without a second charge."
    : "Failed renders do not use your allowance.";
}
async function refreshAccount() {
  const data = await api("/api/me");
  if (account?.id !== data.account?.id) accountEpoch++;
  account = data.account;
  refreshControls();
}
async function login() {
  const result = await api("/auth/start", {});
  window.location.assign(result.url);
}
function openAccount() {
  const root = $("account-content");
  root.replaceChildren();
  if (!account) {
    root.append(
      element(
        "p",
        "Use your LazyingArt account. Your existing music stays available without signing in.",
      ),
    );
    const b = button("Continue with LazyingArt", "log-in", login, "primary");
    b.disabled = !capabilities?.login;
    root.append(b);
    const providers = Object.entries(capabilities?.providers || {})
      .filter(([, on]) => on)
      .map(
        ([name]) =>
          ({
            password: "LazyingArt",
            apple: "Apple",
            google: "Google",
            github: "GitHub",
          })[name],
      );
    root.append(
      element(
        "p",
        providers.length
          ? providers.join(" · ")
          : "Sign-in has not been connected for this preview.",
        "muted",
      ),
    );
  } else {
    root.append(
      element("h3", account.name),
      element(
        "p",
        `${account.usage.tier} · ${account.usage.remaining} renders remaining`,
      ),
    );
    if (!account.termsAccepted)
      root.append(
        button("Review creator terms", "file-check", () => {
          $("account-dialog").close();
          $("terms-dialog").showModal();
        }),
      );
    if (!account.invited && capabilities.invitationRequired) {
      const f = element("form");
      const label = element("label", "Creator invitation");
      const input = element("input");
      input.required = true;
      input.autocomplete = "off";
      input.maxLength = 128;
      label.append(input);
      const submit = element("button", "Redeem", "primary");
      submit.type = "submit";
      f.append(label, submit);
      f.onsubmit = (e) => {
        e.preventDefault();
        guard(async () => {
          await api("/api/invitations/redeem", { code: input.value });
          await refreshAccount();
          $("account-dialog").close();
          notice("Invitation accepted.");
        });
      };
      root.append(f);
    }
    const actions = element("div", undefined, "account-actions");
    actions.append(
      button("Sign out", "log-out", async () => {
        await api("/auth/logout", {});
        accountEpoch++;
        account = null;
        song = null;
        $("messages").replaceChildren();
        $("jobs").replaceChildren();
        $("songs").replaceChildren();
        $("song-detail").replaceChildren();
        $("account-dialog").close();
        refreshControls();
        showTab("create");
      }),
    );
    actions.append(
      button("Blocked accounts", "user-round-x", async () => {
        const data = await api("/api/blocks");
        const list = element("div");
        if (!data.accounts.length)
          list.append(element("p", "No blocked accounts.", "muted"));
        for (const person of data.accounts)
          list.append(
            button("Unblock " + person.name, "user-round-check", async () => {
              await api(`/api/accounts/${person.id}/block`, { active: false });
              list.remove();
              notice("Account unblocked.");
            }),
          );
        root.append(list);
        icons();
      }),
    );
    actions.append(
      button(
        "Delete creator account",
        "trash-2",
        async () => {
          if (
            !confirm(
              "Delete your Musia creator account and hide its music? This cannot be undone.",
            )
          )
            return;
          await api("/api/me", {}, "DELETE");
          accountEpoch++;
          account = null;
          $("account-dialog").close();
          location.reload();
        },
        "danger",
      ),
    );
    root.append(actions);
  }
  $("account-dialog").showModal();
  icons();
}
function addMessage(text, person) {
  const row = element(
    "div",
    undefined,
    person === "You" ? "user-message" : "agent-message",
  );
  row.append(element("span", person, "speaker"), element("p", text));
  $("messages").append(row);
  row.scrollIntoView({ block: "nearest", behavior: "smooth" });
}
$("chat-form").onsubmit = (e) => {
  e.preventDefault();
  guard(async () => {
    if (!authRequired()) return;
    const epoch = accountEpoch;
    busy = true;
    refreshControls();
    const message = $("message").value;
    addMessage(message, "You");
    try {
      const data = await api("/api/agent", { message, brief: brief() });
      if (epoch !== accountEpoch) return;
      fill(data.brief);
      addMessage(data.message, "Musia");
      $("message").value = "";
      notice("");
    } finally {
      busy = false;
      refreshControls();
    }
  });
};
form.addEventListener("input", () => save(DRAFT, brief()));
form.onsubmit = (e) => {
  e.preventDefault();
  guard(async () => {
    if (!authRequired()) return;
    let pending = read(PENDING);
    if (pending && pending.owner !== account.id) {
      notice(
        "A pending render belongs to another account. Sign back into that account to recover it.",
      );
      return;
    }
    if (!pending) {
      pending = {
        owner: account.id,
        key: crypto.randomUUID(),
        body: {
          brief: brief(),
          rights_confirmed: $("rights").checked,
          visibility: $("visibility").value,
        },
      };
      save(PENDING, pending);
    }
    busy = true;
    refreshControls();
    try {
      await api("/api/jobs", pending.body, "POST", pending.key);
      localStorage.removeItem(PENDING);
      notice("Render queued for safety review.");
      await refreshJobs();
      await refreshAccount();
    } catch (error) {
      if (error.status && error.status < 500) localStorage.removeItem(PENDING);
      throw error;
    } finally {
      busy = false;
      refreshControls();
    }
  });
};
async function refreshJobs() {
  if (!account) return;
  const data = await api("/api/jobs");
  const root = $("jobs");
  root.replaceChildren();
  if (!data.jobs.length) root.append(element("p", "No renders yet.", "muted"));
  for (const job of data.jobs) {
    const row = element("div", undefined, "job-row"),
      info = element("div");
    info.append(
      element("strong", job.brief.title || "Song"),
      element(
        "p",
        {
          queued: "Queued · input safety review",
          running: "Creating your song",
          review: "Audio & lyrics review",
          ready: "Ready to listen",
          failed: "Could not finish · allowance returned",
          cancelled: "Cancelled · allowance returned",
          interrupted: "Waiting for recovery",
        }[job.state] || job.state,
      ),
    );
    row.append(info);
    if (job.state === "queued")
      row.append(
        button("Cancel", "x", async () => {
          await api(`/api/jobs/${job.id}/cancel`, {});
          await refreshJobs();
          await refreshAccount();
        }),
      );
    if (job.state === "ready")
      row.append(
        button("Listen", "play", async () => {
          await showTab("mine");
          await openSong(job.id);
        }),
      );
    root.append(row);
  }
  icons();
}
function closeSong() {
  songRequest++;
  song = null;
  const root = $("song-detail");
  root.querySelector("audio")?.pause();
  root.replaceChildren();
  delete root.dataset.song;
  root.hidden = true;
}

async function showTab(next) {
  tab = next;
  libraryRequest++;
  closeSong();
  document.querySelectorAll("[data-tab]").forEach((b) => {
    if (b.dataset.tab === next) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  $("create-view").hidden = next !== "create";
  $("library-view").hidden = next === "create";
  if (next !== "create") await loadSongs();
}

async function loadSongs() {
  const request = ++libraryRequest,
    epoch = accountEpoch,
    mode = tab;
  const root = $("songs");
  root.replaceChildren();
  closeSong();
  $("library-title").textContent = {
    public: "Discover",
    mine: "My music",
    saved: "Saved",
  }[mode];
  if (mode !== "public" && !account) {
    root.append(
      element("p", "Sign in to open your music.", "muted"),
      button("Sign in", "log-in", openAccount),
    );
    icons();
    return;
  }
  const data = await api("/api/songs?mode=" + mode);
  if (request !== libraryRequest || epoch !== accountEpoch) return;
  if (!data.songs.length)
    root.append(
      element(
        "p",
        mode === "public"
          ? "No community songs have been published yet."
          : "No songs here yet.",
        "muted",
      ),
    );
  for (const item of data.songs) {
    const row = element("article", undefined, "song-row");
    const img = element("img", undefined, "song-art");
    img.src = "/assets/brand.png";
    img.alt = "";
    const info = element("div");
    info.append(
      element("h3", item.title),
      element(
        "p",
        `${item.author.name} · ${item.language.toUpperCase()}${item.mine ? " · " + item.visibility + " / " + item.moderation : ""}`,
      ),
    );
    row.append(
      img,
      info,
      button("Play", "play", () => openSong(item.id)),
    );
    root.append(row);
  }
  icons();
}

async function openSong(id) {
  const request = ++songRequest,
    epoch = accountEpoch;
  const current = await api("/api/songs/" + id);
  const comments = await api(`/api/songs/${id}/comments`);
  if (request !== songRequest || epoch !== accountEpoch) return;
  song = current;
  const root = $("song-detail");
  const sameSong = root.dataset.song === id && !!root.querySelector("audio");
  // Preserve the actual audio node and playhead during social updates.
  if (!sameSong) {
    root.querySelector("audio")?.pause();
    root.replaceChildren();
    root.dataset.song = id;
    const audio = element("audio");
    audio.controls = true;
    audio.src = current.audioUrl;
    audio.preload = "metadata";
    root.append(
      element("div", undefined, "detail-head"),
      element("p", undefined, "song-author muted"),
      audio,
      element("div", undefined, "song-actions"),
      element("p", undefined, "song-lyrics"),
      element("section"),
    );
  }
  root.hidden = false;
  root
    .querySelector(".detail-head")
    .replaceChildren(
      element("h2", current.title),
      button("Close", "x", closeSong),
    );
  root.querySelector(".song-author").textContent = `by ${current.author.name}`;
  root.querySelector(".song-lyrics").textContent = current.lyrics;
  const actions = root.querySelector(".song-actions");
  actions.replaceChildren();
  const refresh = () =>
    root.dataset.song === id && epoch === accountEpoch
      ? openSong(id)
      : undefined;
  for (const [kind, icon, text, value] of [
    ["like", "heart", String(current.likes), current.liked],
    ["save", "bookmark", "Save", current.saved],
  ]) {
    const b = button(text, icon, async () => {
      if (!authRequired()) return;
      b.disabled = true;
      try {
        await api(`/api/songs/${id}/reactions/${kind}`, { active: !value });
        await refresh();
      } finally {
        b.disabled = false;
      }
    });
    b.setAttribute("aria-pressed", String(value));
    b.setAttribute(
      "aria-label",
      kind === "like" ? `Like song · ${current.likes}` : "Save song",
    );
    actions.append(b);
  }
  if (current.sharePath)
    actions.append(
      button("Share", "share-2", async () => {
        const url = location.origin + current.sharePath;
        if (navigator.share)
          await navigator.share({ title: current.title, url });
        else {
          await navigator.clipboard.writeText(url);
          notice("Song link copied.");
        }
      }),
    );
  if (current.mine)
    actions.append(
      button(
        current.visibility === "private" ? "Share publicly" : "Make private",
        "globe",
        async () => {
          await api(`/api/songs/${id}/visibility`, {
            visibility: current.visibility === "private" ? "public" : "private",
          });
          await refresh();
        },
      ),
    );
  if (account && !current.mine)
    actions.append(
      button("Report", "flag", async () => {
        const reason = prompt("What should our moderators review?");
        if (reason && reason.trim().length >= 3) {
          await api(`/api/songs/${id}/reports`, { reason });
          notice("Report sent. Thank you.");
        }
      }),
      button("Block author", "user-round-x", async () => {
        await api(`/api/accounts/${current.author.id}/block`, { active: true });
        if (epoch === accountEpoch) await loadSongs();
      }),
    );
  const section = root.querySelector("section");
  section.replaceChildren(element("h3", "Comments"));
  for (const c of comments.comments) {
    const row = element("div", undefined, "comment-row");
    row.append(element("strong", c.author), element("p", c.text));
    if (c.state === "pending") row.append(element("small", "Awaiting review"));
    if (c.mine)
      row.append(
        button("Delete", "trash-2", async () => {
          await api("/api/comments/" + c.id, {}, "DELETE");
          await refresh();
        }),
      );
    section.append(row);
  }
  if (current.sharePath) {
    const f = element("form"),
      input = element("textarea");
    input.rows = 2;
    input.maxLength = 1000;
    input.required = true;
    input.setAttribute("aria-label", "Your comment");
    input.placeholder = "Leave a kind word…";
    const submit = element("button", "Send for review");
    submit.type = "submit";
    f.append(input, submit);
    f.onsubmit = (e) => {
      e.preventDefault();
      guard(async () => {
        if (!authRequired()) return;
        submit.disabled = true;
        try {
          await api(`/api/songs/${id}/comments`, { text: input.value });
          await refresh();
        } finally {
          submit.disabled = false;
        }
      });
    };
    section.append(f);
  }
  icons();
  if (!sameSong) root.scrollIntoView({ block: "start", behavior: "smooth" });
}
document
  .querySelectorAll("[data-tab]")
  .forEach((b) => (b.onclick = () => guard(() => showTab(b.dataset.tab))));
document
  .querySelectorAll("[data-close]")
  .forEach((b) => (b.onclick = () => $(b.dataset.close).close()));
$("plans-button").onclick = () => {
  $("plans-dialog").showModal();
};
$("account-button").onclick = openAccount;
$("accept-terms").onclick = () =>
  guard(async () => {
    await api("/api/terms", {});
    await refreshAccount();
    $("terms-dialog").close();
    notice("Creator terms accepted.");
  });
$("refresh-jobs").onclick = () => guard(refreshJobs);
$("refresh-library").onclick = () => guard(loadSongs);
$("export").onclick = () => {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(brief(), null, 2)], { type: "application/json" }),
  );
  const a = element("a");
  a.href = url;
  a.download = "musia-song-brief.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
async function start() {
  fill(read(DRAFT));
  capabilities = await api("/api/capabilities");
  for (const plan of capabilities.plans) {
    const row = element("div", undefined, "plan-row");
    row.append(
      element("strong", plan.name),
      element(
        "span",
        plan.target_usd === "0" ? "Free" : `US$${plan.target_usd} / month`,
        "price",
      ),
      element(
        "small",
        `${plan.renders} renders/month · Private or public · ${plan.agent_turns_per_day} agent turns/day`,
      ),
    );
    $("plans").append(row);
  }
  await refreshAccount();
  await refreshJobs();
  const shared = new URL(location.href).searchParams.get("song");
  if (shared && /^[a-f0-9]{32}$/.test(shared)) {
    await showTab("public");
    await openSong(shared);
  }
  icons();
}
guard(start);
