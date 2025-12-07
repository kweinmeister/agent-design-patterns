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
				outputs[key].innerHTML = "";
			}
			submitBtn.disabled = true;

			// Start stream
			const eventSource = new EventSource(
				`/stream_voting?prompt=${encodeURIComponent(prompt)}`,
			);

			// Accumulate text for markdown parsing
			const state = {
				humorous: "",
				professional: "",
				urgent: "",
				judge: "",
			};

			eventSource.onmessage = (event) => {
				const data = JSON.parse(event.data);

				if (data.type === "step") {
					const agent = data.agent; // humorous, professional, urgent, judge
					if (outputs[agent]) {
						// Reveal judge section when first token arrives
						if (
							agent === "judge" &&
							judgeSection &&
							judgeSection.style.display === "none"
						) {
							judgeSection.style.display = "block";
						}

						state[agent] += data.content;
						if (typeof marked !== "undefined") {
							outputs[agent].innerHTML = marked.parse(state[agent]);
						} else {
							outputs[agent].textContent = state[agent];
						}
					}
				} else if (data.type === "complete") {
					eventSource.close();
					submitBtn.disabled = false;
				}
			};

			eventSource.onerror = (err) => {
				console.error("EventSource failed:", err);
				eventSource.close();
				submitBtn.disabled = false;
			};
		});
	}
});
