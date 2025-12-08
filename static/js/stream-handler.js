/** biome-ignore-all lint/correctness/noUnusedVariables: This class is used in other scripts */
/**
 * Generic StreamHandler for SSE events.
 */
class StreamHandler {
	/**
	 * @param {string} url - The URL to connect to.
	 * @param {Function} onMessage - Callback for each message.
	 * @param {Function} onComplete - Callback when stream completes.
	 * @param {Function} onError - Callback when error occurs.
	 */
	constructor(url, onMessage, onComplete, onError) {
		this.url = url;
		this.onMessage = onMessage;
		this.onComplete = onComplete;
		this.onError = onError;
		this.eventSource = null;
	}

	start() {
		try {
			this.eventSource = new EventSource(this.url);

			this.eventSource.onmessage = (event) => {
				const data = JSON.parse(event.data);
				this.onMessage(data);

				if (
					data.type === "complete" ||
					(data.role === "final" && data.type !== "step")
				) {
					this.close();
					if (this.onComplete) this.onComplete();
				}
			};

			this.eventSource.onerror = (error) => {
				console.error("SSE Error:", error);
				this.close();
				if (this.onError) this.onError(error);
			};
		} catch (error) {
			console.error("StreamHandler setup error:", error);
			if (this.onError) this.onError(error);
		}
	}

	close() {
		if (this.eventSource) {
			this.eventSource.close();
			this.eventSource = null;
		}
	}
}
