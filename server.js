'use strict';

/**
 * National Public Grievance Portal — Express Backend Server (Hardened v3)
 * ---------------------------------------------------------------
 * Changes over v2:
 *  - Hybrid AI inference: prefers persistent FastAPI/native HTTP microservice
 *    (zero subprocess overhead), auto-falls back to Python subprocess
 *  - Microservice liveness probe every 30 s with live status in /api/health
 *  - SLA breach count added to /api/analytics
 *  - All v2 hardening retained (write-lock, helmet, rate-limit, validation)
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

// ── Valid enum values ─────────────────────────────────────────
const VALID_CATEGORIES = [
    'Water Supply & Quality',
    'Sanitation & Garbage',
    'Roads & Potholes',
    'Electricity & Power Cut',
    'Public Healthcare & Clinics',
];
const VALID_STATUSES = [
    'Submitted', 'Under Review', 'In Progress',
    'Dispatched', 'Resolved', 'Flagged Duplicate',
];
const VALID_PRIORITIES = ['Critical', 'High', 'Medium', 'Low'];

// ── Security headers ──────────────────────────────────────────
app.use(helmet({ contentSecurityPolicy: false })); // CSP off so CDN scripts load

// ── CORS ──────────────────────────────────────────────────────
const CORS_ORIGIN = process.env.CORS_ORIGIN
    ? process.env.CORS_ORIGIN.split(',').map(s => s.trim())
    : [`http://localhost:${PORT}`, `http://127.0.0.1:${PORT}`];

app.use(cors({
    origin: process.env.NODE_ENV === 'production' ? CORS_ORIGIN : '*',
    methods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
}));

// ── Rate limiting ─────────────────────────────────────────────
// Grievance submission: max 20 per 10-minute window per IP
const submitLimiter = rateLimit({
    windowMs: 10 * 60 * 1000,
    max: 20,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many submissions from this IP. Please try again later.' },
});

// Admin PATCH: max 60 per minute per IP
const adminLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 60,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many admin requests. Slow down.' },
});

// ── Body parsing ──────────────────────────────────────────────
app.use(express.json({ limit: '256kb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ── Request logger ────────────────────────────────────────────
app.use((req, res, next) => {
    const start = Date.now();
    res.on('finish', () => {
        const ms = Date.now() - start;
        console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} → ${res.statusCode} (${ms}ms)`);
    });
    next();
});

// ── Persistence ───────────────────────────────────────────────
const DB_PATH = path.join(__dirname, 'data_store', 'grievances_db.json');

/**
 * Write-lock: correct implementation.
 * Chain the next write AFTER the current resolves (not on catch).
 * Each fn is called once; any rejection stays inside writeLock but
 * does NOT re-invoke fn, so the lock always advances.
 */
let writeLock = Promise.resolve();
function withWriteLock(fn) {
    writeLock = writeLock.then(() => fn(), () => fn());
    return writeLock;
}

function loadDB() {
    if (!fs.existsSync(DB_PATH)) {
        const seed = [
            {
                id: 'GRV-2026-8941',
                text: 'Main water pipeline burst near Station Road. Thousands of gallons leaking.',
                area: 'Anna Nagar',
                language: 'en',
                category: 'Water Supply & Quality',
                priority: 'Critical',
                department: 'Department of Water Resources & Sanitation',
                status: 'Dispatched',
                days_open: 1,
                duplicate_matched: false,
                created_at: new Date(Date.now() - 86400000).toISOString(),
                explanation: 'Critical hazard keyword (burst) detected.',
            },
            {
                id: 'GRV-2026-3120',
                text: 'वार्ड नंबर 10 में पिछले 4 दिनों से कचरा नहीं उठाया गया है।',
                area: 'Gandhi Chowk',
                language: 'hi',
                category: 'Sanitation & Garbage',
                priority: 'High',
                department: 'Municipal Solid Waste Management Department',
                status: 'Under Review',
                days_open: 4,
                duplicate_matched: false,
                created_at: new Date(Date.now() - 172800000).toISOString(),
                explanation: 'High duration open (4 days).',
            },
        ];
        fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
        fs.writeFileSync(DB_PATH, JSON.stringify(seed, null, 2), 'utf8');
        return seed;
    }
    try {
        return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
    } catch (err) {
        console.error('[DB] Read error:', err.message);
        return [];
    }
}

function saveDB(records) {
    fs.writeFileSync(DB_PATH, JSON.stringify(records, null, 2), 'utf8');
}

// ── Python subprocess inference (fallback) ────────────────────
const PYTHON_TIMEOUT_MS = 45_000;

function runPythonPipeline(payload) {
    return new Promise((resolve, reject) => {
        const py = spawn('python', ['run_pipeline_bridge.py'], {
            cwd: __dirname,
            env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
        });

        let output = '';
        let errorOutput = '';
        let timedOut = false;

        const timer = setTimeout(() => {
            timedOut = true;
            py.kill('SIGKILL');
            reject(new Error('Python pipeline timed out after 45 seconds.'));
        }, PYTHON_TIMEOUT_MS);

        py.stdout.on('data', d => { output += d.toString('utf8'); });
        py.stderr.on('data', d => { errorOutput += d.toString('utf8'); });

        py.on('close', code => {
            clearTimeout(timer);
            if (timedOut) return;
            if (code !== 0 && !output.trim()) {
                console.error('[Python] non-zero exit:', errorOutput.slice(0, 500));
                return reject(new Error('AI pipeline process failed.'));
            }
            try {
                const parsed = JSON.parse(output.trim());
                if (parsed.error) return reject(new Error(`Pipeline error: ${parsed.error}`));
                resolve(parsed);
            } catch {
                console.error('[Python] JSON parse failed. Raw:', output.slice(0, 200));
                reject(new Error('AI pipeline returned invalid output.'));
            }
        });

        py.on('error', err => {
            clearTimeout(timer);
            console.error('[Python] spawn error:', err.message);
            reject(new Error('Failed to start AI pipeline. Ensure Python is installed.'));
        });

        py.stdin.write(JSON.stringify(payload), 'utf8');
        py.stdin.end();
    });
}

// ── AI Microservice HTTP client (primary path) ────────────────
const AI_SERVICE_HOST = process.env.AI_SERVICE_HOST || '127.0.0.1';
const AI_SERVICE_PORT = parseInt(process.env.AI_SERVICE_PORT || '8000', 10);
let microserviceAvailable = false;

function callAIMicroservice(payload) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify(payload);
        const options = {
            hostname: AI_SERVICE_HOST,
            port: AI_SERVICE_PORT,
            path: '/api/v1/triage',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body),
            },
            timeout: 30_000,
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.error) return reject(new Error(`Microservice: ${parsed.error}`));
                    resolve(parsed);
                } catch {
                    reject(new Error('Microservice returned invalid JSON.'));
                }
            });
        });

        req.on('timeout', () => { req.destroy(); reject(new Error('Microservice timed out.')); });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

function probeMicroservice() {
    const req = http.request({
        hostname: AI_SERVICE_HOST,
        port: AI_SERVICE_PORT,
        path: '/api/v1/health',
        method: 'GET',
        timeout: 3_000,
    }, (res) => {
        const wasDown = !microserviceAvailable;
        microserviceAvailable = res.statusCode === 200;
        if (wasDown && microserviceAvailable) {
            console.log(`✓ [AI] Microservice online at http://${AI_SERVICE_HOST}:${AI_SERVICE_PORT} — persistent inference active.`);
        }
        res.resume();
    });
    req.on('error', () => {
        if (microserviceAvailable) console.warn('[AI] Microservice offline — falling back to subprocess.');
        microserviceAvailable = false;
    });
    req.on('timeout', () => { req.destroy(); microserviceAvailable = false; });
    req.end();
}

// Probe on startup and every 30 seconds
probeMicroservice();
setInterval(probeMicroservice, 30_000);

// Hybrid router: microservice → subprocess fallback
async function runInference(payload) {
    if (microserviceAvailable) {
        try {
            const result = await callAIMicroservice(payload);
            return result;
        } catch (err) {
            console.warn('[AI] Microservice call failed, switching to subprocess:', err.message);
            microserviceAvailable = false; // trigger re-probe on next interval
        }
    }
    return runPythonPipeline(payload);
}

// ── Input validation ──────────────────────────────────────────
const MAX_TEXT = 2000;
const MIN_TEXT = 10;
const ID_REGEX = /^GRV-\d{4}-\d{4}$/;

function validateGrievanceText(text) {
    if (!text || typeof text !== 'string') return 'Grievance text is required.';
    const t = text.trim();
    if (t.length < MIN_TEXT) return `Minimum ${MIN_TEXT} characters required.`;
    if (t.length > MAX_TEXT) return `Maximum ${MAX_TEXT} characters allowed (got ${t.length}).`;
    return null;
}

// ── ID generator ──────────────────────────────────────────────
function newTicketId() {
    return `GRV-2026-${Math.floor(1000 + Math.random() * 9000)}`;
}

// ══════════════════════════════════════════════════════════════
//  API ROUTES
// ══════════════════════════════════════════════════════════════

// POST /api/process-grievance  — Citizen submission
app.post('/api/process-grievance', submitLimiter, async (req, res) => {
    const { text, area } = req.body ?? {};
    const err = validateGrievanceText(text);
    if (err) return res.status(400).json({ error: err });

    // area sanitization
    const safeArea = (typeof area === 'string' ? area.trim().slice(0, 100) : null) || 'General Municipality';

    try {
        const aiResult = await runInference({ text: text.trim(), area: safeArea, days_open: 0 });

        const newRecord = {
            id: newTicketId(),
            text: text.trim(),
            area: safeArea,
            language: aiResult.language_detection.language,
            category: aiResult.classification.predicted_category,
            category_confidence: aiResult.classification.confidence,
            priority: aiResult.priority.priority,
            priority_reason: aiResult.priority.reason,
            priority_method: aiResult.priority.method,
            priority_confidence: aiResult.priority.confidence,
            needs_review: aiResult.priority.confidence < 0.65 && aiResult.priority.method === 'ml',
            department: aiResult.routing.target_department,
            sla_hours: aiResult.routing.sla_target_hours,
            status: aiResult.duplicate_check.is_duplicate ? 'Flagged Duplicate' : 'Submitted',
            days_open: 0,
            duplicate_matched: aiResult.duplicate_check.is_duplicate,
            matched_complaint: aiResult.duplicate_check.matched_complaint,
            similarity_score: aiResult.duplicate_check.similarity_score,
            explanation: aiResult.explanation.summary,
            key_terms: aiResult.explanation.key_diagnostic_terms,
            created_at: new Date().toISOString(),
        };

        await withWriteLock(() => {
            const db = loadDB();
            db.unshift(newRecord);
            saveDB(db);
        });

        return res.json({ success: true, ticket: newRecord, ai_analysis: aiResult });
    } catch (err) {
        console.error('[POST /api/process-grievance]', err.message);
        return res.status(500).json({ error: err.message || 'AI pipeline failed. Please try again.' });
    }
});

// GET /api/grievances  — List with filters
app.get('/api/grievances', (req, res) => {
    try {
        let db = loadDB();
        const { priority, category, department, language, search, status } = req.query;

        if (priority) db = db.filter(g => g.priority && g.priority.toLowerCase() === priority.toLowerCase());
        if (category) db = db.filter(g => g.category && g.category.toLowerCase() === category.toLowerCase());
        if (department) db = db.filter(g => g.department && g.department.toLowerCase() === department.toLowerCase());
        if (language) db = db.filter(g => g.language && g.language.toLowerCase() === language.toLowerCase());
        if (status) db = db.filter(g => g.status && g.status.toLowerCase() === status.toLowerCase());
        if (search) {
            const q = search.toLowerCase();
            db = db.filter(g =>
                (g.text && g.text.toLowerCase().includes(q)) ||
                (g.id && g.id.toLowerCase().includes(q)) ||
                (g.area && g.area.toLowerCase().includes(q))
            );
        }

        return res.json({ total: db.length, grievances: db });
    } catch (err) {
        console.error('[GET /api/grievances]', err.message);
        return res.status(500).json({ error: 'Failed to load grievances.' });
    }
});

// GET /api/grievances/:id  — Single ticket lookup (fixes O(N) client-side search)
app.get('/api/grievances/:id', (req, res) => {
    const { id } = req.params;
    if (!ID_REGEX.test(id)) return res.status(400).json({ error: 'Invalid ticket ID format.' });
    try {
        const db = loadDB();
        const record = db.find(g => g.id === id);
        if (!record) return res.status(404).json({ error: 'Ticket not found.' });
        return res.json({ ticket: record });
    } catch (err) {
        console.error('[GET /api/grievances/:id]', err.message);
        return res.status(500).json({ error: 'Failed to fetch ticket.' });
    }
});

// PATCH /api/grievances/:id  — Admin update
app.patch('/api/grievances/:id', adminLimiter, (req, res) => {
    const { id } = req.params;
    if (!ID_REGEX.test(id)) return res.status(400).json({ error: 'Invalid ticket ID format.' });

    const { status, priority, department } = req.body ?? {};

    // Validate each supplied field
    if (status && !VALID_STATUSES.includes(status)) return res.status(400).json({ error: `Invalid status. Valid: ${VALID_STATUSES.join(', ')}` });
    if (priority && !VALID_PRIORITIES.includes(priority)) return res.status(400).json({ error: `Invalid priority. Valid: ${VALID_PRIORITIES.join(', ')}` });
    if (department && typeof department !== 'string') return res.status(400).json({ error: 'Department must be a string.' });
    if (!status && !priority && !department) return res.status(400).json({ error: 'Provide at least one field to update (status, priority, department).' });

    try {
        const db = loadDB();
        const index = db.findIndex(g => g.id === id);
        if (index === -1) return res.status(404).json({ error: 'Ticket not found.' });

        if (status) db[index].status = status;
        if (priority) db[index].priority = priority;
        if (department) db[index].department = department.trim().slice(0, 200);
        db[index].updated_at = new Date().toISOString();

        withWriteLock(() => saveDB(db));
        return res.json({ success: true, ticket: db[index] });
    } catch (err) {
        console.error('[PATCH /api/grievances/:id]', err.message);
        return res.status(500).json({ error: 'Failed to update ticket.' });
    }
});

// GET /api/analytics  — Aggregated stats
app.get('/api/analytics', (req, res) => {
    try {
        const db = loadDB();
        const total = db.length;
        const byPrio = { Critical: 0, High: 0, Medium: 0, Low: 0 };
        const byLang = { en: 0, hi: 0, ta: 0, 'en-hi': 0, 'en-ta': 0 };
        const byDept = {};
        const byCat = {};
        // 7-day daily trend buckets
        const trend = {};
        const now = Date.now();
        for (let i = 6; i >= 0; i--) {
            const d = new Date(now - i * 86400000);
            trend[d.toISOString().slice(0, 10)] = 0;
        }
        let dups = 0;
        let needs_review = 0;
        let sla_breached = 0;

        db.forEach(g => {
            if (byPrio[g.priority] !== undefined) byPrio[g.priority]++;
            if (byLang[g.language] !== undefined) byLang[g.language]++;
            byDept[g.department] = (byDept[g.department] || 0) + 1;
            byCat[g.category] = (byCat[g.category] || 0) + 1;
            if (g.duplicate_matched) dups++;
            if (g.needs_review) needs_review++;

            // SLA breach: ticket open longer than its SLA target
            if (g.sla_hours && g.created_at && g.status !== 'Resolved') {
                const ageHours = (now - new Date(g.created_at).getTime()) / 3_600_000;
                if (ageHours > g.sla_hours) sla_breached++;
            }

            // Daily trend (last 7 days)
            if (g.created_at) {
                const day = g.created_at.slice(0, 10);
                if (trend[day] !== undefined) trend[day]++;
            }
        });

        return res.json({
            total_complaints: total,
            priority_breakdown: byPrio,
            duplicate_count: dups,
            duplicate_percentage: total > 0 ? Math.round(dups / total * 100) : 0,
            language_breakdown: byLang,
            department_breakdown: byDept,
            category_breakdown: byCat,
            needs_review_count: needs_review,
            sla_breached_count: sla_breached,
            daily_trend: trend,
        });
    } catch (err) {
        console.error('[GET /api/analytics]', err.message);
        return res.status(500).json({ error: 'Failed to compute analytics.' });
    }
});

// GET /api/health  — Server heartbeat + microservice status
app.get('/api/health', (_req, res) => res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    ai_inference_mode: microserviceAvailable ? 'microservice' : 'subprocess',
    ai_microservice_url: `http://${AI_SERVICE_HOST}:${AI_SERVICE_PORT}`,
}));

// ── 404 handler ───────────────────────────────────────────────
app.use((_req, res) => res.status(404).json({ error: 'Endpoint not found.' }));

// ── Global error handler ──────────────────────────────────────
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
    console.error('[Unhandled]', err);
    res.status(500).json({ error: 'An unexpected error occurred.' });
});

// ── Start ─────────────────────────────────────────────────────
app.listen(PORT, () => {
    console.log(`✓ National Public Grievance Portal running at http://localhost:${PORT}`);
    console.log(`  NODE_ENV: ${process.env.NODE_ENV || 'development'}`);
    console.log(`  CORS: ${process.env.NODE_ENV === 'production' ? CORS_ORIGIN.join(', ') : 'open (dev mode)'}`);
});
