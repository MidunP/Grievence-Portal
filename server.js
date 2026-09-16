const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DB_PATH = path.join(__dirname, 'data_store', 'grievances_db.json');

// Ensure DB exists with seed samples if needed
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
                explanation: 'Grievance classified as Water Supply & Quality. Critical hazard keyword (burst) detected.'
            },
            {
                id: 'GRV-2026-3120',
                text: 'वार्ड नंबर 10 में पिछले 4 दिनों से कचरा नहीं उठाया गया है। दुर्गंध फैल रही है।',
                area: 'Gandhi Chowk',
                language: 'hi',
                category: 'Sanitation & Garbage',
                priority: 'High',
                department: 'Municipal Solid Waste Management Department',
                status: 'Under Review',
                days_open: 4,
                duplicate_matched: false,
                created_at: new Date(Date.now() - 172800000).toISOString(),
                explanation: 'Grievance classified as Sanitation & Garbage. High duration open (4 days).'
            },
            {
                id: 'GRV-2026-5542',
                text: 'வார்டு 5 பகுதியில் சாக்கடை நீர் பொங்கி வழிகிறது.',
                area: 'Shanti Vihar',
                language: 'ta',
                category: 'Sanitation & Garbage',
                priority: 'High',
                department: 'Municipal Solid Waste Management Department',
                status: 'In Progress',
                days_open: 2,
                duplicate_matched: false,
                created_at: new Date(Date.now() - 259200000).toISOString(),
                explanation: 'Grievance classified as Sanitation & Garbage. High urgency keywords detected.'
            }
        ];
        fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
        fs.writeFileSync(DB_PATH, JSON.stringify(seed, null, 2), 'utf8');
        return seed;
    }
    try {
        const data = fs.readFileSync(DB_PATH, 'utf8');
        return JSON.parse(data);
    } catch (err) {
        return [];
    }
}

function saveDB(records) {
    fs.writeFileSync(DB_PATH, JSON.stringify(records, null, 2), 'utf8');
}

// Invoke Python AI Pipeline via Stdin/Stdout
function runPythonPipeline(payload) {
    return new Promise((resolve, reject) => {
        const py = spawn('python', ['run_pipeline_bridge.py'], { cwd: __dirname });
        let output = '';
        let errorOutput = '';

        py.stdout.on('data', (data) => {
            output += data.toString();
        });

        py.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });

        py.on('close', (code) => {
            if (code !== 0 && !output) {
                return reject(new Error(`Python process exited with code ${code}: ${errorOutput}`));
            }
            try {
                const parsed = JSON.parse(output.trim());
                resolve(parsed);
            } catch (err) {
                reject(new Error(`Failed to parse Python output: ${output} | Error: ${err.message}`));
            }
        });

        py.stdin.write(JSON.stringify(payload));
        py.stdin.end();
    });
}

// API Routes

// 1. Process New Grievance (Citizen Submission)
app.post('/api/process-grievance', async (req, res) => {
    try {
        const { text, area } = req.body;
        if (!text || !text.trim()) {
            return res.status(400).json({ error: 'Grievance text is required.' });
        }

        const aiResult = await runPythonPipeline({ text, area: area || 'Unknown', days_open: 0 });

        // Construct ticket record
        const ticketId = `GRV-2026-${Math.floor(1000 + Math.random() * 9000)}`;
        const newRecord = {
            id: ticketId,
            text: text.trim(),
            area: area || 'General Municipality',
            language: aiResult.language_detection.language,
            category: aiResult.classification.predicted_category,
            category_confidence: aiResult.classification.confidence,
            priority: aiResult.priority.priority,
            priority_reason: aiResult.priority.reason,
            department: aiResult.routing.target_department,
            sla_hours: aiResult.routing.sla_target_hours,
            status: aiResult.duplicate_check.is_duplicate ? 'Flagged Duplicate' : 'Submitted',
            days_open: 0,
            duplicate_matched: aiResult.duplicate_check.is_duplicate,
            matched_complaint: aiResult.duplicate_check.matched_complaint,
            similarity_score: aiResult.duplicate_check.similarity_score,
            explanation: aiResult.explanation.summary,
            key_terms: aiResult.explanation.key_diagnostic_terms,
            created_at: new Date().toISOString()
        };

        const db = loadDB();
        db.unshift(newRecord);
        saveDB(db);

        res.json({
            success: true,
            ticket: newRecord,
            ai_analysis: aiResult
        });
    } catch (err) {
        console.error('Error processing grievance:', err);
        res.status(500).json({ error: err.message });
    }
});

// 2. Get All Grievances with Filtering
app.get('/api/grievances', (req, res) => {
    const db = loadDB();
    const { priority, category, department, language, search } = req.query;

    let filtered = db;
    if (priority) filtered = filtered.filter(g => g.priority.toLowerCase() === priority.toLowerCase());
    if (category) filtered = filtered.filter(g => g.category.toLowerCase() === category.toLowerCase());
    if (department) filtered = filtered.filter(g => g.department.toLowerCase() === department.toLowerCase());
    if (language) filtered = filtered.filter(g => g.language.toLowerCase() === language.toLowerCase());
    if (search) {
        const query = search.toLowerCase();
        filtered = filtered.filter(g => g.text.toLowerCase().includes(query) || g.id.toLowerCase().includes(query) || g.area.toLowerCase().includes(query));
    }

    res.json({ total: filtered.length, grievances: filtered });
});

// 3. Update Grievance Status / Priority / Department (Admin Action)
app.patch('/api/grievances/:id', (req, res) => {
    const { id } = req.params;
    const { status, priority, department } = req.body;

    const db = loadDB();
    const index = db.findIndex(g => g.id === id);

    if (index === -1) {
        return res.status(404).json({ error: 'Grievance ticket not found' });
    }

    if (status) db[index].status = status;
    if (priority) db[index].priority = priority;
    if (department) db[index].department = department;

    db[index].updated_at = new Date().toISOString();
    saveDB(db);

    res.json({ success: true, ticket: db[index] });
});

// 4. Analytics Summary Endpoint
app.get('/api/analytics', (req, res) => {
    const db = loadDB();
    const total = db.length;

    const critical = db.filter(g => g.priority === 'Critical').length;
    const high = db.filter(g => g.priority === 'High').length;
    const medium = db.filter(g => g.priority === 'Medium').length;
    const low = db.filter(g => g.priority === 'Low').length;
    const duplicates = db.filter(g => g.duplicate_matched).length;

    const byLang = {
        en: db.filter(g => g.language === 'en').length,
        hi: db.filter(g => g.language === 'hi').length,
        ta: db.filter(g => g.language === 'ta').length
    };

    const byDept = {};
    db.forEach(g => {
        byDept[g.department] = (byDept[g.department] || 0) + 1;
    });

    res.json({
        total_complaints: total,
        priority_breakdown: { Critical: critical, High: high, Medium: medium, Low: low },
        duplicate_count: duplicates,
        duplicate_percentage: total > 0 ? Math.round((duplicates / total) * 100) : 0,
        language_breakdown: byLang,
        department_breakdown: byDept
    });
});

app.listen(PORT, () => {
    console.log(`Grievance Portal Full-Stack Server listening on http://localhost:${PORT}`);
});
