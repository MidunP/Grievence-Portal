/* ==========================================================================
   National Public Grievance Portal — Administrative Client Script
   Compliant with DARPG Citizen Charter & Public Administration Workflows
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Backend warm-up (prevents cold-start delay on Render free tier) ── */
    fetch('/api/health', { priority: 'low' }).catch(() => {});

    /* ── Live Portal Clock ───────────────────────────────────── */
    const clockEl = document.getElementById('portal-live-clock');
    function updateLiveClock() {
        if (!clockEl) return;
        const now = new Date();
        const opts = {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false, timeZone: 'Asia/Kolkata'
        };
        clockEl.textContent = 'Official Time: ' + now.toLocaleString('en-IN', opts) + ' IST';
    }
    updateLiveClock();
    setInterval(updateLiveClock, 1000);

    /* ── Toast Notifications ─────────────────────────────────── */
    function toast(msg, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const el = document.createElement('div');
        el.className = `gov-toast gov-toast-${type}`;
        el.textContent = msg;
        container.appendChild(el);
        setTimeout(() => el.remove(), 4200);
    }

    /* ── Accessibility: Font Size Switcher ───────────────────── */
    const fontBtns = {
        sm: document.getElementById('font-decrease'),
        md: document.getElementById('font-reset'),
        lg: document.getElementById('font-increase')
    };

    function setFontSize(size) {
        document.documentElement.setAttribute('data-font-size', size);
        localStorage.setItem('gov-font-size', size);
        Object.entries(fontBtns).forEach(([k, btn]) => {
            if (btn) btn.classList.toggle('active', k === size);
        });
    }

    const savedFontSize = localStorage.getItem('gov-font-size') || localStorage.getItem('janseva-font-size') || 'md';
    setFontSize(savedFontSize);

    if (fontBtns.sm) fontBtns.sm.addEventListener('click', () => setFontSize('sm'));
    if (fontBtns.md) fontBtns.md.addEventListener('click', () => setFontSize('md'));
    if (fontBtns.lg) fontBtns.lg.addEventListener('click', () => setFontSize('lg'));

    /* ── Accessibility: High Contrast Mode Toggle ────────────── */
    const contrastBtn = document.getElementById('contrast-toggle');
    const contrastText = document.getElementById('contrast-text');
    const savedTheme = localStorage.getItem('gov-theme') || 'gov-light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (contrastText) {
        contrastText.textContent = savedTheme === 'gov-contrast' ? 'Standard View' : 'High Contrast';
    }

    if (contrastBtn) {
        contrastBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'gov-contrast' ? 'gov-light' : 'gov-contrast';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('gov-theme', next);
            if (contrastText) {
                contrastText.textContent = next === 'gov-contrast' ? 'Standard View' : 'High Contrast';
            }
        });
    }

    /* ── Multi-Language / Regional Language System (I18N) ───── */
    const I18N = {
        hi: {
            topDept: 'प्रशासनिक सुधार और लोक शिकायत निदेशालय',
            headerSec: 'राष्ट्रीय लोक शिकायत निवारण प्रणाली',
            portalTitle: 'National Public Grievance Portal',
            portalSub: 'Department of Administrative Reforms & Public Grievances (DARPG) • Government of India',
            noticeTag: 'NOTICE / सूचना',
            noticeText: 'Citizen Grievances are prioritized strictly as per DARPG Citizen Charter Timelines. Emergency hazards (Water burst, Live wires, Contamination) are triaged within 12-24 hours. Multilingual submission supported in English, हिन्दी, தமிழ், and Romanized colloquial scripts. Toll-free helpline 1913 operational 24x7.',
            navLodgeSec: 'शिकायत दर्ज करें',
            navTrackSec: 'स्थिति जानें',
            navAdminSec: 'अधिकारी डैशबोर्ड',
            navCharterSec: 'नागरिक अधिकार पत्र',
            navGovSec: 'मॉडल ऑडिट',
            pageTitleLodge: 'Lodge a Public Grievance / नागरिक शिकायत पंजीकरण',
            formGroTitle: 'Citizen Grievance Submission Form / शिकायत विवरण पत्र',
            sampleLabel: 'Standard Municipal Case Templates (Select for verification):',
            partA: 'Part A: Complainant Details (Optional / ऐच्छिक विवरण)',
            citizenName: 'Citizen Name / नागरिक का नाम',
            citizenContact: 'Mobile Number for SMS Tracking / मोबाइल नंबर',
            partB: 'Part B: Administrative Jurisdiction & Incident Location (स्थान)',
            areaSelect: 'Municipal Division / प्रशासनिक क्षेत्र',
            landmark: 'Specific Landmark / निकटतम लैंडमार्क',
            partC: 'Part C: Detailed Grievance Description (शिकायत का विस्तृत विवरण)',
            descLabel: 'Full Description of Public Grievance / समस्या का पूर्ण विवरण',
            voiceStatus: 'Speak Complaint / बोलकर लिखें',
            submitBtn: 'Submit Grievance for Redressal / शिकायत प्रस्तुत करें',
            docketTitle: 'Official Grievance Docket / पावती रसीद',
            pageTitleTrack: 'Track Grievance Status / शिकायत निवारण स्थिति',
            trackInputLabel: 'Grievance Docket Number / शिकायत संख्या:',
            trackBtnText: 'Track Grievance / खोजें',
            pageTitleNodal: 'Nodal Officer Operations Console / शिकायत निवारण कार्यपालक प्रकोष्ठ',
            pageTitleCharter: 'Citizen Charter & Statutory Resolution Timelines / नागरिक अधिकार पत्र',
            pageTitleGov: 'Algorithmic Governance & Ethical AI Disclosure / मॉडल ऑडिट रिपोर्ट',
            footerTitle: 'National Public Grievance Portal • राष्ट्रीय लोक शिकायत पोर्टल'
        },
        ta: {
            topDept: 'நிர்வாக சீர்திருத்தங்கள் மற்றும் பொதுக் குறைதீர்ப்புத் துறை',
            headerSec: 'தேசிய பொதுக் குறைதீர்ப்பு மற்றும் கண்காணிப்பு தளம்',
            portalTitle: 'National Public Grievance Portal',
            portalSub: 'Department of Administrative Reforms & Public Grievances (DARPG) • Government of India',
            noticeTag: 'NOTICE / அறிவிப்பு',
            noticeText: 'குடிமக்கள் சாசன காலக்கெடுவின்படி புகார்கள் முன்னுரிமைப்படுத்தப்படுகின்றன. அவசர ஆபத்துகள் (குடிநீர் குழாய் உடைப்பு, மின்கம்பி ஆபத்து, நீர் மாசுபடுதல்) 12-24 மணி நேரத்திற்குள் தீர்க்கப்படுகின்றன. கட்டணமில்லா உதவி எண் 1913 24 மணி நேரமும் செயல்படுகிறது.',
            navLodgeSec: 'குறை பதிவு செய்',
            navTrackSec: 'நிலவரம் அறிதல்',
            navAdminSec: 'அதிகாரி பலகை',
            navCharterSec: 'குடிமக்கள் சாசனம்',
            navGovSec: 'மாதிரி தணிக்கை',
            pageTitleLodge: 'Lodge a Public Grievance / பொதுக் குறைதீர்ப்புப் பதிவு',
            formGroTitle: 'Citizen Grievance Submission Form / புகார் விவரப் படிவம்',
            sampleLabel: 'வழக்கமான நகராட்சி மாதிரிகள் (சரிபார்ப்புக்கு தேர்ந்தெடுக்கவும்):',
            partA: 'Part A: Complainant Details (Optional / மனுதாரர் விவரங்கள்)',
            citizenName: 'Citizen Name / மனுதாரர் பெயர்',
            citizenContact: 'Mobile Number for SMS Tracking / அலைபேசி எண்',
            partB: 'Part B: Administrative Jurisdiction & Incident Location (நிர்வாக எல்லை)',
            areaSelect: 'Municipal Division / நகராட்சி நிர்வாகப் பிரிவு',
            landmark: 'Specific Landmark / முக்கிய அடையாளம்',
            partC: 'Part C: Detailed Grievance Description (விரிவான குறை விவரம்)',
            descLabel: 'Full Description of Public Grievance / பொதுக் குறையின் முழு விவரம்',
            voiceStatus: 'Speak Complaint / புகாரைப் பேசவும்',
            submitBtn: 'Submit Grievance for Redressal / புகார் சமர்ப்பிக்க',
            docketTitle: 'Official Grievance Docket / அதிகாரப்பூர்வ ரசீது',
            pageTitleTrack: 'Track Grievance Status / குறைதீர்ப்பு நிலை அறிதல்',
            trackInputLabel: 'Grievance Docket Number / புகார் பதிவு எண்:',
            trackBtnText: 'Track Grievance / தேடுக',
            pageTitleNodal: 'Nodal Officer Operations Console / நோடல் அதிகாரி கட்டுப்பாட்டு மையம்',
            pageTitleCharter: 'Citizen Charter & Statutory Resolution Timelines / குடிமக்கள் சாசனம்',
            pageTitleGov: 'Algorithmic Governance & Ethical AI Disclosure / மாதிரி தணிக்கை அறிக்கை',
            footerTitle: 'National Public Grievance Portal • தேசிய பொதுக் குறைதீர்ப்பு தளம்'
        },
        te: {
            topDept: 'పరిపాలనా సంస్కరణలు మరియు ప్రజా ఫిర్యాదుల శాఖ',
            headerSec: 'జాతీయ ప్రజా ఫిర్యాదుల పరిష్కార మరియు పర్యవేక్షణ వ్యవస్థ',
            portalTitle: 'National Public Grievance Portal',
            portalSub: 'Department of Administrative Reforms & Public Grievances (DARPG) • Government of India',
            noticeTag: 'NOTICE / ప్రకటన',
            noticeText: 'పౌర చార్టర్ కాలపరిమితుల ప్రకారం ప్రజా ఫిర్యాదులు పరిష్కరించబడతాయి. అత్యవసర ప్రమాదాలు (పైప్‌లైన్ పగిలిపోవడం, లైవ్ వైర్లు, కలుషిత నీరు) 12-24 గంటల్లో పరిష్కరించబడతాయి. టోల్ ఫ్రీ హెల్ప్‌లైన్ 1913 నిరంతరం అందుబాటులో ఉంది.',
            navLodgeSec: 'ఫిర్యాదు నమోదు',
            navTrackSec: 'స్థితి తెలుసుకోండి',
            navAdminSec: 'నోడల్ అధికారి కన్సోల్',
            navCharterSec: 'పౌర చార్టర్ & గడువులు',
            navGovSec: 'మోడల్ ఆడిట్',
            pageTitleLodge: 'Lodge a Public Grievance / పౌర ఫిర్యాదు నమోదు',
            formGroTitle: 'Citizen Grievance Submission Form / ఫిర్యాదు సమర్పణ ఫారమ్',
            sampleLabel: 'ప్రామాణిక మున్సిపల్ ఫిర్యాదులు (పరిశీలన కోసం ఎంచుకోండి):',
            partA: 'Part A: Complainant Details (Optional / ఫిర్యాదుదారు వివరాలు)',
            citizenName: 'Citizen Name / పౌరుడి పేరు',
            citizenContact: 'Mobile Number for SMS Tracking / మొబైల్ నంబర్',
            partB: 'Part B: Administrative Jurisdiction & Incident Location (పరిపాలనా విభాగం)',
            areaSelect: 'Municipal Division / మున్సిపల్ పరిపాలనా విభాగం',
            landmark: 'Specific Landmark / సమీప ల్యాండ్‌మార్క్',
            partC: 'Part C: Detailed Grievance Description (సమగ్ర ఫిర్యాదు వివరాలు)',
            descLabel: 'Full Description of Public Grievance / ప్రజా ఫిర్యాదు పూర్తి వివరణ',
            voiceStatus: 'Speak Complaint / మాట్లాడి నమోదు చేయండి',
            submitBtn: 'Submit Grievance for Redressal / ఫిర్యాదును సమర్పించండి',
            docketTitle: 'Official Grievance Docket / అధికారిక రసీదు',
            pageTitleTrack: 'Track Grievance Status / ఫిర్యాదు పరిష్కార స్థితి',
            trackInputLabel: 'Grievance Docket Number / ఫిర్యాదు సంఖ్య:',
            trackBtnText: 'Track Grievance / శోధించండి',
            pageTitleNodal: 'Nodal Officer Operations Console / నోడల్ అధికారి కార్యనిర్వాహక విభాగం',
            pageTitleCharter: 'Citizen Charter & Statutory Resolution Timelines / పౌర చార్టర్ & గడువులు',
            pageTitleGov: 'Algorithmic Governance & Ethical AI Disclosure / మోడల్ ఆడిట్ నివేదిక',
            footerTitle: 'National Public Grievance Portal • జాతీయ ప్రజా ఫిర్యాదుల పోర్టల్'
        },
        en: {
            topDept: 'Directorate of Administrative Reforms & Public Grievances',
            headerSec: 'National Public Grievance Redressal System',
            portalTitle: 'National Public Grievance Portal',
            portalSub: 'Department of Administrative Reforms & Public Grievances (DARPG) • Government of India',
            noticeTag: 'NOTICE',
            noticeText: 'Citizen Grievances are prioritized strictly as per DARPG Citizen Charter Timelines. Emergency hazards (Water burst, Live wires, Contamination) are triaged within 12-24 hours. Multilingual submission supported. Toll-free helpline 1913 operational 24x7.',
            navLodgeSec: '',
            navTrackSec: '',
            navAdminSec: '',
            navCharterSec: '',
            navGovSec: '',
            pageTitleLodge: 'Lodge a Public Grievance',
            formGroTitle: 'Citizen Grievance Submission Form',
            sampleLabel: 'Standard Municipal Case Templates (Select for verification):',
            partA: 'Part A: Complainant Details (Optional)',
            citizenName: 'Citizen Name',
            citizenContact: 'Mobile Number for SMS Tracking',
            partB: 'Part B: Administrative Jurisdiction & Incident Location',
            areaSelect: 'Municipal Division',
            landmark: 'Specific Landmark',
            partC: 'Part C: Detailed Grievance Description',
            descLabel: 'Full Description of Public Grievance',
            voiceStatus: 'Speak Complaint',
            submitBtn: 'Submit Grievance for Redressal',
            docketTitle: 'Official Grievance Docket',
            pageTitleTrack: 'Track Grievance Status',
            trackInputLabel: 'Grievance Docket Number:',
            trackBtnText: 'Track Grievance',
            pageTitleNodal: 'Nodal Officer Operations Console',
            pageTitleCharter: 'Citizen Charter & Statutory Resolution Timelines',
            pageTitleGov: 'Algorithmic Governance & Ethical AI Disclosure',
            footerTitle: 'National Public Grievance Portal'
        }
    };

    let currentLang = localStorage.getItem('gov-portal-lang') || 'hi';

    function applyLanguage(lang) {
        if (!I18N[lang]) lang = 'hi';
        currentLang = lang;
        const dict = I18N[lang];

        const langSelect = document.getElementById('portal-lang-select');
        if (langSelect && langSelect.value !== lang) {
            langSelect.value = lang;
        }

        const elMap = {
            'top-dept-title': dict.topDept,
            'header-secondary-title': dict.headerSec,
            'header-portal-title': dict.portalTitle,
            'header-portal-sub': dict.portalSub,
            'notice-tag': dict.noticeTag,
            'notice-text': dict.noticeText,
            'nav-lbl-lodge-sec': dict.navLodgeSec,
            'nav-lbl-lodge-en': '',       // BUG FIX: hide English sub-label in non-English modes
            'nav-lbl-track-sec': dict.navTrackSec,
            'nav-lbl-track-en': '',
            'nav-lbl-admin-sec': dict.navAdminSec,
            'nav-lbl-admin-en': '',
            'nav-lbl-charter-sec': dict.navCharterSec,
            'nav-lbl-charter-en': '',
            'nav-lbl-gov-sec': dict.navGovSec,
            'nav-lbl-gov-en': '',
            'page-title-lodge': dict.pageTitleLodge,
            'form-gro-title': dict.formGroTitle,
            'sample-box-label': dict.sampleLabel,
            'legend-part-a': dict.partA,
            'lbl-citizen-name': dict.citizenName,
            'lbl-citizen-contact': dict.citizenContact,
            'legend-part-b': dict.partB,
            'lbl-area-select': dict.areaSelect,
            'lbl-landmark': dict.landmark,
            'legend-part-c': dict.partC,
            'lbl-desc': dict.descLabel,
            'voice-status': dict.voiceStatus,
            'btn-text': dict.submitBtn,
            'docket-panel-title': dict.docketTitle,
            'page-title-track': dict.pageTitleTrack,
            'lbl-track-input': dict.trackInputLabel,
            'track-btn-text': dict.trackBtnText,
            'page-title-nodal': dict.pageTitleNodal,
            'page-title-charter': dict.pageTitleCharter,
            'page-title-gov': dict.pageTitleGov,
            'footer-portal-title': dict.footerTitle
        };

        Object.entries(elMap).forEach(([id, text]) => {
            const el = document.getElementById(id);
            if (el) {
                if (text === '') {
                    el.style.display = 'none';
                } else {
                    el.style.display = '';
                    el.textContent = text;
                }
            }
        });

        localStorage.setItem('gov-portal-lang', lang);
    }

    const langSelect = document.getElementById('portal-lang-select');
    if (langSelect) {
        langSelect.value = currentLang;
        langSelect.addEventListener('change', (e) => {
            const chosen = e.target.value;
            applyLanguage(chosen);
            const langLabels = { hi: 'हिन्दी (Hindi)', ta: 'தமிழ் (Tamil)', te: 'తెలుగు (Telugu)', en: 'English' };
            toast(`Language set to ${langLabels[chosen] || chosen}.`, 'info');
        });
    }
    applyLanguage(currentLang);

    /* ── System Status & AI Engine Probe ─────────────────────── */
    async function probeSystemStatus() {
        const titleEl = document.getElementById('status-title');
        const detailEl = document.getElementById('status-detail');
        const dotEl = document.getElementById('status-dot');
        if (!titleEl || !detailEl) return;

        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            const isMicro = data.ai_inference_mode === 'microservice';

            if (dotEl) {
                dotEl.className = 'status-indicator-dot ' + (isMicro ? 'mode-microservice' : 'mode-subprocess');
            }
            titleEl.textContent = 'System Status: Operational';
            detailEl.textContent = isMicro
                ? 'AI Engine: Persistent Microservice (FastAPI ⚡)'
                : 'AI Engine: Subprocess Pipeline (Zero-Downtime Fallback)';
        } catch {
            if (dotEl) dotEl.className = 'status-indicator-dot mode-subprocess';
            titleEl.textContent = 'System Status: Degradation Check';
            detailEl.textContent = 'AI Engine: Local Service Unreachable';
        }
    }
    probeSystemStatus();
    setInterval(probeSystemStatus, 30_000);

    /* ── Navigation Tab Switching ────────────────────────────── */
    const navLinks = document.querySelectorAll('.nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const targetId = link.dataset.tab;
            navLinks.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                pane.classList.add('hidden');
            });

            link.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.remove('hidden');
                targetPane.classList.add('active');
            }

            if (targetId === 'admin-tab') loadAdmin();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    /* ── Character Counter ───────────────────────────────────── */
    const textarea = document.getElementById('grievance-text');
    const charCount = document.getElementById('char-count');
    if (textarea && charCount) {
        textarea.addEventListener('input', () => {
            charCount.textContent = textarea.value.length;
        });
    }

    /* ── Municipal Case Sample Inputs ────────────────────────── */
    document.querySelectorAll('.sample-pill-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!textarea) return;
            textarea.value = btn.dataset.text;
            if (charCount) charCount.textContent = textarea.value.length;
            textarea.focus();
            toast('Municipal case study loaded into complaint text.', 'info');
        });
    });

    /* ── Web Speech API (Voice Input Assist) ──────────────────── */
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
        recognition.lang = 'en-IN';

        recognition.onstart = () => {
            isListening = true;
            voiceBtn.classList.add('listening');
            if (voiceStatus) voiceStatus.textContent = 'Listening... बोलिए';
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
            toast(`Voice recognition notice: ${e.error}`, 'error');
            stopListening();
        };

        recognition.onend = stopListening;

        function stopListening() {
            isListening = false;
            if (voiceBtn) voiceBtn.classList.remove('listening');
            if (voiceStatus) voiceStatus.textContent = 'Speak Complaint / बोलकर लिखें';
            if (voiceIcon) voiceIcon.textContent = '🎤';
        }

        voiceBtn.addEventListener('click', () => {
            if (isListening) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch {
                    toast('Speech recognition initialization failed.', 'error');
                }
            }
        });
    } else if (voiceBtn) {
        voiceBtn.title = 'Web Speech API is not supported in this browser.';
        voiceBtn.style.opacity = '0.6';
    }

    /* ── Grievance Submission Flow (POST /api/process-grievance) ── */
    const form = document.getElementById('grievance-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const resetBtn = document.getElementById('reset-btn');

    // BUG FIX: Reset button must also reset char counter and clear the docket panel
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (charCount) charCount.textContent = '0';
            // Clear docket result back to empty state
            const emptyState = document.getElementById('ai-empty-state');
            const resultContent = document.getElementById('ai-result-content');
            if (emptyState) emptyState.classList.remove('hidden');
            if (resultContent) resultContent.classList.add('hidden');
            toast('Form cleared. You may submit a new petition.', 'info');
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const text = textarea ? textarea.value.trim() : '';
            const area = document.getElementById('area-select')?.value || 'Anna Nagar';
            const landmark = document.getElementById('landmark-input')?.value.trim() || '';
            const citizenName = document.getElementById('citizen-name')?.value.trim() || 'Citizen (Anonymous)';
            const declaration = document.getElementById('statutory-declaration');

            if (declaration && !declaration.checked) {
                toast('Statutory declaration affirmation is required to lodge a formal petition.', 'error');
                return;
            }

            if (!text || text.length < 10) {
                toast('Grievance description must contain at least 10 characters.', 'error');
                if (textarea) textarea.focus();
                return;
            }

            // Lock UI & indicate processing
            submitBtn.disabled = true;
            if (btnText) btnText.textContent = 'Auditing & Triaging Petition...';
            if (btnLoader) btnLoader.classList.remove('hidden');

            try {
                // BUG FIX: Include landmark in submission payload
                const areaFull = landmark ? `${area} — near ${landmark}` : area;
                const res = await fetch('/api/process-grievance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, area: areaFull })
                });

                const data = await res.json();

                if (!res.ok || !data.success) {
                    throw new Error(data.error || 'Failed to process petition');
                }

                renderOfficialDocket(data.ticket, data.ai_analysis, citizenName);
                toast(`Grievance ${data.ticket.id} registered and triaged successfully.`, 'success');

            } catch (err) {
                toast(err.message || 'Error communicating with municipal server.', 'error');
            } finally {
                submitBtn.disabled = false;
                if (btnText) btnText.textContent = I18N[currentLang]?.submitBtn || 'Submit Grievance for Redressal / शिकायत प्रस्तुत करें';
                if (btnLoader) btnLoader.classList.add('hidden');
            }
        });
    }

    /* ── Render Official Docket ──────────────────────────────── */
    function renderOfficialDocket(ticket, ai, citizenName) {
        const emptyState = document.getElementById('ai-empty-state');
        const resultContent = document.getElementById('ai-result-content');
        if (emptyState) emptyState.classList.add('hidden');
        if (resultContent) resultContent.classList.remove('hidden');

        // BUG FIX: Update ticket-status-badge in the docket header
        const statusBadgeDocket = document.getElementById('ticket-status-badge');
        if (statusBadgeDocket) {
            statusBadgeDocket.textContent = ticket.status || 'Submitted';
            statusBadgeDocket.className = 'gov-status-badge ' + (
                ticket.status === 'Flagged Duplicate' ? 'status-duplicate' : 'status-submitted'
            );
        }

        // References & Timing
        const ticketIdEl = document.getElementById('ticket-id');
        const timeEl = document.getElementById('docket-timestamp');
        if (ticketIdEl) ticketIdEl.textContent = ticket.id;
        if (timeEl) {
            const dt = ticket.created_at ? new Date(ticket.created_at) : new Date();
            timeEl.textContent = 'Docket Generated: ' + dt.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
        }

        // Language
        const langNames = {
            'en': 'English (Official)',
            'hi': 'हिन्दी / Hindi',
            'ta': 'தமிழ் / Tamil',
            'te': 'తెలుగు / Telugu',
            'en-hi': 'Hinglish (Colloquial)',
            'en-ta': 'Tanglish (Colloquial)'
        };
        const langEl = document.getElementById('res-language');
        const langConfEl = document.getElementById('res-lang-conf');
        if (langEl) langEl.textContent = langNames[ticket.language] || ticket.language;
        if (langConfEl) {
            langConfEl.textContent = ai && ai.language_confidence
                ? `Confidence: ${(ai.language_confidence * 100).toFixed(1)}%`
                : 'Deterministic Script Match';
        }

        // Category
        const catEl = document.getElementById('res-category');
        const catConfEl = document.getElementById('res-cat-conf');
        if (catEl) catEl.textContent = ticket.category;
        if (catConfEl) {
            const conf = ticket.category_confidence || (ai && ai.category_confidence);
            catConfEl.textContent = conf ? `Confidence: ${(conf * 100).toFixed(1)}%` : 'Rule-Calibrated';
        }

        // Priority & SLA
        const prioEl = document.getElementById('res-priority');
        const prioReasonEl = document.getElementById('res-prio-reason');
        const reviewBadge = document.getElementById('res-review-badge');
        if (prioEl) {
            prioEl.textContent = ticket.priority;
            prioEl.className = `gov-priority-tag prio-${(ticket.priority || 'low').toLowerCase()}`;
        }
        if (prioReasonEl) prioReasonEl.textContent = ticket.priority_reason || 'Calibrated municipal risk index';
        if (reviewBadge) {
            reviewBadge.classList.toggle('hidden', !ticket.needs_review);
        }

        // Department & SLA
        const deptEl = document.getElementById('res-department');
        const slaEl = document.getElementById('res-sla');
        if (deptEl) deptEl.textContent = ticket.department || 'Municipal Administration';
        if (slaEl) slaEl.textContent = `SLA Target: ${ticket.sla_hours || 48} Hours`;

        // Duplicate Notice
        const dupAlert = document.getElementById('duplicate-alert');
        const dupDetails = document.getElementById('dup-details');
        if (dupAlert) {
            if (ticket.duplicate_matched) {
                dupAlert.classList.remove('hidden');
                if (dupDetails) {
                    dupDetails.textContent = `Matches existing registered complaint in this ward (${ticket.matched_complaint || 'Ward Index'}). Vector similarity: ${(ticket.similarity_score * 100).toFixed(0)}%. Linked under common civic incident file.`;
                }
            } else {
                dupAlert.classList.add('hidden');
            }
        }

        // Explanation & Diagnostic Keywords
        const explEl = document.getElementById('res-explanation-summary');
        if (explEl) {
            explEl.textContent = ticket.explanation ||
                `Petition routed to ${ticket.department} with ${ticket.priority} priority based on public safety risk factors and municipal jurisdictional norms.`;
        }

        const termsContainer = document.getElementById('key-terms-tags');
        if (termsContainer) {
            termsContainer.innerHTML = '';
            const terms = ticket.key_terms || [];
            if (terms.length > 0) {
                terms.forEach(t => {
                    const span = document.createElement('span');
                    span.className = 'term-chip';
                    span.textContent = t;
                    termsContainer.appendChild(span);
                });
            } else {
                termsContainer.innerHTML = '<span class="text-subtle">Domain vocabulary matched</span>';
            }
        }

        // Wire Action Toolbar
        const printBtn = document.getElementById('print-docket-btn');
        if (printBtn) {
            printBtn.onclick = () => window.print();
        }

        const copyBtn = document.getElementById('copy-docket-id-btn');
        if (copyBtn) {
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(ticket.id).then(() => {
                    toast(`Registration Number ${ticket.id} copied to clipboard.`, 'success');
                }).catch(() => {
                    toast(ticket.id, 'info');
                });
            };
        }

        const trackThisBtn = document.getElementById('track-this-btn');
        if (trackThisBtn) {
            trackThisBtn.onclick = () => {
                const trackTabBtn = document.getElementById('tab-btn-track');
                const trackInput = document.getElementById('track-input');
                if (trackTabBtn) trackTabBtn.click();
                if (trackInput) {
                    trackInput.value = ticket.id;
                    setTimeout(executeTrackGrievance, 100);
                }
            };
        }
    }

    /* ── Tracking Flow (GET /api/grievances/:id) ───────────────── */
    const trackBtn = document.getElementById('track-btn');
    const trackInput = document.getElementById('track-input');

    if (trackBtn) trackBtn.addEventListener('click', executeTrackGrievance);
    if (trackInput) {
        trackInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') executeTrackGrievance();
        });
    }

    async function executeTrackGrievance() {
        const id = (trackInput ? trackInput.value : '').trim().toUpperCase();
        if (!id) {
            toast('Please enter a valid Registration Docket Number (e.g. GRV-2026-1001).', 'error');
            return;
        }

        const emptyPanel = document.getElementById('track-empty');
        const resultPanel = document.getElementById('track-result');

        try {
            const res = await fetch(`/api/grievances/${encodeURIComponent(id)}`);
            if (res.status === 404) {
                toast(`No grievance record found with Registration ID "${id}".`, 'error');
                return;
            }
            const data = await res.json();
            const ticket = data.ticket;

            if (emptyPanel) emptyPanel.classList.add('hidden');
            if (resultPanel) resultPanel.classList.remove('hidden');

            renderTrackRecord(ticket);

        } catch {
            toast('Failed to contact municipal server for tracking lookup.', 'error');
        }
    }

    function renderTrackRecord(t) {
        const idEl = document.getElementById('track-id');
        const statusBadge = document.getElementById('track-status-badge');
        if (idEl) idEl.textContent = t.id;
        if (statusBadge) {
            statusBadge.textContent = t.status || 'Submitted';
            statusBadge.className = 'gov-status-badge ' + (
                t.status === 'Resolved' ? 'status-resolved' :
                    t.status === 'In Progress' || t.status === 'Dispatched' ? 'status-inprogress' :
                        t.status === 'Flagged Duplicate' ? 'status-duplicate' : 'status-submitted'
            );
        }

        // Table fields
        document.getElementById('track-category').textContent = t.category || '--';
        const prioEl = document.getElementById('track-priority');
        if (prioEl) {
            prioEl.textContent = t.priority || '--';
            prioEl.className = `gov-priority-tag prio-${(t.priority || 'low').toLowerCase()}`;
        }
        document.getElementById('track-area').textContent = t.area || '--';
        document.getElementById('track-dept').textContent = t.department || '--';
        document.getElementById('track-lang').textContent = t.language || '--';
        document.getElementById('track-sla').textContent = `${t.sla_hours || 48} Hours`;
        document.getElementById('track-date').textContent = t.created_at ? new Date(t.created_at).toLocaleString('en-IN') : '--';
        document.getElementById('track-text').textContent = t.text || '--';

        // SLA Compliance Status
        const ageHours = t.created_at ? (Date.now() - new Date(t.created_at).getTime()) / 3_600_000 : 0;
        const isBreached = t.sla_hours && ageHours > t.sla_hours && t.status !== 'Resolved';
        const slaStatusEl = document.getElementById('track-sla-status');
        if (slaStatusEl) {
            slaStatusEl.innerHTML = isBreached
                ? `<span class="badge-breached">SLA Overdue (${Math.round(ageHours)}h elapsed / Target ${t.sla_hours}h)</span>`
                : `<span class="badge-compliant">Within SLA Timelines (${Math.round(ageHours)}h elapsed)</span>`;
        }

        // Stepper state
        const steps = ['submitted', 'review', 'progress', 'dispatched', 'resolved'];
        const statusOrder = {
            'Submitted': 1,
            'Under Review': 2,
            'In Progress': 3,
            'Dispatched': 4,
            'Resolved': 5,
            'Flagged Duplicate': 2
        };
        const currentStep = statusOrder[t.status] || 1;

        // BUG FIX: HTML has tl-line-1 through tl-line-4 (1-indexed connectors between steps)
        // JS was looking for tl-line-0 which doesn't exist. Connectors sit BETWEEN steps,
        // so connector after step[idx] = tl-line-{idx+1}
        steps.forEach((s, idx) => {
            const stepEl = document.getElementById(`tl-${s}`);
            const lineEl = document.getElementById(`tl-line-${idx + 1}`); // FIXED: was idx, now idx+1
            if (stepEl) {
                stepEl.classList.remove('step-done', 'step-current');
                if (idx + 1 < currentStep) stepEl.classList.add('step-done');
                else if (idx + 1 === currentStep) stepEl.classList.add('step-current');
            }
            if (lineEl) {
                lineEl.classList.toggle('line-done', idx + 1 < currentStep);
            }
        });

        // BUG FIX: Clear static ATR placeholder text when real ticket data is shown
        const atrEl = document.getElementById('track-atr-content');
        if (atrEl) {
            atrEl.textContent = t.status === 'Resolved'
                ? 'Grievance has been resolved and case closed by the competent authority.'
                : t.status === 'Dispatched' || t.status === 'In Progress'
                    ? 'Field inspection team deployed. Work order issued to zonal maintenance crew.'
                    : 'Petition received and under administrative review. ATR will be filed upon dispatch.';
        }
    }

    /* ── Nodal Officer Console (Operations) ───────────────────── */
    let prioChart = null;
    let langChart = null;
    let catChart = null;
    let trendChart = null;

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

            // Populate KPIs
            document.getElementById('stat-total').textContent = analytics.total_complaints ?? 0;
            document.getElementById('stat-critical').textContent = analytics.priority_breakdown?.Critical ?? 0;
            document.getElementById('stat-high').textContent = analytics.priority_breakdown?.High ?? 0;
            document.getElementById('stat-duplicates').textContent = analytics.duplicate_count ?? 0;
            document.getElementById('stat-sla-breach').textContent = analytics.sla_breached_count ?? 0;
            document.getElementById('stat-review').textContent = analytics.needs_review_count ?? 0;

            // Review banner
            const banner = document.getElementById('review-queue-banner');
            const reviewCount = document.getElementById('review-queue-count');
            if (analytics.needs_review_count > 0) {
                if (banner) banner.classList.remove('hidden');
                if (reviewCount) reviewCount.textContent = analytics.needs_review_count;
            } else if (banner) {
                banner.classList.add('hidden');
            }

            buildGovCharts(analytics);

            currentGrievances = gData.grievances || [];
            currentPage = 1;
            renderPaginatedTable();

        } catch {
            toast('Failed to retrieve executive operations dataset.', 'error');
        }
    }

    function buildGovCharts(a) {
        const pb = a.priority_breakdown || {};
        const lb = a.language_breakdown || {};
        const cb = a.category_breakdown || {};
        const trend = a.daily_trend || {};

        // 1. Priority Distribution (Clean Gov doughnut)
        if (prioChart) prioChart.destroy();
        const pCanvas = document.getElementById('priority-chart');
        if (pCanvas) {
            prioChart = new Chart(pCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [pb.Critical || 0, pb.High || 0, pb.Medium || 0, pb.Low || 0],
                        backgroundColor: ['#b91c1c', '#c25e00', '#15803d', '#334155'],
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    cutout: '60%',
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }
                    },
                    maintainAspectRatio: false
                }
            });
        }

        // 2. Multi-Script Language Distribution
        if (langChart) langChart.destroy();
        const lCanvas = document.getElementById('lang-chart');
        if (lCanvas) {
            langChart = new Chart(lCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['English', 'Hindi', 'Tamil', 'Hinglish', 'Tanglish'],
                    datasets: [{
                        data: [lb.en || 0, lb.hi || 0, lb.ta || 0, lb['en-hi'] || 0, lb['en-ta'] || 0],
                        backgroundColor: ['#0b2545', '#ea580c', '#0284c7', '#ca8a04', '#16a34a'],
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    cutout: '60%',
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }
                    },
                    maintainAspectRatio: false
                }
            });
        }

        // 3. Category Horizontal Bar Chart
        if (catChart) catChart.destroy();
        const cCanvas = document.getElementById('category-chart');
        if (cCanvas) {
            const catLabels = Object.keys(cb);
            const catData = catLabels.map(k => cb[k]);
            catChart = new Chart(cCanvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: catLabels.map(l => l.length > 20 ? l.slice(0, 18) + '…' : l),
                    datasets: [{
                        label: 'Grievance Petitions',
                        data: catData,
                        backgroundColor: '#133e7c',
                        borderRadius: 2
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: '#e2e8f0' }, ticks: { font: { size: 10 } } },
                        y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                    },
                    maintainAspectRatio: false
                }
            });
        }

        // 4. 7-Day Municipal Receipt Trend (Line)
        if (trendChart) trendChart.destroy();
        const tCanvas = document.getElementById('trend-chart');
        if (tCanvas) {
            const trendLabels = Object.keys(trend).map(d => {
                const dt = new Date(d + 'T00:00:00');
                return dt.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
            });
            const trendData = Object.values(trend);
            trendChart = new Chart(tCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: trendLabels,
                    datasets: [{
                        label: 'Petitions Lodged',
                        data: trendData,
                        borderColor: '#0b2545',
                        backgroundColor: 'rgba(11, 37, 69, 0.08)',
                        pointBackgroundColor: '#c25e00',
                        pointRadius: 4,
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true
                    }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: '#e2e8f0' }, ticks: { font: { size: 10 } } },
                        y: { grid: { color: '#e2e8f0' }, ticks: { font: { size: 10 }, precision: 0 } }
                    },
                    maintainAspectRatio: false
                }
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
        if (count) count.textContent = `${total} municipal record${total !== 1 ? 's' : ''} indexed`;

        if (total === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="table-empty-cell">No grievances match the current administrative filters.</td></tr>';
            if (pagContainer) pagContainer.innerHTML = '';
            return;
        }

        const totalPages = Math.ceil(total / PAGE_SIZE);
        if (currentPage > totalPages) currentPage = totalPages;
        const start = (currentPage - 1) * PAGE_SIZE;
        const pageItems = currentGrievances.slice(start, start + PAGE_SIZE);

        pageItems.forEach(item => {
            const tr = document.createElement('tr');
            const now = Date.now();
            const ageHours = item.created_at ? (now - new Date(item.created_at).getTime()) / 3_600_000 : 0;
            const isBreached = item.sla_hours && ageHours > item.sla_hours && item.status !== 'Resolved';

            if (item.needs_review) tr.classList.add('row-review-flag');
            if (isBreached) tr.classList.add('row-sla-breach');

            const prioClass = `prio-${(item.priority || 'low').toLowerCase()}`;
            const slaFlag = isBreached ? ' <span class="badge-breached" title="SLA Breached">OVERDUE</span>' : '';
            const reviewFlag = item.needs_review ? ' <span class="gov-badge-review" title="Low Model Confidence">VERIFY</span>' : '';

            tr.innerHTML = `
                <td class="ref-mono">${escapeHtml(item.id)}</td>
                <td>${escapeHtml(item.language || '--')}</td>
                <td>${escapeHtml(item.area || '--')}</td>
                <td><span class="text-clip" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</span></td>
                <td>${escapeHtml(item.category || '--')}</td>
                <td>
                    <span class="gov-priority-tag ${prioClass}">${escapeHtml(item.priority)}</span>
                    ${reviewFlag}
                    ${slaFlag}
                </td>
                <td><span class="text-clip" title="${escapeHtml(item.department)}">${escapeHtml(item.department || '--')}</span></td>
                <td>
                    <select class="status-select-sm" data-id="${item.id}">
                        ${['Submitted', 'Under Review', 'In Progress', 'Dispatched', 'Resolved', 'Flagged Duplicate']
                    .map(s => `<option${item.status === s ? ' selected' : ''}>${s}</option>`)
                    .join('')}
                    </select>
                </td>
                <td>
                    <button class="gov-btn-secondary btn-sm save-status-btn" data-id="${item.id}">Save</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Wire Save button handlers
        document.querySelectorAll('.save-status-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const select = btn.closest('tr').querySelector('.status-select-sm');
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
                        toast(`Ticket ${id} status successfully updated to "${select.value}".`, 'success');
                    } else {
                        toast(data.error || `Failed to update status for ${id}.`, 'error');
                    }
                } catch {
                    toast('Network error during status update.', 'error');
                } finally {
                    btn.textContent = 'Save';
                    btn.disabled = false;
                }
            });
        });

        // Render Pagination
        if (pagContainer) {
            pagContainer.innerHTML = '';
            if (totalPages <= 1) return;

            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.textContent = '‹ Prev';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => { currentPage--; renderPaginatedTable(); };
            pagContainer.appendChild(prevBtn);

            for (let p = 1; p <= totalPages; p++) {
                const pBtn = document.createElement('button');
                pBtn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
                pBtn.textContent = p;
                pBtn.onclick = () => { currentPage = p; renderPaginatedTable(); };
                pagContainer.appendChild(pBtn);
            }

            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.textContent = 'Next ›';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => { currentPage++; renderPaginatedTable(); };
            pagContainer.appendChild(nextBtn);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    /* ── Export CSV for Nodal Review ─────────────────────────── */
    function exportCSV() {
        if (!currentGrievances.length) {
            toast('No records available to export.', 'error');
            return;
        }

        const headers = ['Registration_ID', 'Language', 'Municipal_Division', 'Category', 'Priority', 'Assigned_Department', 'SLA_Hours', 'Status', 'Needs_Human_Review', 'Registered_At', 'Description'];
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
        link.setAttribute('download', `National_Grievance_Statutory_Report_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast('Statutory CSV grievance ledger generated and downloaded.', 'success');
    }

    /* ── Queue Filtering ─────────────────────────────────────── */
    ['filter-priority', 'filter-language', 'filter-review', 'filter-search'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('change', applyGovFilters);
        if (id === 'filter-search') el.addEventListener('keyup', applyGovFilters);
    });

    async function applyGovFilters() {
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
