// Load knowledge on startup
/** biome-ignore-all lint/correctness/noUnusedVariables: biome-ignore */
document.addEventListener("DOMContentLoaded", loadKnowledge);

async function loadKnowledge() {
	const list = document.getElementById("knowledge-list");
	try {
		const response = await fetch("/rag/knowledge");
		const data = await response.json();

		if (data.documents && data.documents.length > 0) {
			list.innerHTML = data.documents
				.map(
					(doc) => `
                <div class="knowledge-item">
                    <div class="doc-icon">📄</div>
                    <div class="doc-content">${doc}</div>
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
	} catch (error) {
		console.error("Failed to load knowledge:", error);
	}
}

async function ingestKnowledge() {
	const btn = document.getElementById("ingest-btn");
	btn.disabled = true;
	btn.innerHTML = '<span class="spinner"></span> Ingesting...';

	try {
		await fetch("/rag/ingest", { method: "POST" });

		// Poll for updates (simple version)
		let retries = 0;
		const interval = setInterval(async () => {
			await loadKnowledge();
			const list = document.getElementById("knowledge-list");
			if (!list.querySelector(".empty-state") || retries > 10) {
				clearInterval(interval);
				btn.disabled = false;
				btn.textContent = "Ingest Data";
			}
			retries++;
		}, 1000);
	} catch (error) {
		console.error("Ingestion failed:", error);
		btn.disabled = false;
		btn.textContent = "Ingest Data";
	}
}

async function resetKnowledge() {
	if (!confirm("Are you sure you want to clear the knowledge base?")) return;

	try {
		await fetch("/rag/reset", { method: "POST" });
		await loadKnowledge();
	} catch (error) {
		console.error("Reset failed:", error);
	}
}

async function handleQuery(event) {
	event.preventDefault();
	const input = document.getElementById("query-input");
	const history = document.getElementById("chat-history");
	const query = input.value.trim();

	if (!query) return;

	// Add user message
	history.innerHTML += `
        <div class="message user">
            <div class="content">${query}</div>
        </div>
    `;
	input.value = "";
	history.scrollTop = history.scrollHeight;

	// Show loading
	const loadingId = `loading-${Date.now()}`;
	history.innerHTML += `
        <div class="message agent loading" id="${loadingId}">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
    `;
	history.scrollTop = history.scrollHeight;

	try {
		const queryResponse = await fetch("/rag/query", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ query }),
		});
		const data = await queryResponse.json();

		document.getElementById(loadingId).remove();

		let parsedHtml = data.final;
		if (data.final.includes("**")) {
			parsedHtml = marked.parse(data.final);
		}

		history.innerHTML += `
            <div class="message agent">
                <div class="content markdown-body">${parsedHtml}</div>
            </div>
        `;
		history.scrollTop = history.scrollHeight;
	} catch (error) {
		console.error("Query failed:", error);
		document.getElementById(loadingId).remove();
		history.innerHTML += `
            <div class="message agent error">
                <div class="content">Sorry, something went wrong.</div>
            </div>
        `;
	}
}
