document.addEventListener('DOMContentLoaded', () => {
    const ingestBtn = document.getElementById('ingest-btn');
    const knowledgeInput = document.getElementById('knowledge-input');
    const ingestStatus = document.getElementById('ingest-status');

    const queryBtn = document.getElementById('query-btn');
    const queryInput = document.getElementById('query-input');

    const responseContainer = document.getElementById('response-container');
    const responseText = document.getElementById('response-text');

    // New UI Elements
    const statsBar = document.getElementById('stats-bar');
    const timeTotal = document.getElementById('time-total');
    const timeRetrieval = document.getElementById('time-retrieval');
    const timeRerank = document.getElementById('time-rerank');
    const timeGen = document.getElementById('time-gen');

    const citationsContainer = document.getElementById('citations-container');
    const citationsList = document.getElementById('citations-list');

    // Ingest Handler
    ingestBtn.addEventListener('click', async () => {
        const text = knowledgeInput.value.trim();
        if (!text) {
            ingestStatus.textContent = "Please enter some text first.";
            ingestStatus.style.color = "#ef4444";
            return;
        }

        ingestStatus.textContent = "Chunking & Indexing...";
        ingestStatus.style.color = "var(--text-muted)";
        ingestBtn.disabled = true;

        try {
            const res = await fetch('/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await res.json();

            if (res.ok) {
                ingestStatus.textContent = data.message || "Knowledge stored successfully!";
                ingestStatus.style.color = "#22c55e";
            } else {
                throw new Error(data.message || "Unknown error");
            }
        } catch (err) {
            ingestStatus.textContent = "Error: " + err.message;
            ingestStatus.style.color = "#ef4444";
        } finally {
            ingestBtn.disabled = false;
        }
    });

    // --- PDF Upload Logic ---
    const pdfInput = document.getElementById('pdf-input');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadBtn = document.getElementById('upload-btn');

    pdfInput.addEventListener('change', () => {
        if (pdfInput.files.length > 0) {
            fileNameDisplay.textContent = pdfInput.files[0].name;
            uploadBtn.disabled = false;
        } else {
            fileNameDisplay.textContent = "Choose a PDF file...";
            uploadBtn.disabled = true;
        }
    });

    uploadBtn.addEventListener('click', async () => {
        const file = pdfInput.files[0];
        if (!file) return;

        ingestStatus.textContent = "Uploading & Parsing PDF...";
        ingestStatus.style.color = "var(--text-muted)";
        uploadBtn.disabled = true;
        ingestBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData // No Content-Type header needed for FormData
            });
            const data = await res.json();

            if (res.ok) {
                ingestStatus.textContent = data.message;
                ingestStatus.style.color = "#22c55e";
            } else {
                throw new Error(data.message || "Upload failed");
            }
        } catch (err) {
            ingestStatus.textContent = "Error: " + err.message;
            ingestStatus.style.color = "#ef4444";
        } finally {
            uploadBtn.disabled = false;
            ingestBtn.disabled = false;
        }
    });

    // Query Handler
    async function handleQuery() {
        const question = queryInput.value.trim();
        if (!question) return;

        // Reset UI
        responseContainer.classList.remove('hidden');
        statsBar.classList.add('hidden');
        citationsContainer.classList.add('hidden');

        responseText.innerHTML = '<span class="typing-effect">Thinking... (Retrieving & Reranking)</span>';

        queryBtn.disabled = true;

        try {
            const res = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await res.json();

            if (res.ok) {
                // Render Answer (Markdown)
                responseText.innerHTML = marked.parse(data.answer);

                // Render Stats
                statsBar.classList.remove('hidden');
                if (data.timings) {
                    timeTotal.textContent = `${data.timings.total || 0}s`;
                    timeRetrieval.textContent = `${data.timings.retrieval || 0}s`;
                    timeRerank.textContent = `${data.timings.reranking || 0}s`;
                    timeGen.textContent = `${data.timings.generation || 0}s`;
                }

                // Render Citations
                if (data.citations && data.citations.length > 0) {
                    citationsContainer.classList.remove('hidden');
                    citationsList.innerHTML = '';

                    data.citations.forEach(cit => {
                        const card = document.createElement('div');
                        card.className = 'citation-card';
                        card.innerHTML = `
                            <div>
                                <span class="citation-badge">[${cit.id}]</span>
                            </div>
                            <div class="citation-text">"${cit.text}"</div>
                        `;
                        citationsList.appendChild(card);
                    });
                }

            } else {
                responseText.textContent = "Error: " + (data.message || "Unknown error");
            }
        } catch (err) {
            responseText.textContent = "Network error: " + err.message;
        } finally {
            queryBtn.disabled = false;
        }
    }

    queryBtn.addEventListener('click', handleQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleQuery();
    });
});
