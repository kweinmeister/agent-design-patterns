/**
 * Voting Pattern - UI Logic
 */

document.addEventListener("DOMContentLoaded", () => {
	const form = document.querySelector("form");
	const submitBtn = document.querySelector('button[type="submit"]');
	const container = document.getElementById("results-container");

	// Result elements
	const outputs = {
		humorous: document.getElementById("result-humorous"),
		professional: document.getElementById("result-professional"),
		urgent: document.getElementById("result-urgent"),
		judge: document.getElementById("result-judge"),
	};

	if (form) {
		form.addEventListener("submit", async (e) => {
			e.preventDefault();
			const formData = new FormData(form);
			const prompt = formData.get("prompt");

			if (!prompt) return;

			// Reset UI
			container.style.display = "block";
			// Hide judge section initially
			const judgeSection = document.getElementById("judge-section");
			if (judgeSection) judgeSection.style.display = "none";

			for (const key in outputs) {
				if (outputs[key]) outputs[key].innerHTML = "";
			}
			if (submitBtn) submitBtn.disabled = true;

			// Initialize state for this run
			const accumulatedState = {
				humorous: "",
				professional: "",
				urgent: "",
				judge: "",
			};

			const resetSubmitButton = () => {
				if (submitBtn) {
					submitBtn.disabled = false;
					submitBtn.classList.remove("loading");
					submitBtn.textContent = "Run Agent";
				}
			};

			// Start stream
			const streamHandler = new StreamHandler(
				`/stream_voting?prompt=${encodeURIComponent(prompt)}`,
				(data) => {
					// onMessage
					if (data.type === "step") {
						const agent = data.agent; // humorous, professional, urgent, judge
						if (outputs[agent]) {
							// Reveal judge section when first token arrives
							if (agent === "judge" && judgeSection) {
								judgeSection.style.display = "block";
							}

							if (accumulatedState[agent] !== undefined) {
								accumulatedState[agent] += data.content;
								const currentContent = accumulatedState[agent];

								if (
									typeof marked !== "undefined" &&
									typeof DOMPurify !== "undefined"
								) {
									outputs[agent].innerHTML = DOMPurify.sanitize(
										marked.parse(currentContent),
									);
								} else {
									// Fallback to plain text for security if libraries are missing.
									outputs[agent].textContent = currentContent;
								}
							}
						}
					}
				},
				() => {
					// onComplete
					resetSubmitButton();
				},
				(err) => {
					// onError
					console.error("Stream error:", err);
					resetSubmitButton();
				},
			);
			streamHandler.start();
		});
	}
});
