window.setScenario = (type) => {
	const input = document.getElementById("log-input");
	if (type === "p1") {
		input.value =
			"PaymentService failed with 500 error for User 123. Transaction ID: tx_999.";
	} else if (type === "p2") {
		input.value =
			"Database connection timeout in InventoryService. Retrying...";
	} else if (type === "p3") {
		input.value =
			"The dashboard is loading slowly for User 456. Page load time 5s.";
	}
};

document.addEventListener("DOMContentLoaded", () => {
	const btnRun = document.getElementById("btn-run-pipeline");
	const logInput = document.getElementById("log-input");

	// Steps
	const stepExtract = document.getElementById("step-extract");
	const stepAssess = document.getElementById("step-assess");
	const stepCommunicate = document.getElementById("step-communicate");

	// Outputs
	const emailSubject = document.getElementById("email-subject");
	const emailBody = document.getElementById("email-body");

	btnRun.addEventListener("click", async () => {
		const text = logInput.value.trim();
		if (!text) return;

		// Reset UI
		btnRun.disabled = true;
		emailSubject.textContent = "...";
		emailBody.innerHTML = '<p class="text-muted">Processing...</p>';

		[stepExtract, stepAssess, stepCommunicate].forEach((s) => {
			s.classList.remove("active", "completed");
		});
		document.querySelector(".triage-wrapper").classList.add("pipeline-active");

		// Simulate Stepper Progress (Fake visual delay for better UX)
		// In a real streaming set up, we'd bind to actual events.
		// Here we just animate through the stages while we await the backend.

		stepExtract.classList.add("active");

		try {
			// Start the actual request
			const responsePromise = fetch("/sequential/run", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					input_text: text,
				}),
			});

			// VISUAL FLOURISH: Wait a bit to show "Extracting"
			await new Promise((r) => setTimeout(r, 800));
			stepExtract.classList.remove("active");
			stepExtract.classList.add("completed");
			stepAssess.classList.add("active");

			// Wait a bit to show "Assessing"
			await new Promise((r) => setTimeout(r, 800));
			stepAssess.classList.remove("active");
			stepAssess.classList.add("completed");
			stepCommunicate.classList.add("active");

			const response = await responsePromise;
			const data = await response.json();

			// Finalize
			stepCommunicate.classList.remove("active");
			stepCommunicate.classList.add("completed");

			// Allow user to think "Communicating" happened briefly
			await new Promise((r) => setTimeout(r, 600));

			// Parse Output
			// The agent returns a JSON string with subject and body.
			const resultText = data.output;
			let subject = "Incident Report";
			let body = resultText; // Default to raw text in case of error
			try {
				const emailData = JSON.parse(resultText);
				subject = emailData.subject || subject;
				body = emailData.body || body;
			} catch (e) {
				console.error("Failed to parse agent response as JSON, showing raw output.", e);
			}
			emailSubject.textContent = subject;
			emailBody.innerHTML = DOMPurify.sanitize(body.replace(/\n/g, "<br>"));
		} catch (e) {
			console.error(e);
			emailBody.innerHTML = `<p class="text-error">Error: ${e.message}</p>`;
		} finally {
			btnRun.disabled = false;
			document
				.querySelector(".triage-wrapper")
				.classList.remove("pipeline-active");
		}
	});
});
