/**
 * Agent Design Patterns - Main Application Logic
 * Uses the Module Pattern to encapsulate logic and state.
 */

const App = {
	state: {
		patterns: [],
		currentPatternId: null,
		currentView: "info", // 'info', 'code', 'demo'
	},

	elements: {
		sidebarList: document.getElementById("pattern-list"),
		pageTitle: document.getElementById("page-title"),
		welcomeScreen: document.getElementById("welcome-screen"),
		demoFrame: document.getElementById("demo-frame"),
		viewToggle: document.getElementById("view-toggle"),
		markdownContainer: document.getElementById("markdown-container"),
		codeDisplay: document.getElementById("code-display"),
		codeViewer: document.getElementById("code-viewer"),
		infoViewer: document.getElementById("info-viewer"),
		toggleBtns: document.querySelectorAll(".toggle-btn"),
		copyBtn: document.querySelector(".copy-btn"),
	},

	init() {
		this.setupMermaid();
		this.fetchPatterns();
		this.setupEventListeners();
	},

	setupMermaid() {
		if (typeof mermaid !== "undefined") {
			mermaid.initialize({
				startOnLoad: false,
				theme: "dark",
				securityLevel: "loose",
				fontFamily: "Fira Code, monospace",
			});
		}
	},

	setupEventListeners() {
		// 1. Sidebar delegation (instead of inline onclicks)
		this.elements.sidebarList.addEventListener("click", (e) => {
			const link = e.target.closest(".pattern-link");
			if (!link) return;
			e.preventDefault();
			const { id, url, name } = link.dataset;
			this.loadPattern(id, url, name);
		});

		// 2. View Toggle delegation
		this.elements.viewToggle.addEventListener("click", (e) => {
			const btn = e.target.closest(".toggle-btn");
			if (!btn) return;
			const view = btn.dataset.view; // We will need to add data-view attributes
			this.switchView(view);
		});

		// 3. Copy Button
		if (this.elements.copyBtn) {
			this.elements.copyBtn.addEventListener("click", () => this.copyCode());
		}
	},

	setupFormHandling() {
		// 4. Form Loading State
		document.addEventListener("submit", (e) => {
			if (e.target.matches(".run-form")) {
				const btn = e.target.querySelector('button[type="submit"]');
				if (btn) {
					btn.classList.add("loading");
					btn.textContent = "Running...";
				}
			}
		});
	},

	async fetchPatterns() {
		try {
			const res = await fetch("patterns.json");
			this.state.patterns = await res.json();
			this.renderSidebar();
		} catch (e) {
			console.error("Failed to load patterns:", e);
			this.elements.sidebarList.innerHTML = `<div class="error-message">Failed to load patterns.</div>`;
		}
	},

	escapeHtml(str) {
		if (!str) return "";
		return str
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;");
	},

	renderSidebar() {
		this.elements.sidebarList.innerHTML = this.state.patterns
			.map(
				(p) => `
                <a href="#" class="pattern-link" 
                   data-id="${this.escapeHtml(p.id)}" 
                   data-url="${this.escapeHtml(p.demo_url || "")}" 
                   data-name="${this.escapeHtml(p.name)}">
                    <div class="pattern-icon">${p.icon || "⚡"}</div>
                    <div class="pattern-info">
                        <div class="pattern-name">${this.escapeHtml(p.name)}</div>
                        <div class="pattern-desc">${this.escapeHtml(p.description)}</div>
                    </div>
                </a>
            `,
			)
			.join("");
	},

	loadPattern(id, url, name) {
		this.state.currentPatternId = id;

		// UI Updates
		this.elements.pageTitle.textContent = name;
		this.elements.viewToggle.classList.remove("hidden");
		this.elements.welcomeScreen.classList.add("hidden");

		// Sidebar Active State
		document.querySelectorAll(".pattern-link").forEach((link) => {
			link.classList.toggle("active", link.dataset.id === id);
		});

		// Manage Demo Button Visibility
		const demoBtn = document.querySelector('.toggle-btn[data-view="demo"]');
		if (demoBtn) {
			if (!url) {
				demoBtn.classList.add("hidden");
				if (demoBtn.classList.contains("active")) this.switchView("info");
			} else {
				demoBtn.classList.remove("hidden");
				this.elements.demoFrame.src = url;
			}
		}

		// Fetch Content
		this.loadCodeFiles(id);
		this.loadReadme(id);

		// Reset View
		this.switchView("info");
	},

	switchView(viewName) {
		this.state.currentView = viewName;

		// Update Buttons
		this.elements.toggleBtns.forEach((btn) => {
			btn.classList.toggle("active", btn.dataset.view === viewName);
		});

		// Update Visibility
		this.elements.demoFrame.classList.toggle("hidden", viewName !== "demo");
		this.elements.codeViewer.classList.toggle("hidden", viewName !== "code");
		this.elements.infoViewer.classList.toggle("hidden", viewName !== "info");
	},

	async loadReadme(patternId) {
		const container = this.elements.markdownContainer;

		try {
			const res = await fetch(`api/patterns/${patternId}/README.md`);
			if (!res.ok) throw new Error(res.status);

			const text = await res.text();
			container.innerHTML = `<div class="markdown-container">${marked.parse(text)}</div>`;

			this.processMermaidBlocks(container);
			this.highlightCodeBlocks(container);
		} catch {
			console.error("Failed to load README:");
			container.innerHTML =
				'<p class="text-muted">No information available.</p>';
		}
	},

	processMermaidBlocks(container) {
		// Marked renders ```mermaid as <pre><code class="language-mermaid">
		const mermaidBlocks = container.querySelectorAll("code.language-mermaid");

		mermaidBlocks.forEach((block) => {
			const code = block.textContent;
			const pre = block.parentElement;

			const div = document.createElement("div");
			div.className = "mermaid";
			div.textContent = code;

			pre.replaceWith(div);
		});

		if (mermaidBlocks.length > 0) {
			mermaid.run({ querySelector: ".mermaid" });
		}
	},

	highlightCodeBlocks(container) {
		if (window.hljs) {
			container.querySelectorAll("pre code").forEach((block) => {
				// Skip mermaid blocks as they are handled separately
				if (!block.classList.contains("language-mermaid")) {
					hljs.highlightElement(block);
				}
			});
		}
	},

	async loadCodeFiles(patternId) {
		const fileList = document.getElementById("code-file-list");
		const display = this.elements.codeDisplay;

		fileList.innerHTML = '<div class="loading-message">Loading...</div>';
		display.textContent = "";

		try {
			const res = await fetch(`api/code/${patternId}`);
			if (!res.ok) throw new Error(res.statusText);

			const files = await res.json();
			this.renderCodeFileList(files);

			// Select first file by default
			const firstFile = Object.keys(files)[0];
			if (firstFile) {
				this.showFileContent(firstFile, files[firstFile]);
				// Mark first item active
				const firstBtn = fileList.querySelector(".file-item");
				if (firstBtn) firstBtn.classList.add("active");
			}
		} catch (e) {
			console.error("Failed to load files:", e);
			fileList.innerHTML = `<div class="error-message">Error loading files</div>`;
			display.textContent = "Failed to load code files.";
		}
	},

	renderCodeFileList(files) {
		const fileList = document.getElementById("code-file-list");
		fileList.innerHTML = "";

		Object.entries(files).forEach(([filename, content]) => {
			const div = document.createElement("div");
			div.className = "file-item";
			div.textContent = filename;
			div.onclick = () => {
				document.querySelectorAll(".file-item").forEach((b) => {
					b.classList.remove("active");
				});
				div.classList.add("active");
				this.showFileContent(filename, content);
			};
			fileList.appendChild(div);
		});
	},

	showFileContent(filename, content) {
		const display = this.elements.codeDisplay;
		display.textContent = content;

		// Determine language
		let lang = "plaintext";
		if (filename.endsWith(".py")) lang = "python";
		else if (filename.endsWith(".js")) lang = "javascript";
		else if (filename.endsWith(".html")) lang = "xml";
		else if (filename.endsWith(".css")) lang = "css";
		else if (filename.endsWith(".md")) lang = "markdown";

		display.className = `language-${lang}`;

		if (window.hljs) {
			delete display.dataset.highlighted;
			hljs.highlightElement(display);
		}
	},

	async copyCode() {
		const btn = document.getElementById("copy-btn");
		const text = this.elements.codeDisplay.textContent;
		const originalIcon = btn.innerHTML;

		try {
			await navigator.clipboard.writeText(text);
			btn.classList.add("copied");
			btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

			setTimeout(() => {
				btn.classList.remove("copied");
				btn.innerHTML = originalIcon;
			}, 2000);
		} catch (err) {
			console.error("Copy failed", err);
		}
	},
};

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
	// Check if we are on the main page
	if (document.getElementById("pattern-list")) {
		App.init();
	}

	// Always setup form handling if a run-form is present
	if (document.querySelector(".run-form")) {
		App.setupFormHandling();
	}
});
