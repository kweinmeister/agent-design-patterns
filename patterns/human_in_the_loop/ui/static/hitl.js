/**
 * Human in the Loop - UI Logic
 */

const HitlApp = {
	state: {
		sessionId: null,
		isProcessing: false,
		waitingForConfirmation: false,
		isPublished: false,
	},

	init() {
		this.state.sessionId = uuidv4();
		this.setupListeners();
	},

	// Listeners setup
	setupListeners() {
		const prForm = document.getElementById("pr-form");
		if (prForm) {
			prForm.addEventListener("submit", (e) => {
				e.preventDefault();
				const formData = new FormData(prForm);
				// Construct detailed prompt
				const prompt = `Draft a press release for ${formData.get("company")} with the following details:
Product: ${formData.get("product")}
Key Features: ${formData.get("features")}
Target Audience: ${formData.get("audience")}
Availability: ${formData.get("availability")}
Price: ${formData.get("price")}
Vision: ${formData.get("vision")}
Quote: ${formData.get("quote")}
Location: ${formData.get("location")}
Assets: ${formData.get("assets")}

Use this information to create a compelling draft.
IMPORTANT: Return ONLY the press release text. Do not include any conversational preamble like "Here is a draft" or "Sure". Start directly with the headline or dateline.`;

				this.sendMessage(prompt, "Drafting Press Release...");
			});
		}

		// Approve Button
		const btnApprove = document.getElementById("btn-approve");
		if (btnApprove) {
			btnApprove.addEventListener("click", () => {
				this.hideControls();

				if (this.state.waitingForConfirmation) {
					this.sendMessage('{"confirmed": true}');
				} else {
					this.sendMessage("Looks good. Publish it.");
				}
			});
		}

		// Reject Button (Shows input)
		const btnReject = document.getElementById("btn-reject");
		if (btnReject) {
			btnReject.addEventListener("click", () => {
				this.hideControls();
				document
					.getElementById("feedback-input-area")
					.classList.remove("hidden");
				document.getElementById("feedback-text").focus();
			});
		}

		// Send Feedback Button (Regenerate)
		const btnSendFeedback = document.getElementById("btn-send-feedback");
		if (btnSendFeedback) {
			btnSendFeedback.addEventListener("click", () => {
				this.submitFeedback();
			});
		}

		// Cancel Feedback
		const btnCancelFeedback = document.getElementById("btn-cancel-feedback");
		if (btnCancelFeedback) {
			btnCancelFeedback.addEventListener("click", () => {
				document.getElementById("feedback-input-area").classList.add("hidden");
				document.getElementById("action-bar").classList.remove("hidden");
			});
		}

		const feedbackText = document.getElementById("feedback-text");
		if (feedbackText) {
			feedbackText.addEventListener("keypress", (e) => {
				if (e.key === "Enter") this.submitFeedback();
			});
		}
	},

	submitFeedback() {
		const input = document.getElementById("feedback-text");
		const val = input.value.trim();
		if (val) {
			document.getElementById("feedback-input-area").classList.add("hidden");

			if (this.state.waitingForConfirmation) {
				// If waiting for confirmation (ADK state), we must reject via JSON or it hangs?
				// ADK usually expects a confirmation boolean.
				this.sendMessage(JSON.stringify({ confirmed: false, reason: val }));
			} else {
				// Just drafting feedback
				this.sendMessage(
					`I don't like this draft. Change this: ${val}. Regenerate the draft.`,
				);
			}
			input.value = "";
		}
	},

	async sendMessage(text, statusText = "Processing...") {
		if (this.state.isProcessing) return;
		this.state.isProcessing = true;
		this.setLoading(true, statusText);
		this.hideControls(); // Hide while processing

		try {
			const response = await fetch("/hitl/run", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					prompt: text,
					session_id: this.state.sessionId,
				}),
			});

			const data = await response.json();

			if (data.history && data.history.length > 0) {
				const lastMsg = data.history[data.history.length - 1];
				if (lastMsg.role !== "user") {
					this.updateDocument(lastMsg.content);

					// State Detection using Structural Flags from Backend
					// 1. Success / Published
					if (data.is_published) {
						this.state.waitingForConfirmation = false;
						this.state.isPublished = true;

						const btn = document.getElementById("btn-generate");
						if (btn) btn.textContent = "Published! ✅";
					}
					// 2. Confirmation Needed
					else if (data.requires_confirmation) {
						this.state.waitingForConfirmation = true;
						this.showControls();
					}
					// 3. Fallback: Draft Review (Normal response)
					else {
						this.state.waitingForConfirmation = false;
						this.showControls(); // Show buttons for "Draft Review" step
					}
				}
			}
		} catch (err) {
			console.error(err);
			this.updateDocument("Error communicating with agent.", true);
		} finally {
			this.state.isProcessing = false;

			// Use dedicated state variable to determine button state
			const btn = document.getElementById("btn-generate");
			if (btn && !this.state.isPublished) {
				this.setLoading(false);
			} else if (btn) {
				btn.disabled = false;
			}
		}
	},

	showControls() {
		document.getElementById("action-bar").classList.remove("hidden");
	},

	hideControls() {
		document.getElementById("action-bar").classList.add("hidden");
	},

	updateDocument(content, isSystem = false) {
		const container = document.getElementById("document-preview");
		if (!container) return;

		if (isSystem) {
			if (content.toLowerCase().includes("error")) {
				container.innerHTML = `<div class="placeholder-text" style="color:red"><p>${content}</p></div>`;
			}
			return;
		}

		// Render Markdown
		let safeContent = content;
		if (typeof DOMPurify !== "undefined" && typeof marked !== "undefined") {
			safeContent = DOMPurify.sanitize(marked.parse(content));
		} else if (typeof marked !== "undefined") {
			safeContent = marked.parse(content);
		} else {
			// Fallback for text
			safeContent = content.replace(/\n/g, "<br>");
		}

		container.innerHTML = safeContent;
		container.scrollTop = 0;
	},

	setLoading(loading, statusText = "Processing...") {
		const btn = document.getElementById("btn-generate");
		if (btn) {
			btn.disabled = loading;
			btn.textContent = loading ? statusText : "Draft Press Release";
		}
	},
};

document.addEventListener("DOMContentLoaded", () => {
	HitlApp.init();
});
