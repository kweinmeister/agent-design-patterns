document.addEventListener("DOMContentLoaded", () => {
	const form = document.querySelector(".run-form");
	const resultsGrid = document.getElementById("results-grid");

	if (form) {
		form.addEventListener("submit", async (e) => {
			e.preventDefault();

			const formData = new FormData(form);
			const prompt = formData.get("prompt");
			const submitBtn = form.querySelector('button[type="submit"]');

			if (!prompt) return;

			// Clear previous results
			resultsGrid.innerHTML = "";
			resultsGrid.style.display = "grid";
			submitBtn.disabled = true;

			try {
				const streamHandler = new StreamHandler(
					`/stream_reflection?prompt=${encodeURIComponent(prompt)}`,
					(data) => {
						// onMessage
						if (data.type === "step") {
							const card = document.createElement("div");
							const h3 = document.createElement("h3");
							const contentDiv = document.createElement("div");
							contentDiv.className = "content";
							contentDiv.textContent = data.content;

							// Apply specific styling based on role
							let cssClass = "result-card";
							if (data.role === "CriticAgent") cssClass += " critique";
							if (data.role === "RefinerAgent") cssClass += " final";
							card.className = cssClass;
							h3.textContent = data.role;

							card.append(h3, contentDiv);
							resultsGrid.appendChild(card);
							window.scrollTo(0, document.body.scrollHeight);
						} else if (data.type === "complete") {
							// Optional: Handle completion explicitly if needed
							submitBtn.disabled = false;
						}
					},
					() => {
						// onComplete
						if (submitBtn) {
							submitBtn.disabled = false;
							submitBtn.classList.remove("loading");
							submitBtn.textContent = "Run Agent";
						}
					},
					(_error) => {
						// onError
						if (submitBtn) {
							submitBtn.disabled = false;
							submitBtn.classList.remove("loading");
							submitBtn.textContent = "Run Agent";
						}
					},
				);
				streamHandler.start();
			} catch (error) {
				console.error("Fetch error:", error);
				if (submitBtn) {
					submitBtn.disabled = false;
					submitBtn.classList.remove("loading");
					submitBtn.textContent = "Run Agent";
				}
			}
		});
	}
});
