document.addEventListener('DOMContentLoaded', () => {
    // Tab Navigation
    const navTabs = document.querySelectorAll('.segment-btn');
    const tabContents = document.querySelectorAll('.tab-pane');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));

            tab.classList.add('active');
            document.getElementById(target).classList.remove('hidden');

            if (target === 'admin-tab') {
                loadAdminDashboard();
            }
        });
    });

    // Presets click handler
    const presetBtns = document.querySelectorAll('.btn-preset');
    const textarea = document.getElementById('grievance-text');

    presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            textarea.value = btn.getAttribute('data-text');
            textarea.focus();
        });
    });

    // Form Submission
    const form = document.getElementById('grievance-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');

    const emptyState = document.getElementById('ai-empty-state');
    const resultPanel = document.getElementById('ai-result-content');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = textarea.value.trim();
        const area = document.getElementById('area-select').value;

        if (!text) return;

        // Loading State
        btnText.textContent = 'Executing AI Triage...';
        btnLoader.classList.remove('hidden');
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/process-grievance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, area })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                alert(`Error: ${data.error || 'Failed to process grievance'}`);
                return;
            }

            // Render Results
            renderAIResult(data.ticket, data.ai_analysis);

        } catch (err) {
            console.error(err);
            alert('Network or server error while executing AI pipeline.');
        } finally {
            btnText.textContent = 'Submit Grievance';
            btnLoader.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    function renderAIResult(ticket, ai) {
        emptyState.classList.add('hidden');
        resultPanel.classList.remove('hidden');

        document.getElementById('ticket-id').textContent = ticket.id;
        document.getElementById('ticket-status-badge').textContent = ticket.status;

        // Language
        const langNames = { en: 'English (en)', hi: 'Hindi (हिंदी)', ta: 'Tamil (தமிழ்)' };
        document.getElementById('res-language').textContent = langNames[ai.language_detection.language] || ai.language_detection.language;
        document.getElementById('res-lang-conf').textContent = `${Math.round(ai.language_detection.confidence * 100)}% Confidence (${ai.language_detection.method})`;

        // Category
        document.getElementById('res-category').textContent = ai.classification.predicted_category;
        document.getElementById('res-cat-conf').textContent = `${Math.round(ai.classification.confidence * 100)}% Confidence`;

        // Priority
        const priorityEl = document.getElementById('res-priority');
        priorityEl.textContent = ai.priority.priority;
        priorityEl.className = `priority-pill prio-${ai.priority.priority.toLowerCase()}`;
        document.getElementById('res-prio-reason').textContent = ai.priority.reason;

        // Department & SLA
        document.getElementById('res-department').textContent = ai.routing.target_department;
        document.getElementById('res-sla').textContent = `Target SLA: ${ai.routing.sla_target_hours}h`;

        // Duplicate Check Banner
        const dupAlert = document.getElementById('duplicate-alert');
        if (ai.duplicate_check.is_duplicate) {
            dupAlert.classList.remove('hidden');
            const scorePct = Math.round(ai.duplicate_check.similarity_score * 100);
            document.getElementById('dup-details').textContent = `Matches similar complaint in ${ticket.area} with ${scorePct}% vector match score.`;
        } else {
            dupAlert.classList.add('hidden');
        }

        // Explanation Summary & Diagnostic Terms
        document.getElementById('res-explanation-summary').textContent = ai.explanation.summary;
        const termsContainer = document.getElementById('key-terms-tags');
        termsContainer.innerHTML = '';

        (ai.explanation.key_diagnostic_terms || []).forEach(term => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = term;
            termsContainer.appendChild(chip);
        });
    }

    // Admin Dashboard Loader
    async function loadAdminDashboard() {
        try {
            const [analyticsRes, grievancesRes] = await Promise.all([
                fetch('/api/analytics'),
                fetch('/api/grievances')
            ]);

            const analytics = await analyticsRes.json();
            const grievancesData = await grievancesRes.json();

            // Stats
            document.getElementById('stat-total').textContent = analytics.total_complaints;
            document.getElementById('stat-critical').textContent = analytics.priority_breakdown.Critical || 0;
            document.getElementById('stat-high').textContent = analytics.priority_breakdown.High || 0;
            document.getElementById('stat-duplicates').textContent = analytics.duplicate_count || 0;

            // Render Table
            renderTable(grievancesData.grievances);

        } catch (err) {
            console.error('Failed to load admin stats:', err);
        }
    }

    function renderTable(grievances) {
        const tbody = document.getElementById('grievances-tbody');
        tbody.innerHTML = '';

        if (!grievances || grievances.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 1.5rem; color: var(--text-secondary);">No grievances found.</td></tr>';
            return;
        }

        grievances.forEach(item => {
            const tr = document.createElement('tr');
            const langBadge = item.language === 'hi' ? 'hi' : item.language === 'ta' ? 'ta' : 'en';

            tr.innerHTML = `
        <td><strong>${item.id}</strong></td>
        <td><span class="badge badge-neutral">${langBadge}</span></td>
        <td>${item.area}</td>
        <td style="max-width: 260px;" class="text-truncate">${item.text}</td>
        <td>${item.category}</td>
        <td><span class="priority-pill prio-${item.priority.toLowerCase()}">${item.priority}</span></td>
        <td style="max-width: 200px;" class="text-truncate">${item.department}</td>
        <td><span class="badge badge-success">${item.status}</span></td>
        <td>
          <button class="btn-preset update-btn" data-id="${item.id}">Update</button>
        </td>
      `;
            tbody.appendChild(tr);
        });

        // Add status update handlers
        document.querySelectorAll('.update-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                const nextStatus = prompt('Update Ticket Status (e.g. Dispatched, In Progress, Resolved):', 'In Progress');
                if (nextStatus) {
                    await fetch(`/api/grievances/${id}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: nextStatus })
                    });
                    loadAdminDashboard();
                }
            });
        });
    }

    // Filter Listeners
    ['filter-priority', 'filter-language', 'filter-search'].forEach(id => {
        document.getElementById(id).addEventListener('change', filterTable);
        document.getElementById(id).addEventListener('keyup', filterTable);
    });

    async function filterTable() {
        const prio = document.getElementById('filter-priority').value;
        const lang = document.getElementById('filter-language').value;
        const search = document.getElementById('filter-search').value;

        const params = new URLSearchParams();
        if (prio) params.append('priority', prio);
        if (lang) params.append('language', lang);
        if (search) params.append('search', search);

        const res = await fetch(`/api/grievances?${params.toString()}`);
        const data = await res.json();
        renderTable(data.grievances);
    }
});
