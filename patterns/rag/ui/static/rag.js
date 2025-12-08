// Load knowledge on startup
/** biome-ignore-all lint/correctness/noUnusedVariables: biome-ignore */
document.addEventListener("DOMContentLoaded", () => {
	RagApp.init();
});

const RagApp = {
	state: {
		documents: [],
		messages: [],
		sessionId: null,
	},

	init() {
		this.state.sessionId = crypto.randomUUID();
		this.loadKnowledge();
		this.setupListeners();
	},

	setupListeners() {
		const form = document.getElementById("query-form");
		if (form) {
			form.addEventListener("submit", (e) => this.handleQuery(e));
		}

		const ingestBtn = document.getElementById("ingest-btn");
		if (ingestBtn) {
			ingestBtn.addEventListener("click", () => this.ingestKnowledge());
		}

		// Reset handled inline in HTML onclick, but could be moved here if we remove onclick attributes
		// For now, exposing global functions for compatibility with existing inline calls
		window.ingestKnowledge = () => this.ingestKnowledge();
		window.resetKnowledge = () => this.resetKnowledge();
		window.handleQuery = (e) => this.handleQuery(e);
	},

	async loadKnowledge() {
		const list = document.getElementById("knowledge-list");
		try {
			const response = await fetch("/rag/knowledge");
			const data = await response.json();

			this.state.documents = data.documents || [];
			this.renderKnowledge();
		} catch (error) {
			console.error("Failed to load knowledge:", error);
			list.innerHTML = `<div class="error-message">Failed to load knowledge base.</div>`;
		}
	},

	renderKnowledge() {
		const list = document.getElementById("knowledge-list");
		if (this.state.documents.length > 0) {
			// Check if DOMPurify is loaded (it is loaded in rag.html.j2)
			const sanitize = (content) => {
				if (typeof DOMPurify !== "undefined") {
					return DOMPurify.sanitize(content);
				}
				// Fallback if library fails to load
				const p = document.createElement("p");
				p.textContent = content;
				return p.innerHTML;
			};

			list.innerHTML = this.state.documents
				.map(
					(doc) => `
                <div class="knowledge-item">
                    <div class="doc-icon">📄</div>
                    <!-- Use sanitize instead of this.escapeHtml -->
                    <div class="doc-content">${sanitize(doc)}</div>
                </div>
            `,
				)
				.join("");
		} else {
			list.innerHTML = `
                <div class="empty-state">
                    <span class="icon">📭</span>
                    <p>Knowledge base is empty</p>
                </div>
            `;
		}
	},

	async ingestKnowledge() {
		const btn = document.getElementById("ingest-btn");
		btn.disabled = true;

		// Save original content
		const originalContent = btn.innerHTML;
		btn.innerHTML = '<span class="spinner"></span> Ingesting...';

		try {
			await fetch("/rag/ingest", { method: "POST" });

			// Poll for updates (simple version)
			let retries = 0;
			const interval = setInterval(async () => {
				await this.loadKnowledge();
				const list = document.getElementById("knowledge-list");

				// If we have documents, we are done
				if (this.state.documents.length > 0 || retries > 10) {
					clearInterval(interval);
					btn.disabled = false;
					btn.innerHTML = originalContent;
				}
				retries++;
			}, 1000);
		} catch (error) {
			console.error("Ingestion failed:", error);
			btn.disabled = false;
			btn.innerHTML = originalContent;
		}
	},

	async resetKnowledge() {
		if (!confirm("Are you sure you want to clear the knowledge base?")) return;

		try {
			await fetch("/rag/reset", { method: "POST" });
			await this.loadKnowledge();
		} catch (error) {
			console.error("Reset failed:", error);
		}
	},

	async handleQuery(event) {
		event.preventDefault();
		const input = document.getElementById("query-input");
		const history = document.getElementById("chat-history");
		const query = input.value.trim();

		if (!query) return;

		// Add user message
		this.appendMessage("user", query);
		input.value = "";

		// Show loading
		const loadingId = this.appendLoading();

		try {
			const queryResponse = await fetch("/rag/query", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					query,
					session_id: this.state.sessionId,
				}),
			});
			const data = await queryResponse.json();

			this.removeMessage(loadingId);
			this.appendMessage("agent", data.final);
		} catch (error) {
			console.error("Query failed:", error);
			this.removeMessage(loadingId);
			this.appendMessage("agent error", "Sorry, something went wrong.");
		}
	},

	appendMessage(role, content) {
		const history = document.getElementById("chat-history");
		const msgDiv = document.createElement("div");
		msgDiv.className = `message ${role}`;

		if (role.includes("user")) {
			const contentDiv = document.createElement("div");
			contentDiv.className = "content";
			contentDiv.textContent = content; // Text only for user
			msgDiv.appendChild(contentDiv);
		} else {
			const contentDiv = document.createElement("div");
			contentDiv.className = "content markdown-body";

			// XSS Prevention + Markdown
			if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
				const dirtyHtml = marked.parse(content);
				contentDiv.innerHTML = DOMPurify.sanitize(dirtyHtml);
			} else {
				// Fallback to plain text if marked or DOMPurify is missing for security.
				contentDiv.textContent = content;
			}
			msgDiv.appendChild(contentDiv);
		}

		history.appendChild(msgDiv);
		history.scrollTop = history.scrollHeight;
	},

	appendLoading() {
		const history = document.getElementById("chat-history");
		const id = `loading-${Date.now()}`;
		const msgDiv = document.createElement("div");
		msgDiv.className = "message agent loading";
		msgDiv.id = id;
		msgDiv.innerHTML =
			'<div class="typing-indicator"><span></span><span></span><span></span></div>';
		history.appendChild(msgDiv);
		history.scrollTop = history.scrollHeight;
		return id;
	},

	removeMessage(id) {
		const el = document.getElementById(id);
		if (el) el.remove();
	},
};
