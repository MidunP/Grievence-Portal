document.addEventListener('DOMContentLoaded', () => {

    /* ── Toast Notifications ─────────────────────────────────── */
    function toast(msg, type = 'info') {
        const c = document.getElementById('toast-container');
        if (!c) return;
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.textContent = msg;
        c.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    }

    /* ── Dark / Light Theme Toggle ───────────────────────────── */
    const themeBtn = document.getElementById('theme-toggle-btn');
    const savedTheme = localStorage.getItem('janseva-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (themeBtn) {
        themeBtn.textContent = savedTheme === 'light' ? '☀️' : '🌙';
        themeBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('janseva-theme', next);
            themeBtn.textContent = next === 'light' ? '☀️' : '🌙';
        });
    }

    /* ── Navigation Tabs ─────────────────────────────────────── */
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => { p.classList.remove('active'); p.classList.add('hidden'); });
            btn.classList.add('active');
            const pane = document.getElementById(target);
            if (pane) {
                pane.classList.remove('hidden');
                pane.classList.add('active');
            }
            if (target === 'admin-tab') loadAdmin();
        });
    });
    document.querySelectorAll('.tab-pane:not(.active)').forEach(p => p.classList.add('hidden'));

    /* ── Character Counter ───────────────────────────────────── */
    const textarea = document.getElementById('grievance-text');
    const charCount = document.getElementById('char-count');
    if (textarea && charCount) {
        textarea.addEventListener('input', () => {
            charCount.textContent = textarea.value.length;
        });
    }

    /* ── Sample Input Buttons ────────────────────────────────── */
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!textarea) return;
            textarea.value = btn.dataset.text;
            if (charCount) charCount.textContent = textarea.value.length;
            textarea.focus();
        });
    });

    /* ── Web Speech API (Voice Input) ────────────────────────── */
    const voiceBtn = document.getElementById('voice-btn');
    const voiceStatus = document.getElementById('voice-status');
    const voiceIcon = document.getElementById('voice-icon');
    let recognition = null;
    let isListening = false;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition && voiceBtn) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-IN'; // Default to English (India), supports hi-IN / ta-IN

        recognition.onstart = () => {
            isListening = true;
            voiceBtn.classList.add('listening');
            if (voiceStatus) voiceStatus.textContent = 'Listening...';
            if (voiceIcon) voiceIcon.textContent = '🔴';
        };

        recognition.onresult = (e) => {
            let transcript = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                transcript += e.results[i][0].transcript;
            }
            if (textarea) {
                textarea.value = transcript;
                if (charCount) charCount.textContent = textarea.value.length;
            }
        };

        recognition.onerror = (e) => {
            toast(`Voice recognition error: ${e.error}`, 'error');
            stopListening();
        };

        recognition.onend = () => {
            stopListening();
        };

        voiceBtn.addEventListener('click', () => {
            if (isListening) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (err) {
                    toast('Voice recognition start failed.', 'error');
                }
            }
        });
    } else if (voiceBtn) {
        voiceBtn.title = 'Web Speech API is not supported in this browser.';
        voiceBtn.style.opacity = '0.6';
    }

    function stopListening() {
        isListening = false;
        if (voiceBtn) voiceBtn.classList.remove('listening');
        if (voiceStatus) voiceStatus.textContent = 'Voice Input';
        if (voiceIcon) voiceIcon.textContent = '🎤';
    }

    /* ── Grievance Submission Form ───────────────────────────── */
    const form = document.getElementById('grievance-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const emptyState = document.getElementById('ai-empty-state');
    const resultContent = document.getElementById('ai-result-content');

    const LANG_MAP = {
        en: 'English (en)',
        hi: 'Hindi (hi)',
        ta: 'Tamil (ta)',
        'en-hi': 'Hinglish (en-hi)',
        'en-ta': 'Tanglish (en-ta)'
    };

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = textarea.value.trim();
            const area = document.getElementById('area-select').value;
            if (!text) {
                toast('Please enter a grievance description.', 'error');
                return;
            }
            if (text.length < 10) {
                toast('Description must be at least 10 characters long.', 'error');
                return;
            }

            btnText.textContent = 'Processing with AI Triage...';
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
                toast(`Grievance ${data.ticket.id} filed successfully!`, 'success');
            } catch {
                toast('Network error. Is the server running?', 'error');
            } finally {
                btnText.textContent = 'Submit to AI Triage Engine';
                btnLoader.classList.add('hidden');
                submitBtn.disabled = false;
            }
        });
    }

    function renderResult(ticket, ai) {
        if (emptyState) emptyState.classList.add('hidden');
        if (resultContent) resultContent.classList.remove('hidden');

        document.getElementById('ticket-id').textContent = ticket.id;
        document.getElementById('ticket-status-badge').textContent = ticket.status;

        const langKey = ai.language_detection.language;
        document.getElementById('res-language').textContent = LANG_MAP[langKey] || langKey;
        document.getElementById('res-lang-conf').textContent = `${Math.round((ai.language_detection.confidence || 1) * 100)}% (${ai.language_detection.method})`;

        document.getElementById('res-category').textContent = ai.classification.predicted_category;
        document.getElementById('res-cat-conf').textContent = `${Math.round(ai.classification.confidence * 100)}% confidence`;

        const prioEl = document.getElementById('res-priority');
        prioEl.textContent = ai.priority.priority;
        prioEl.className = `prio-tag prio-${ai.priority.priority.toLowerCase()}`;
        document.getElementById('res-prio-reason').textContent = ai.priority.reason;

        // Review badge
        const reviewBadge = document.getElementById('res-review-badge');
        if (ticket.needs_review || (ai.priority.confidence < 0.65 && ai.priority.method === 'ml')) {
            if (reviewBadge) reviewBadge.classList.remove('hidden');
        } else {
            if (reviewBadge) reviewBadge.classList.add('hidden');
        }

        document.getElementById('res-department').textContent = ai.routing.target_department;
        document.getElementById('res-sla').textContent = `SLA: ${ai.routing.sla_target_hours}h`;

        const dupEl = document.getElementById('duplicate-alert');
        if (ai.duplicate_check.is_duplicate) {
            dupEl.classList.remove('hidden');
            const pct = Math.round(ai.duplicate_check.similarity_score * 100);
            document.getElementById('dup-details').textContent = `Matches an existing complaint in ${ticket.area} (${pct}% vector similarity).`;
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

    /* ── Direct Ticket Tracking ──────────────────────────────── */
    const trackBtn = document.getElementById('track-btn');
    const trackInput = document.getElementById('track-input');
    const trackResult = document.getElementById('track-result');
    const trackEmpty = document.getElementById('track-empty');

    const STATUS_ORDER = ['Submitted', 'Under Review', 'In Progress', 'Dispatched', 'Resolved'];
    const TL_IDS = ['tl-submitted', 'tl-review', 'tl-progress', 'tl-dispatched', 'tl-resolved'];
    const TL_LINES = ['tl-line-1', 'tl-line-2', 'tl-line-3', 'tl-line-4'];

    if (trackBtn) trackBtn.addEventListener('click', doTrack);
    if (trackInput) trackInput.addEventListener('keydown', e => { if (e.key === 'Enter') doTrack(); });

    async function doTrack() {
        const id = trackInput.value.trim().toUpperCase();
        if (!id) {
            toast('Please enter a reference number.', 'error');
            return;
        }

        try {
            // Direct GET /api/grievances/:id endpoint (O(1) look up instead of O(N) full fetch)
            const res = await fetch(`/api/grievances/${encodeURIComponent(id)}`);
            const data = await res.json();

            if (!res.ok || data.error || !data.ticket) {
                toast(`Ticket "${id}" not found. Verify your reference ID.`, 'error');
                if (trackResult) trackResult.classList.add('hidden');
                if (trackEmpty) trackEmpty.classList.remove('hidden');
                return;
            }

            renderTrack(data.ticket);
        } catch {
            toast('Failed to fetch ticket data. Please check your network connection.', 'error');
        }
    }

    function renderTrack(t) {
        if (trackEmpty) trackEmpty.classList.add('hidden');
        if (trackResult) trackResult.classList.remove('hidden');

        document.getElementById('track-id').textContent = t.id;
        document.getElementById('track-status-badge').textContent = t.status || '--';
        document.getElementById('track-category').textContent = t.category || '--';
        document.getElementById('track-area').textContent = t.area || '--';
        document.getElementById('track-dept').textContent = t.department || '--';
        document.getElementById('track-sla').textContent = t.sla_hours ? `${t.sla_hours}h` : '--';
        document.getElementById('track-lang').textContent = LANG_MAP[t.language] || t.language || '--';
        document.getElementById('track-text').textContent = t.text || '--';

        const prioEl = document.getElementById('track-priority');
        prioEl.textContent = t.priority || '--';
        prioEl.className = `prio-tag prio-${(t.priority || 'low').toLowerCase()}`;

        const d = t.created_at ? new Date(t.created_at) : null;
        document.getElementById('track-date').textContent = d
            ? d.toLocaleDateString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
            : '--';

        const idx = STATUS_ORDER.indexOf(t.status);
        TL_IDS.forEach((id, i) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.remove('active', 'done');
            if (i < idx) el.classList.add('done');
            else if (i === idx) el.classList.add('active');
        });
        TL_LINES.forEach((id, i) => {
            const el = document.getElementById(id);
            if (el) el.classList.toggle('done', i < idx);
        });
    }

    /* ── Operations Center Admin Panel & Pagination ───────────── */
    let prioChart = null;
    let langChart = null;
    let currentGrievances = [];
    let currentPage = 1;
    const PAGE_SIZE = 10;

    const refreshBtn = document.getElementById('admin-refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', loadAdmin);

    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) exportBtn.addEventListener('click', exportCSV);

    async function loadAdmin() {
        try {
            const [aRes, gRes] = await Promise.all([
                fetch('/api/analytics'),
                fetch('/api/grievances')
            ]);
            const analytics = await aRes.json();
            const gData = await gRes.json();

            document.getElementById('stat-total').textContent = analytics.total_complaints ?? 0;
            document.getElementById('stat-critical').textContent = analytics.priority_breakdown?.Critical ?? 0;
            document.getElementById('stat-high').textContent = analytics.priority_breakdown?.High ?? 0;
            document.getElementById('stat-duplicates').textContent = analytics.duplicate_count ?? 0;

            // Review banner
            const banner = document.getElementById('review-queue-banner');
            const reviewCount = document.getElementById('review-queue-count');
            if (analytics.needs_review_count > 0) {
                if (banner) banner.classList.remove('hidden');
                if (reviewCount) reviewCount.textContent = analytics.needs_review_count;
            } else if (banner) {
                banner.classList.add('hidden');
            }

            buildCharts(analytics);
            currentGrievances = gData.grievances || [];
            currentPage = 1;
            renderPaginatedTable();
        } catch {
            toast('Failed to load operations dashboard.', 'error');
        }
    }

    const CHART_OPTS = {
        plugins: {
            legend: {
                labels: {
                    color: '#8a8d9a',
                    font: { family: 'Inter', size: 11 },
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
        const pCanvas = document.getElementById('priority-chart');
        if (pCanvas) {
            prioChart = new Chart(pCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [pb.Critical || 0, pb.High || 0, pb.Medium || 0, pb.Low || 0],
                        backgroundColor: ['#ff4757', '#ffa502', '#2ed573', '#70a1ff'],
                        borderWidth: 0
                    }]
                },
                options: CHART_OPTS
            });
        }

        if (langChart) langChart.destroy();
        const lCanvas = document.getElementById('lang-chart');
        if (lCanvas) {
            langChart = new Chart(lCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['English', 'Hindi', 'Tamil', 'Hinglish', 'Tanglish'],
                    datasets: [{
                        data: [lb.en || 0, lb.hi || 0, lb.ta || 0, lb['en-hi'] || 0, lb['en-ta'] || 0],
                        backgroundColor: ['#6c63ff', '#ff6b6b', '#4ecdc4', '#ffd166', '#a8ff78'],
                        borderWidth: 0
                    }]
                },
                options: CHART_OPTS
            });
        }
    }

    function renderPaginatedTable() {
        const tbody = document.getElementById('grievances-tbody');
        const count = document.getElementById('queue-count');
        const pagContainer = document.getElementById('table-pagination');
        if (!tbody) return;

        tbody.innerHTML = '';
        const total = currentGrievances.length;
        if (count) count.textContent = `${total} complaint${total !== 1 ? 's' : ''} total`;

        if (total === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="table-empty">No grievances match the current filter.</td></tr>';
            if (pagContainer) pagContainer.innerHTML = '';
            return;
        }

        const totalPages = Math.ceil(total / PAGE_SIZE);
        if (currentPage > totalPages) currentPage = totalPages;
        const start = (currentPage - 1) * PAGE_SIZE;
        const pageItems = currentGrievances.slice(start, start + PAGE_SIZE);

        pageItems.forEach(item => {
            const tr = document.createElement('tr');
            if (item.needs_review) tr.className = 'needs-review-row';

            tr.innerHTML = `
        <td class="ref-mono">${item.id}</td>
        <td>${item.language || '--'}</td>
        <td>${item.area || '--'}</td>
        <td><span class="text-clip-td" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</span></td>
        <td>${item.category || '--'}</td>
        <td>
          <span class="prio-tag prio-${(item.priority || 'low').toLowerCase()}">${item.priority}</span>
          ${item.needs_review ? '<span title="Flagged for review due to low ML confidence">⚠️</span>' : ''}
        </td>
        <td><span class="text-clip-td" title="${escapeHtml(item.department)}">${escapeHtml(item.department || '--')}</span></td>
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

        // Add save event listeners
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
                    const data = await res.json();
                    if (res.ok && data.success) {
                        toast(`Ticket ${id} status updated to "${select.value}".`, 'success');
                    } else {
                        toast(data.error || `Failed to update ${id}.`, 'error');
                    }
                } catch {
                    toast('Network error while updating status.', 'error');
                } finally {
                    btn.textContent = 'Save';
                    btn.disabled = false;
                }
            });
        });

        // Render Pagination Controls
        if (pagContainer) {
            pagContainer.innerHTML = '';
            if (totalPages <= 1) return;

            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.textContent = '‹';
            prevBtn.disabled = currentPage === 1;
            prevBtn.addEventListener('click', () => { currentPage--; renderPaginatedTable(); });
            pagContainer.appendChild(prevBtn);

            for (let p = 1; p <= totalPages; p++) {
                const pBtn = document.createElement('button');
                pBtn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
                pBtn.textContent = p;
                pBtn.addEventListener('click', () => { currentPage = p; renderPaginatedTable(); });
                pagContainer.appendChild(pBtn);
            }

            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.textContent = '›';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.addEventListener('click', () => { currentPage++; renderPaginatedTable(); });
            pagContainer.appendChild(nextBtn);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    /* ── CSV Export ──────────────────────────────────────────── */
    function exportCSV() {
        if (!currentGrievances.length) {
            toast('No data available to export.', 'error');
            return;
        }

        const headers = ['Ticket ID', 'Language', 'Division/Area', 'Category', 'Priority', 'Department', 'SLA Hours', 'Status', 'Needs Review', 'Created At', 'Description'];
        const rows = currentGrievances.map(g => [
            g.id,
            g.language || '',
            g.area || '',
            g.category || '',
            g.priority || '',
            g.department || '',
            g.sla_hours || '',
            g.status || '',
            g.needs_review ? 'YES' : 'NO',
            g.created_at || '',
            `"${(g.text || '').replace(/"/g, '""')}"`
        ]);

        const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `JanSeva_Grievances_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast('Grievance queue exported to CSV.', 'success');
    }

    /* ── Admin Filters ───────────────────────────────────────── */
    ['filter-priority', 'filter-language', 'filter-review', 'filter-search'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('change', applyFilter);
        if (id === 'filter-search') el.addEventListener('keyup', applyFilter);
    });

    async function applyFilter() {
        const prio = document.getElementById('filter-priority')?.value;
        const lang = document.getElementById('filter-language')?.value;
        const rev = document.getElementById('filter-review')?.value;
        const search = document.getElementById('filter-search')?.value;

        const params = new URLSearchParams();
        if (prio) params.append('priority', prio);
        if (lang) params.append('language', lang);
        if (search) params.append('search', search);

        try {
            const res = await fetch(`/api/grievances?${params}`);
            const data = await res.json();
            let items = data.grievances || [];
            if (rev === 'flagged') {
                items = items.filter(g => g.needs_review);
            }
            currentGrievances = items;
            currentPage = 1;
            renderPaginatedTable();
        } catch { /* silent */ }
    }

});
