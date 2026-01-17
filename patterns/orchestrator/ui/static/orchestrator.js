/**
 * orchestrator.js
 * Handles the UI logic for the Orchestrator pattern.
 */

class OrchestratorUI {
	constructor() {
		this.form = document.getElementById("orchestrator-form");
		this.statusBar = document.getElementById("status-bar");
		this.emptyState = document.getElementById("empty-state");
		this.planSection = document.getElementById("plan-section");
		this.planContainer = document.getElementById("plan-container");
		this.statusText = document.getElementById("status-text");
		this.loadingDots = document.getElementById("loading-dots");
		this.synthesisSection = document.getElementById("synthesis-section");
		this.synthesisOutput = document.getElementById("synthesis-output");
		this.submitBtn = document.getElementById("submit-btn");

		this.workerCards = {};
		this.setupEventListeners();
	}

	setupEventListeners() {
		if (this.form) {
			this.form.onsubmit = (e) => this.handleSubmit(e);
		}
	}

	handleSubmit(e) {
		e.preventDefault();
		const prompt = new FormData(this.form).get("prompt");
		this.resetUI();

		const url = `/stream_orchestrator?prompt=${encodeURIComponent(prompt)}`;
		const handler = new StreamHandler(
			url,
			(data) => this.handleMessage(data),
			() => this.handleComplete(),
			(error) => this.handleError(error),
		);
		handler.start();
	}

	resetUI() {
		if (this.emptyState) this.emptyState.classList.add("hidden");
		if (this.statusBar) this.statusBar.classList.remove("hidden");
		if (this.planSection) this.planSection.classList.add("hidden");
		if (this.planContainer) this.planContainer.innerHTML = "";
		if (this.synthesisSection) this.synthesisSection.classList.add("hidden");
		if (this.synthesisOutput) this.synthesisOutput.innerText = "";
		if (this.statusText) this.statusText.innerText = "Initializing Manager...";
		if (this.loadingDots) this.loadingDots.classList.remove("hidden");

		if (this.submitBtn) {
			this.submitBtn.disabled = true;
			this.submitBtn.classList.add("opacity-50", "pointer-events-none");
		}
		this.workerCards = {};
		this.fullSynthesisContent = "";
	}

	handleMessage(data) {
		switch (data.type) {
			case "status":
				if (this.statusText) this.statusText.innerText = data.message;
				break;
			case "plan":
				this.renderPlan(data.plan);
				break;
			case "worker_start":
				this.activateWorker(data.task_id);
				break;
			case "worker_complete":
				this.completeWorker(data.task_id);
				break;
			case "synthesis_step":
				this.handleSynthesisStep(data.content);
				break;
			case "complete":
				this.handleComplete();
				break;
		}
	}

	renderPlan(plan) {
		if (!this.planSection || !this.planContainer) return;

		const template = document.getElementById("worker-card-template");
		if (!template) {
			console.error("Worker card template not found");
			return;
		}

		this.planSection.classList.remove("hidden");

		plan.tasks.forEach((task, index) => {
			const clone = template.content.cloneNode(true);
			const card = clone.querySelector(".worker-card");

			card.id = `task-${index}`;

			// Safe text content population
			card.querySelector(".worker-type").textContent = task.worker_type;
			card.querySelector(".worker-rationale").textContent = task.description;

			this.planContainer.appendChild(clone);

			// Re-select the card from the DOM to ensure we have the live element reference
			// (cloneNode returns a fragment, appending it consumes it)
			this.workerCards[index] = document.getElementById(`task-${index}`);

			setTimeout(() => {
				if (this.workerCards[index]) {
					this.workerCards[index].classList.remove("translate-y-4");
				}
			}, 50);
		});
	}

	activateWorker(taskId) {
		const card = this.workerCards[taskId];
		if (card) {
			card.classList.add(
				"active",
				"opacity-100",
				"ring-2",
				"ring-indigo-500/40",
				"bg-indigo-500/5",
				"scale-[1.01]",
			);
			card.querySelector(".status-indicator").className =
				"status-indicator w-3 h-3 bg-indigo-500 rounded-full animate-ping";
			card.querySelector(".worker-progress").classList.remove("hidden");
		}
	}

	completeWorker(taskId) {
		const card = this.workerCards[taskId];
		if (card) {
			card.classList.remove(
				"active",
				"ring-2",
				"ring-indigo-500/40",
				"scale-[1.01]",
			);
			card.classList.add("ring-2", "ring-emerald-500/20");
			card.querySelector(".status-indicator").className =
				"status-indicator w-3 h-3 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]";
			card.querySelector(".worker-progress").classList.add("hidden");
			card.querySelector(".worker-done").classList.remove("hidden");
		}
	}

	handleSynthesisStep(content) {
		if (!this.synthesisSection || !this.synthesisOutput) return;
		this.synthesisSection.classList.remove("hidden");
		if (this.statusBar) {
			this.statusBar.classList.add(
				"bg-emerald-500/10",
				"border-emerald-500/20",
			);
			this.statusBar.classList.remove("bg-slate-900/80", "border-white/10");
		}
		if (this.statusText) {
			this.statusText.innerText = "Synthesis: Finalizing Output";
			this.statusText.classList.add("text-emerald-400");
			this.statusText.classList.remove("text-white");
		}

		// Accumulate and parse markdown
		this.fullSynthesisContent = (this.fullSynthesisContent || "") + content;
		this.synthesisOutput.innerHTML =
			typeof marked !== "undefined" && typeof DOMPurify !== "undefined"
				? DOMPurify.sanitize(marked.parse(this.fullSynthesisContent))
				: this.fullSynthesisContent;

		this.synthesisOutput.scrollIntoView({ behavior: "smooth", block: "end" });
	}

	handleComplete() {
		if (this.statusText) {
			this.statusText.innerText = "Mission Success";
			this.statusText.classList.add("text-emerald-400");
		}
		if (this.loadingDots) this.loadingDots.classList.add("hidden");
		if (this.submitBtn) {
			this.submitBtn.disabled = false;
			this.submitBtn.classList.remove("opacity-50", "pointer-events-none");
		}
	}

	handleError(_error) {
		if (this.statusBar) {
			this.statusBar.className =
				"flex items-center gap-3 px-8 py-5 bg-red-500/10 border border-red-500/20 rounded-3xl text-red-400";
		}
		if (this.statusText) this.statusText.innerText = "Error: Link Severed";
		if (this.submitBtn) {
			this.submitBtn.disabled = false;
			this.submitBtn.classList.remove("opacity-50", "pointer-events-none");
		}
	}
}

// Initialize when ready
document.addEventListener("DOMContentLoaded", () => {
	new OrchestratorUI();
});
