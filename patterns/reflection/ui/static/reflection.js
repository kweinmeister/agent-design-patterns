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

			try {
				const eventSource = new EventSource(
					`/stream_reflection?prompt=${encodeURIComponent(prompt)}`,
				);

				const stopLoading = () => {
					if (submitBtn) {
						submitBtn.classList.remove("loading");
						submitBtn.textContent = "Run Agent";
					}
					eventSource.close();
				};

				eventSource.onmessage = (event) => {
					const data = JSON.parse(event.data);

					const card = document.createElement("div");
					const h3 = document.createElement("h3");
					const contentDiv = document.createElement("div");
					contentDiv.className = "content";
					contentDiv.textContent = data.content;

					if (data.role === "final") {
						card.className = "result-card final";
						h3.textContent = "Final Result";
					} else {
						// Apply specific styling based on role
						let cssClass = "result-card";
						if (data.role === "Critic") cssClass += " critique";
						if (data.role === "Refiner") cssClass += " final"; // Re-use final style or keep standard
						card.className = cssClass;
						h3.textContent = data.role;
					}

					card.append(h3, contentDiv);
					resultsGrid.appendChild(card);

					if (data.role === "final") {
						stopLoading();
					}

					// Scroll to bottom
					window.scrollTo(0, document.body.scrollHeight);
				};

				eventSource.onerror = (error) => {
					console.error("SSE Error:", error);
					stopLoading();
				};
			} catch (error) {
				console.error("Fetch error:", error);
				if (submitBtn) {
					submitBtn.classList.remove("loading");
					submitBtn.textContent = "Run Agent";
				}
			}
		});
	}
});
