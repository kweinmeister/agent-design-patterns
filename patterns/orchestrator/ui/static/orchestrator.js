/**
 * orchestrator.js
 * Handles the UI logic for the Orchestrator pattern.
 */

class OrchestratorUI {
    constructor() {
        this.form = document.getElementById('orchestrator-form');
        this.statusBar = document.getElementById('status-bar'); // Updated
        this.emptyState = document.getElementById('empty-state');
        this.planSection = document.getElementById('plan-section');
        this.planContainer = document.getElementById('plan-container');
        this.statusText = document.getElementById('status-text');
        this.loadingDots = document.getElementById('loading-dots');
        this.synthesisSection = document.getElementById('synthesis-section');
        this.synthesisOutput = document.getElementById('synthesis-output');
        this.submitBtn = document.getElementById('submit-btn');
        
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
        const prompt = new FormData(this.form).get('prompt');
        this.resetUI();

        const url = `/stream_orchestrator?prompt=${encodeURIComponent(prompt)}`;
        const handler = new StreamHandler(
            url,
            (data) => this.handleMessage(data),
            () => this.handleComplete(),
            (error) => this.handleError(error)
        );
        handler.start();
    }

    resetUI() {
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.statusBar) this.statusBar.classList.remove('hidden');
        if (this.planSection) this.planSection.classList.add('hidden');
        if (this.planContainer) this.planContainer.innerHTML = '';
        if (this.synthesisSection) this.synthesisSection.classList.add('hidden');
        if (this.synthesisOutput) this.synthesisOutput.innerText = '';
        if (this.statusText) this.statusText.innerText = 'Initializing Manager...';
        if (this.loadingDots) this.loadingDots.classList.remove('hidden');
        
        if (this.submitBtn) {
            this.submitBtn.disabled = true;
            this.submitBtn.classList.add('opacity-50', 'pointer-events-none');
        }
        this.workerCards = {};
        this.fullSynthesisContent = '';
    }

    handleMessage(data) {
        switch (data.type) {
            case 'status':
                if (this.statusText) this.statusText.innerText = data.message;
                break;
            case 'plan':
                this.renderPlan(data.plan);
                break;
            case 'worker_start':
                this.activateWorker(data.task_id);
                break;
            case 'worker_complete':
                this.completeWorker(data.task_id);
                break;
            case 'synthesis_step':
                this.handleSynthesisStep(data.content);
                break;
            case 'complete':
                this.handleComplete();
                break;
        }
    }

    renderPlan(plan) {
        if (!this.planSection || !this.planContainer) return;
        this.planSection.classList.remove('hidden');
        plan.tasks.forEach((task, index) => {
            const card = document.createElement('div');
            card.className = 'worker-card glass-card p-6 rounded-3xl opacity-40 transform translate-y-4 border border-white/5';
            card.id = `task-${index}`;
            card.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <span class="px-3 py-1 bg-indigo-500/10 rounded-full text-[10px] font-black text-indigo-400 uppercase tracking-widest">${task.worker_type}</span>
                    <div class="status-indicator w-3 h-3 bg-slate-800 rounded-full border border-white/10"></div>
                </div>
                <h4 class="text-white font-bold text-lg mb-2">${task.title}</h4>
                <p class="text-sm text-slate-400 leading-relaxed">${task.description}</p>
                
                <div class="mt-6 hidden worker-progress space-y-2">
                    <div class="flex justify-between items-end">
                        <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-widest leading-none">Processing</span>
                        <span class="text-[10px] text-slate-500 font-mono leading-none">worker-${index}</span>
                    </div>
                    <div class="h-1 bg-slate-950 rounded-full overflow-hidden">
                        <div class="h-full bg-indigo-500 w-1/3 animate-progress shadow-[0_0_10px_rgba(99,102,241,0.5)]"></div>
                    </div>
                </div>
                
                <div class="mt-6 hidden worker-done px-4 py-2 bg-emerald-500/10 rounded-xl text-emerald-400 font-bold text-[10px] flex items-center gap-2 uppercase tracking-tighter">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                    Task Verified
                </div>
            `;
            this.planContainer.appendChild(card);
            this.workerCards[index] = card;
            setTimeout(() => card.classList.remove('translate-y-4'), 50);
        });
    }

    activateWorker(taskId) {
        const card = this.workerCards[taskId];
        if (card) {
            card.classList.add('active', 'opacity-100', 'ring-2', 'ring-indigo-500/40', 'bg-indigo-500/5', 'scale-[1.01]');
            card.querySelector('.status-indicator').className = 'status-indicator w-3 h-3 bg-indigo-500 rounded-full animate-ping';
            card.querySelector('.worker-progress').classList.remove('hidden');
        }
    }

    completeWorker(taskId) {
        const card = this.workerCards[taskId];
        if (card) {
            card.classList.remove('active', 'ring-2', 'ring-indigo-500/40', 'scale-[1.01]');
            card.classList.add('ring-2', 'ring-emerald-500/20');
            card.querySelector('.status-indicator').className = 'status-indicator w-3 h-3 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]';
            card.querySelector('.worker-progress').classList.add('hidden');
            card.querySelector('.worker-done').classList.remove('hidden');
        }
    }

    handleSynthesisStep(content) {
        if (!this.synthesisSection || !this.synthesisOutput) return;
        this.synthesisSection.classList.remove('hidden');
        if (this.statusBar) {
            this.statusBar.classList.add('bg-emerald-500/10', 'border-emerald-500/20');
            this.statusBar.classList.remove('bg-slate-900/80', 'border-white/10');
        }
        if (this.statusText) {
            this.statusText.innerText = 'Synthesis: Finalizing Output';
            this.statusText.classList.add('text-emerald-400');
            this.statusText.classList.remove('text-white');
        }
        
        // Accumulate and parse markdown
        this.fullSynthesisContent = (this.fullSynthesisContent || '') + content;
        this.synthesisOutput.innerHTML = typeof marked !== 'undefined' 
            ? marked.parse(this.fullSynthesisContent) 
            : this.fullSynthesisContent;
            
        this.synthesisOutput.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    handleComplete() {
        if (this.statusText) {
            this.statusText.innerText = 'Mission Success';
            this.statusText.classList.add('text-emerald-400');
        }
        if (this.loadingDots) this.loadingDots.classList.add('hidden');
        if (this.submitBtn) {
            this.submitBtn.disabled = false;
            this.submitBtn.classList.remove('opacity-50', 'pointer-events-none');
        }
    }

    handleError(error) {
        if (this.statusBar) {
            this.statusBar.className = 'flex items-center gap-3 px-8 py-5 bg-red-500/10 border border-red-500/20 rounded-3xl text-red-400';
        }
        if (this.statusText) this.statusText.innerText = 'Error: Link Severed';
        if (this.submitBtn) {
            this.submitBtn.disabled = false;
            this.submitBtn.classList.remove('opacity-50', 'pointer-events-none');
        }
    }
}

// Initialize when ready
document.addEventListener('DOMContentLoaded', () => {
    new OrchestratorUI();
});
