document.addEventListener('DOMContentLoaded', () => {

    /* ── Toast ───────────────────────────────────────────────── */
    function toast(msg, type = 'info') {
        const c = document.getElementById('toast-container');
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.textContent = msg;
        c.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    }

    /* ── Tabs ────────────────────────────────────────────────── */
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => { p.classList.remove('active'); p.classList.add('hidden'); });
            btn.classList.add('active');
            const pane = document.getElementById(target);
            pane.classList.remove('hidden');
            pane.classList.add('active');
            if (target === 'admin-tab') loadAdmin();
        });
    });

    /* Make non-active tabs hidden on load */
    document.querySelectorAll('.tab-pane:not(.active)').forEach(p => p.classList.add('hidden'));

    /* ── Character counter ───────────────────────────────────── */
    const textarea = document.getElementById('grievance-text');
    const charCount = document.getElementById('char-count');
    textarea.addEventListener('input', () => { charCount.textContent = textarea.value.length; });

    /* ── Sample inputs ───────────────────────────────────────── */
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            textarea.value = btn.dataset.text;
            charCount.textContent = textarea.value.length;
            textarea.focus();
        });
    });

    /* ── Submit ──────────────────────────────────────────────── */
    const form = document.getElementById('grievance-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const emptyState = document.getElementById('ai-empty-state');
    const result = document.getElementById('ai-result-content');

    const LANG = { en: 'English (en)', hi: 'Hindi (hi)', ta: 'Tamil (ta)' };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = textarea.value.trim();
        const area = document.getElementById('area-select').value;
        if (!text) { toast('Enter a grievance description.', 'error'); return; }

        btnText.textContent = 'Processing...';
        btnLoader.classList.remove('hidden');
        submitBtn.disabled = true;

        try {
            const res = await fetch('/api/process-grievance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, area })
            });
            const data = await res.json();

            if (!res.ok || data.error) {
                toast(data.error || 'AI pipeline failed.', 'error');
                return;
            }

            renderResult(data.ticket, data.ai_analysis);
            toast(`Ticket ${data.ticket.id} filed.`, 'success');
        } catch {
            toast('Network error. Is the server running?', 'error');
        } finally {
            btnText.textContent = 'Submit to AI Triage Engine';
            btnLoader.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    function renderResult(ticket, ai) {
        emptyState.classList.add('hidden');
        result.classList.remove('hidden');

        document.getElementById('ticket-id').textContent = ticket.id;
        document.getElementById('ticket-status-badge').textContent = ticket.status;

        document.getElementById('res-language').textContent = LANG[ai.language_detection.language] || ai.language_detection.language;
        document.getElementById('res-lang-conf').textContent = `${Math.round(ai.language_detection.confidence * 100)}% -- ${ai.language_detection.method}`;

        document.getElementById('res-category').textContent = ai.classification.predicted_category;
        document.getElementById('res-cat-conf').textContent = `${Math.round(ai.classification.confidence * 100)}% confidence`;

        const prioEl = document.getElementById('res-priority');
        prioEl.textContent = ai.priority.priority;
        prioEl.className = `prio-tag prio-${ai.priority.priority.toLowerCase()}`;
        document.getElementById('res-prio-reason').textContent = ai.priority.reason;

        document.getElementById('res-department').textContent = ai.routing.target_department;
        document.getElementById('res-sla').textContent = `SLA: ${ai.routing.sla_target_hours}h`;

        const dupEl = document.getElementById('duplicate-alert');
        if (ai.duplicate_check.is_duplicate) {
            dupEl.classList.remove('hidden');
            const pct = Math.round(ai.duplicate_check.similarity_score * 100);
            document.getElementById('dup-details').textContent = `Matches a similar complaint in ${ticket.area} -- ${pct}% vector similarity.`;
        } else {
            dupEl.classList.add('hidden');
        }

        document.getElementById('res-explanation-summary').textContent = ai.explanation.summary;

        const tags = document.getElementById('key-terms-tags');
        tags.innerHTML = '';
        (ai.explanation.key_diagnostic_terms || []).forEach(t => {
            const chip = document.createElement('span');
            chip.className = 'term-chip';
            chip.textContent = t;
            tags.appendChild(chip);
        });
    }

    /* ── Track ticket ────────────────────────────────────────── */
    const trackBtn = document.getElementById('track-btn');
    const trackInput = document.getElementById('track-input');
    const trackResult = document.getElementById('track-result');
    const trackEmpty = document.getElementById('track-empty');

    const STATUS_ORDER = ['Submitted', 'Under Review', 'In Progress', 'Dispatched', 'Resolved'];
    const TL_IDS = ['tl-submitted', 'tl-review', 'tl-progress', 'tl-dispatched', 'tl-resolved'];
    const TL_LINES = ['tl-line-1', 'tl-line-2', 'tl-line-3', 'tl-line-4'];

    trackBtn.addEventListener('click', doTrack);
    trackInput.addEventListener('keydown', e => { if (e.key === 'Enter') doTrack(); });

    async function doTrack() {
        const id = trackInput.value.trim().toUpperCase();
        if (!id) { toast('Enter a reference number.', 'error'); return; }
        try {
            const res = await fetch('/api/grievances');
            const data = await res.json();
            const t = (data.grievances || []).find(g => g.id.toUpperCase() === id);
            if (!t) {
                toast(`Ticket "${id}" not found.`, 'error');
                trackResult.classList.add('hidden');
                trackEmpty.classList.remove('hidden');
                return;
            }
            renderTrack(t);
        } catch {
            toast('Failed to fetch ticket data.', 'error');
        }
    }

    function renderTrack(t) {
        trackEmpty.classList.add('hidden');
        trackResult.classList.remove('hidden');

        document.getElementById('track-id').textContent = t.id;
        document.getElementById('track-status-badge').textContent = t.status || '--';
        document.getElementById('track-category').textContent = t.category || '--';
        document.getElementById('track-area').textContent = t.area || '--';
        document.getElementById('track-dept').textContent = t.department || '--';
        document.getElementById('track-sla').textContent = t.sla_hours ? `${t.sla_hours}h` : '--';
        document.getElementById('track-lang').textContent = LANG[t.language] || t.language || '--';
        document.getElementById('track-text').textContent = t.text || '--';

        const prioEl = document.getElementById('track-priority');
        prioEl.textContent = t.priority || '--';
        prioEl.className = `prio-tag prio-${(t.priority || 'low').toLowerCase()}`;

        const d = t.created_at ? new Date(t.created_at) : null;
        document.getElementById('track-date').textContent = d
            ? d.toLocaleDateString('en-IN', { dateStyle: 'long' })
            : '--';

        const idx = STATUS_ORDER.indexOf(t.status);
        TL_IDS.forEach((id, i) => {
            const el = document.getElementById(id);
            el.classList.remove('active', 'done');
            if (i < idx) el.classList.add('done');
            else if (i === idx) el.classList.add('active');
        });
        TL_LINES.forEach((id, i) => {
            const el = document.getElementById(id);
            if (el) el.classList.toggle('done', i < idx);
        });
    }

    /* ── Admin ───────────────────────────────────────────────── */
    let prioChart = null;
    let langChart = null;

    document.getElementById('admin-refresh-btn').addEventListener('click', loadAdmin);

    async function loadAdmin() {
        try {
            const [aRes, gRes] = await Promise.all([
                fetch('/api/analytics'),
                fetch('/api/grievances')
            ]);
            const analytics = await aRes.json();
            const gData = await gRes.json();

            document.getElementById('stat-total').textContent = analytics.total_complaints;
            document.getElementById('stat-critical').textContent = analytics.priority_breakdown.Critical || 0;
            document.getElementById('stat-high').textContent = analytics.priority_breakdown.High || 0;
            document.getElementById('stat-duplicates').textContent = analytics.duplicate_count || 0;

            buildCharts(analytics);
            buildTable(gData.grievances || []);
        } catch {
            toast('Failed to load dashboard.', 'error');
        }
    }

    const CHART_OPTS = {
        plugins: {
            legend: {
                labels: {
                    color: '#6a6a6a',
                    font: { family: 'system-ui', size: 11 },
                    boxWidth: 10,
                    padding: 8
                }
            }
        },
        cutout: '65%'
    };

    function buildCharts(a) {
        const pb = a.priority_breakdown || {};
        const lb = a.language_breakdown || {};

        if (prioChart) prioChart.destroy();
        prioChart = new Chart(
            document.getElementById('priority-chart').getContext('2d'),
            {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [pb.Critical || 0, pb.High || 0, pb.Medium || 0, pb.Low || 0],
                        backgroundColor: ['#7a2020', '#7a4a10', '#5a5a10', '#1d3452'],
                        borderColor: ['#b33a3a', '#a06020', '#7a7a20', '#4a7fc1'],
                        borderWidth: 1
                    }]
                },
                options: CHART_OPTS
            }
        );

        if (langChart) langChart.destroy();
        langChart = new Chart(
            document.getElementById('lang-chart').getContext('2d'),
            {
                type: 'doughnut',
                data: {
                    labels: ['English', 'Hindi', 'Tamil'],
                    datasets: [{
                        data: [lb.en || 0, lb.hi || 0, lb.ta || 0],
                        backgroundColor: ['#1d3452', '#5a4a10', '#3a1d5a'],
                        borderColor: ['#4a7fc1', '#a06020', '#7a50c1'],
                        borderWidth: 1
                    }]
                },
                options: CHART_OPTS
            }
        );
    }

    function buildTable(items) {
        const tbody = document.getElementById('grievances-tbody');
        const count = document.getElementById('queue-count');
        tbody.innerHTML = '';
        count.textContent = `${items.length} complaint${items.length !== 1 ? 's' : ''}`;

        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="9" class="table-empty">No grievances found.</td></tr>';
            return;
        }

        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
        <td class="ref-mono">${item.id}</td>
        <td>${item.language || '--'}</td>
        <td>${item.area || '--'}</td>
        <td><span class="text-clip-td" title="${item.text}">${item.text}</span></td>
        <td>${item.category || '--'}</td>
        <td><span class="prio-tag prio-${(item.priority || 'low').toLowerCase()}">${item.priority}</span></td>
        <td><span class="text-clip-td" title="${item.department}">${item.department || '--'}</span></td>
        <td>
          <select class="status-select" data-id="${item.id}">
            ${['Submitted', 'Under Review', 'In Progress', 'Dispatched', 'Resolved', 'Flagged Duplicate']
                    .map(s => `<option${item.status === s ? ' selected' : ''}>${s}</option>`)
                    .join('')}
          </select>
        </td>
        <td>
          <button class="save-btn" data-id="${item.id}">Save</button>
        </td>
      `;
            tbody.appendChild(tr);
        });

        document.querySelectorAll('.save-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const select = btn.closest('tr').querySelector('.status-select');
                btn.textContent = '...';
                btn.disabled = true;
                try {
                    const res = await fetch(`/api/grievances/${id}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: select.value })
                    });
                    if (res.ok) toast(`${id} updated.`, 'success');
                    else toast(`Failed to update ${id}.`, 'error');
                } catch {
                    toast('Network error.', 'error');
                } finally {
                    btn.textContent = 'Save';
                    btn.disabled = false;
                }
            });
        });
    }

    /* ── Filters ─────────────────────────────────────────────── */
    ['filter-priority', 'filter-language', 'filter-search'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('change', applyFilter);
        el.addEventListener('keyup', applyFilter);
    });

    async function applyFilter() {
        const prio = document.getElementById('filter-priority').value;
        const lang = document.getElementById('filter-language').value;
        const search = document.getElementById('filter-search').value;
        const params = new URLSearchParams();
        if (prio) params.append('priority', prio);
        if (lang) params.append('language', lang);
        if (search) params.append('search', search);
        try {
            const res = await fetch(`/api/grievances?${params}`);
            const data = await res.json();
            buildTable(data.grievances || []);
        } catch { /* silent */ }
    }

});
