/* ================================================================
   Online Market — AI Shopping Assistant (Gemini powered)
   Include with: <script src="chatbot.js"></script>
   Works on any page — injects its own floating chat widget.
   ================================================================ */
(function () {
  const GEMINI_MODEL = "gemini-3.5-flash";
  const GEMINI_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;
  const PRODUCTS_API = "https://fakestoreapi.com/products";

  // NOTE: hardcoding a key here means it's visible to anyone who views your page source.
  // Fine for local/personal use — for a public deployment, proxy this call through a backend instead.
  const apiKey = "GEMINI_API_KEY";
  let productContext = "";
  let productsLoaded = false;
  let chatHistory = []; // [{ role: 'user' | 'model', text }]

  // ---------------- Styles ----------------
  const style = document.createElement("style");
  style.textContent = `
    #aiChatToggle {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: #febd69;
      border: none;
      font-size: 24px;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(0,0,0,0.25);
      z-index: 9998;
    }
    #aiChatToggle:hover { filter: brightness(1.05); background: #007185; }
    #aiChatWindow {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 340px;
      max-width: calc(100vw - 32px);
      height: 460px;
      max-height: calc(100vh - 140px);
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.3);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 9999;
      font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;
    }
    #aiChatWindow.open { display: flex; }
    #aiChatHeader {
      background: #131921;
      color: white;
      padding: 12px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    #aiChatHeader span { font-weight: bold; font-size: 15px; }
    #aiChatHeader button {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 15px;
      margin-left: 8px;
    }
    #aiChatMessages {
      flex: 1;
      padding: 12px;
      overflow-y: auto;
      background: #F5F6F7;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .aiMsg {
      max-width: 82%;
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.4;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .aiMsg.user {
      align-self: flex-end;
      background: #FFD814;
      color: #111;
      border-bottom-right-radius: 2px;
    }
    .aiMsg.bot {
      align-self: flex-start;
      background: white;
      border: 1px solid #ddd;
      color: #111;
      border-bottom-left-radius: 2px;
    }
    .aiMsg.system {
      align-self: center;
      background: transparent;
      color: #666;
      font-size: 12px;
      text-align: center;
      max-width: 100%;
    }
    #aiChatInputRow {
      display: flex;
      border-top: 1px solid #ddd;
      padding: 8px;
      gap: 6px;
      flex-shrink: 0;
    }
    #aiChatInput {
      flex: 1;
      border: 1px solid #ccc;
      border-radius: 16px;
      padding: 8px 12px;
      font-size: 13px;
      outline: none;
    }
    #aiChatSend {
      background: #007185;
      color: white;
      border: none;
      border-radius: 16px;
      padding: 0 16px;
      cursor: pointer;
      font-size: 13px;
    }
    #aiChatSend:disabled { opacity: 0.5; cursor: default; }
  `;
  document.head.appendChild(style);

  // ---------------- DOM ----------------
  const toggleBtn = document.createElement("button");
  toggleBtn.id = "aiChatToggle";
  toggleBtn.title = "Chat with our shopping assistant";
  toggleBtn.textContent = "💬";
  document.body.appendChild(toggleBtn);

  const chatWindow = document.createElement("div");
  chatWindow.id = "aiChatWindow";
  chatWindow.innerHTML = `
    <div id="aiChatHeader">
      <span>🛍️ Shop Assistant</span>
      <div>
        <button id="aiChatCloseBtn" title="Close">✕</button>
      </div>
    </div>
    <div id="aiChatMessages"></div>
    <div id="aiChatInputRow">
      <input id="aiChatInput" type="text" placeholder="Ask about products..." />
      <button id="aiChatSend">Send</button>
    </div>
  `;
  document.body.appendChild(chatWindow);

  const messagesEl = chatWindow.querySelector("#aiChatMessages");
  const inputEl = chatWindow.querySelector("#aiChatInput");
  const sendBtn = chatWindow.querySelector("#aiChatSend");
  const closeBtn = chatWindow.querySelector("#aiChatCloseBtn");

  toggleBtn.addEventListener("click", () => {
    chatWindow.classList.toggle("open");
    if (chatWindow.classList.contains("open")) {
      if (messagesEl.children.length === 0) {
        addMessage("bot", "Hello! I am AskMart, your virtual assistant for product search and shopping-related inquiries on Online Market. How can I help you today?");
      }
      inputEl.focus();
      ensureProductsLoaded();
    }
  });
  closeBtn.addEventListener("click", () => chatWindow.classList.remove("open"));

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // Renders a small safe subset of Markdown (bold, italic, line breaks) that Gemini tends to use.
  function formatMessage(text) {
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "aiMsg " + role;
    if (role === "bot") {
      div.innerHTML = formatMessage(text);
    } else {
      div.textContent = text;
    }
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function setMessageText(el, text) {
    el.innerHTML = formatMessage(text);
  }

  // ---------------- Product context ----------------
  async function ensureProductsLoaded() {
    if (productsLoaded) return;
    try {
      const cached = sessionStorage.getItem("ai_product_context");
      if (cached) {
        productContext = cached;
        productsLoaded = true;
        return;
      }
      const res = await fetch(PRODUCTS_API);
      const products = await res.json();
      productContext = products
        .map(p =>
          `#${p.id} | ${p.title} | $${p.price} | ${p.category} | rating ${p.rating.rate}/5 (${p.rating.count} reviews) | ${p.description.slice(0, 140)}`
        )
        .join("\n");
      sessionStorage.setItem("ai_product_context", productContext);
      productsLoaded = true;
    } catch (e) {
      console.error("Failed to load product catalog for chatbot:", e);
    }
  }

  function buildSystemInstruction() {
    return `You are the friendly shopping assistant for "Online Market", an online store.
Only answer using the product catalog below — never invent products, prices, or details that aren't listed.
If someone asks about something not in the catalog, tell them we don't currently carry it.
Keep answers short and conversational. When recommending a product, mention its name and price.
You can suggest the user click "View" on a product or "Add to Cart", but you cannot add items to the cart yourself.

Product catalog:
${productContext || "(catalog still loading — ask the user to try again in a moment)"}`;
  }

  // ---------------- Sending messages ----------------
  async function callGemini(contents, attempt = 1) {
    const res = await fetch(`${GEMINI_ENDPOINT}?key=${encodeURIComponent(apiKey)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: buildSystemInstruction() }] },
        contents: contents
      })
    });

    const data = await res.json();

    // Gemini is overloaded (503) — retry a few times with backoff before giving up.
    if (!res.ok && res.status === 503 && attempt < 3) {
      await new Promise(r => setTimeout(r, attempt * 1200));
      return callGemini(contents, attempt + 1);
    }

    return { res, data };
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    addMessage("user", text);
    chatHistory.push({ role: "user", text });
    inputEl.value = "";
    sendBtn.disabled = true;
    const thinkingEl = addMessage("bot", "Typing...");

    await ensureProductsLoaded();

    try {
      const contents = chatHistory.map(m => ({
        role: m.role === "user" ? "user" : "model",
        parts: [{ text: m.text }]
      }));

      const { res, data } = await callGemini(contents);

      if (!res.ok) {
        const msg = (data && data.error && data.error.message) || "Something went wrong talking to Gemini.";
        setMessageText(thinkingEl, res.status === 503
          ? "⚠️ Gemini is under heavy load right now. Please try sending your message again in a moment."
          : "⚠️ " + msg);
        return;
      }

      const parts = data && data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts;
      const reply = parts ? parts.map(p => p.text).join("") : "Sorry, I couldn't come up with a response.";
      setMessageText(thinkingEl, reply);
      chatHistory.push({ role: "model", text: reply });
    } catch (e) {
      setMessageText(thinkingEl, "⚠️ Network error — please try again.");
      console.error(e);
    } finally {
      sendBtn.disabled = false;
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();