// ============================================================
// Smart Public Transport — Multi-Language Interface
// One dictionary, applied everywhere via [data-i18n] / [data-i18n-placeholder]
// AND the t() helper used in passenger.js for dynamically built HTML.
//
// Add a language by adding a new top-level key below and an <option> in
// the language <select> on each page — no other code changes needed.
// ============================================================

const TRANSLATIONS = {
    en: {
        // Login page
        unified_title: "Sign in to Smart Transit",
        unified_sub: "One login works for every role — Passenger, Driver, Conductor or Admin.",
        field_identifier: "Email or Phone Number",
        field_password: "Password",
        field_name: "Full Name",
        field_email: "Email",
        field_phone: "Phone Number (optional)",
        btn_sign_in: "Sign In",
        btn_create_account: "Create Passenger Account",
        new_passenger_q: "New passenger?",
        link_create_account: "Create an account",
        link_back_to_login: "Back to sign in",
        or_google_divider: "Or continue with Google, by role",
        who_are_you: "Who are you?",
        card_passenger_title: "Passenger / User",
        card_passenger_desc: "Track buses, view routes, stops and estimated arrival times.",
        card_passenger_note: "Browse without an account",
        card_passenger_btn: "Continue as Guest →",
        card_driver_title: "Driver",
        card_driver_desc: "Access assigned bus, route and trip information.",
        card_driver_btn: "Driver Login →",
        card_conductor_title: "Conductor",
        card_conductor_desc: "Manage passenger trips, assigned bus and route information.",
        card_conductor_btn: "Conductor Login →",
        card_admin_title: "Administrator",
        card_admin_desc: "Manage buses, drivers, conductors, routes and system operations.",
        card_admin_btn: "Administrator Login →",

        // Header
        app_name: "Smart Transit",
        header_live: "LIVE",

        // Passenger dashboard — nav & tabs
        nav_find_bus: "Find Bus",
        nav_live_radar: "Live Radar",
        nav_progress: "Progress",
        search_placeholder: "Search buses, routes, or stops...",
        filter_all: "All",
        filter_live: "Live Only",

        // Trip planner
        plan_trip_title: "Plan Your Trip",
        plan_trip_sub: "Enter where you're starting from and where you're going — we'll show the route and any live buses on it.",
        field_source: "Source",
        field_destination: "Destination",
        source_placeholder: "e.g. Vijayawada",
        destination_placeholder: "e.g. Tirupathi",
        btn_find_route: "Show Route & Live Buses",
        swap_locations: "Swap",
        trip_no_results: "No routes found between these two places yet.",
        trip_searching: "Searching routes…",
        view_on_map: "View on Map",
        live_buses_count: "live bus(es) found",
        boarding_at: "Board at",
        alight_at: "Alight at",

        // Bus cards (dynamic)
        no_buses_found: "No buses found matching your search",
        live_gps: "LIVE GPS",
        gps_simulated: "GPS Simulated",
        on_time: "ON TIME",
        delayed: "DELAYED",
        driver_label: "Driver",
        view_live_gps_map: "View Live GPS Map",
        stop_timeline: "Stop Timeline",
        standard: "Standard",
        unknown_route: "Unknown Route",

        // Progress tab
        no_bus_selected_title: "No Bus Selected",
        no_bus_selected_desc: "Select a bus from \"Find Bus\" or \"Live Radar\" to see stop-by-stop progress",
        approaching_next_stop: "Approaching Next Stop",
        live_eta: "Live ETA",
        distance_label: "Distance",
        status_label: "Status",
        stop_by_stop_progress: "Stop-by-Stop Progress",
        sync_btn: "Sync",
        verified: "Verified",
        min_behind: "min behind",
        running_on_schedule: "Running on schedule",
        to_next_stop: "to next stop",
        km_total: "km total",

        // Timeline
        no_stops_data: "No stops data available",
        passed: "Passed",
        live_position: "Live Position",
        from_word: "from",
        eta_label: "ETA",
        next_stop: "Next Stop",
        final_destination: "Final Destination",
        terminus: "Terminus",
        away: "away",
        stop_word: "Stop",

        // Map popups
        live_gps_stream: "LIVE GPS STREAM",
        loading: "Loading...",

        // Complaints
        report_issue_title: "Report an Issue",
        select_category: "Select category...",
        describe_issue: "Describe the issue...",
        submit_report: "Submit Report",
        complaint_fill: "Please fill in category and description.",
        complaint_success: "✓ Report submitted successfully!",
        complaint_error: "Error submitting report. Try again.",

        // Misc
        logout: "Logout",
    },
    hi: {
        // Login page
        unified_title: "स्मार्ट ट्रांज़िट में साइन इन करें",
        unified_sub: "एक ही लॉगिन सभी भूमिकाओं के लिए काम करता है — यात्री, ड्राइवर, कंडक्टर या एडमिन।",
        field_identifier: "ईमेल या फ़ोन नंबर",
        field_password: "पासवर्ड",
        field_name: "पूरा नाम",
        field_email: "ईमेल",
        field_phone: "फ़ोन नंबर (वैकल्पिक)",
        btn_sign_in: "साइन इन करें",
        btn_create_account: "यात्री खाता बनाएं",
        new_passenger_q: "नए यात्री हैं?",
        link_create_account: "खाता बनाएं",
        link_back_to_login: "साइन इन पर वापस जाएं",
        or_google_divider: "या भूमिका के अनुसार Google से जारी रखें",
        who_are_you: "आप कौन हैं?",
        card_passenger_title: "यात्री / उपयोगकर्ता",
        card_passenger_desc: "बसों को ट्रैक करें, मार्ग, स्टॉप और अनुमानित आगमन समय देखें।",
        card_passenger_note: "बिना खाते के देखें",
        card_passenger_btn: "अतिथि के रूप में जारी रखें →",
        card_driver_title: "ड्राइवर",
        card_driver_desc: "आवंटित बस, मार्ग और यात्रा की जानकारी प्राप्त करें।",
        card_driver_btn: "ड्राइवर लॉगिन →",
        card_conductor_title: "कंडक्टर",
        card_conductor_desc: "यात्री यात्राएं, आवंटित बस और मार्ग जानकारी प्रबंधित करें।",
        card_conductor_btn: "कंडक्टर लॉगिन →",
        card_admin_title: "प्रशासक",
        card_admin_desc: "बसें, ड्राइवर, कंडक्टर, मार्ग और सिस्टम संचालन प्रबंधित करें।",
        card_admin_btn: "प्रशासक लॉगिन →",

        // Header
        app_name: "स्मार्ट ट्रांज़िट",
        header_live: "लाइव",

        // Nav & tabs
        nav_find_bus: "बस खोजें",
        nav_live_radar: "लाइव रडार",
        nav_progress: "प्रगति",
        search_placeholder: "बस, मार्ग या स्टॉप खोजें...",
        filter_all: "सभी",
        filter_live: "केवल लाइव",

        // Trip planner
        plan_trip_title: "अपनी यात्रा की योजना बनाएं",
        plan_trip_sub: "बताएं कि आप कहाँ से शुरू कर रहे हैं और कहाँ जा रहे हैं — हम मार्ग और उस पर मौजूद लाइव बसें दिखाएंगे।",
        field_source: "प्रस्थान स्थान",
        field_destination: "गंतव्य",
        source_placeholder: "जैसे विजयवाड़ा",
        destination_placeholder: "जैसे तिरुपति",
        btn_find_route: "मार्ग और लाइव बसें दिखाएं",
        swap_locations: "बदलें",
        trip_no_results: "इन दोनों स्थानों के बीच अभी तक कोई मार्ग नहीं मिला।",
        trip_searching: "मार्ग खोजे जा रहे हैं…",
        view_on_map: "मानचित्र पर देखें",
        live_buses_count: "लाइव बस(एं) मिलीं",
        boarding_at: "यहाँ चढ़ें",
        alight_at: "यहाँ उतरें",

        // Bus cards
        no_buses_found: "आपकी खोज से मेल खाने वाली कोई बस नहीं मिली",
        live_gps: "लाइव GPS",
        gps_simulated: "GPS अनुकरण",
        on_time: "समय पर",
        delayed: "विलंबित",
        driver_label: "ड्राइवर",
        view_live_gps_map: "लाइव GPS मानचित्र देखें",
        stop_timeline: "स्टॉप टाइमलाइन",
        standard: "सामान्य",
        unknown_route: "अज्ञात मार्ग",

        // Progress
        no_bus_selected_title: "कोई बस चयनित नहीं",
        no_bus_selected_desc: "स्टॉप-दर-स्टॉप प्रगति देखने के लिए \"बस खोजें\" या \"लाइव रडार\" से एक बस चुनें",
        approaching_next_stop: "अगला स्टॉप आ रहा है",
        live_eta: "लाइव ईटीए",
        distance_label: "दूरी",
        status_label: "स्थिति",
        stop_by_stop_progress: "स्टॉप-दर-स्टॉप प्रगति",
        sync_btn: "सिंक करें",
        verified: "सत्यापित",
        min_behind: "मिनट पीछे",
        running_on_schedule: "समय पर चल रही है",
        to_next_stop: "अगले स्टॉप तक",
        km_total: "किमी कुल",

        // Timeline
        no_stops_data: "स्टॉप डेटा उपलब्ध नहीं है",
        passed: "गुज़र चुका",
        live_position: "लाइव स्थिति",
        from_word: "से",
        eta_label: "ईटीए",
        next_stop: "अगला स्टॉप",
        final_destination: "अंतिम गंतव्य",
        terminus: "टर्मिनस",
        away: "दूर",
        stop_word: "स्टॉप",

        // Map
        live_gps_stream: "लाइव GPS स्ट्रीम",
        loading: "लोड हो रहा है...",

        // Complaints
        report_issue_title: "समस्या दर्ज करें",
        select_category: "श्रेणी चुनें...",
        describe_issue: "समस्या का वर्णन करें...",
        submit_report: "रिपोर्ट सबमिट करें",
        complaint_fill: "कृपया श्रेणी और विवरण भरें।",
        complaint_success: "✓ रिपोर्ट सफलतापूर्वक सबमिट हो गई!",
        complaint_error: "रिपोर्ट सबमिट करने में त्रुटि। पुनः प्रयास करें।",

        logout: "लॉगआउट",
    },
    te: {
        // Login page
        unified_title: "స్మార్ట్ ట్రాన్సిట్‌లోకి సైన్ ఇన్ చేయండి",
        unified_sub: "ఒకే లాగిన్ ప్రయాణికుడు, డ్రైవర్, కండక్టర్ లేదా అడ్మిన్ — అన్ని పాత్రలకూ పనిచేస్తుంది.",
        field_identifier: "ఇమెయిల్ లేదా ఫోన్ నంబర్",
        field_password: "పాస్‌వర్డ్",
        field_name: "పూర్తి పేరు",
        field_email: "ఇమెయిల్",
        field_phone: "ఫోన్ నంబర్ (ఐచ్ఛికం)",
        btn_sign_in: "సైన్ ఇన్ చేయండి",
        btn_create_account: "ప్రయాణికుల ఖాతా సృష్టించండి",
        new_passenger_q: "కొత్త ప్రయాణికులా?",
        link_create_account: "ఖాతా సృష్టించండి",
        link_back_to_login: "సైన్ ఇన్‌కు తిరిగి వెళ్ళండి",
        or_google_divider: "లేదా పాత్ర ప్రకారం Google తో కొనసాగించండి",
        who_are_you: "మీరు ఎవరు?",
        card_passenger_title: "ప్రయాణికుడు / వినియోగదారు",
        card_passenger_desc: "బస్సులను ట్రాక్ చేయండి, మార్గాలు, స్టాప్‌లు మరియు అంచనా రాక సమయాలను చూడండి.",
        card_passenger_note: "ఖాతా లేకుండా చూడండి",
        card_passenger_btn: "అతిథిగా కొనసాగించండి →",
        card_driver_title: "డ్రైవర్",
        card_driver_desc: "కేటాయించిన బస్సు, మార్గం మరియు ట్రిప్ సమాచారాన్ని పొందండి.",
        card_driver_btn: "డ్రైవర్ లాగిన్ →",
        card_conductor_title: "కండక్టర్",
        card_conductor_desc: "ప్రయాణికుల ట్రిప్‌లు, కేటాయించిన బస్సు మరియు మార్గ సమాచారాన్ని నిర్వహించండి.",
        card_conductor_btn: "కండక్టర్ లాగిన్ →",
        card_admin_title: "అడ్మినిస్ట్రేటర్",
        card_admin_desc: "బస్సులు, డ్రైవర్లు, కండక్టర్లు, మార్గాలు మరియు సిస్టమ్ కార్యకలాపాలను నిర్వహించండి.",
        card_admin_btn: "అడ్మిన్ లాగిన్ →",

        // Header
        app_name: "స్మార్ట్ ట్రాన్సిట్",
        header_live: "లైవ్",

        // Nav & tabs
        nav_find_bus: "బస్సు వెతకండి",
        nav_live_radar: "లైవ్ రాడార్",
        nav_progress: "పురోగతి",
        search_placeholder: "బస్సులు, మార్గాలు లేదా స్టాప్‌లను వెతకండి...",
        filter_all: "అన్నీ",
        filter_live: "లైవ్ మాత్రమే",

        // Trip planner
        plan_trip_title: "మీ ప్రయాణాన్ని ప్లాన్ చేయండి",
        plan_trip_sub: "మీరు ఎక్కడ నుండి బయలుదేరుతున్నారో, ఎక్కడికి వెళ్తున్నారో నమోదు చేయండి — మేము మార్గాన్ని మరియు దానిపై ఉన్న లైవ్ బస్సులను చూపిస్తాము.",
        field_source: "ప్రారంభ స్థలం",
        field_destination: "గమ్యస్థానం",
        source_placeholder: "ఉదా. విజయవాడ",
        destination_placeholder: "ఉదా. తిరుపతి",
        btn_find_route: "మార్గం & లైవ్ బస్సులు చూపించు",
        swap_locations: "మార్చు",
        trip_no_results: "ఈ రెండు ప్రదేశాల మధ్య ఇంకా మార్గాలు కనుగొనబడలేదు.",
        trip_searching: "మార్గాలను వెతుకుతోంది…",
        view_on_map: "మ్యాప్‌లో చూడండి",
        live_buses_count: "లైవ్ బస్సు(లు) కనుగొనబడ్డాయి",
        boarding_at: "ఇక్కడ ఎక్కండి",
        alight_at: "ఇక్కడ దిగండి",

        // Bus cards
        no_buses_found: "మీ శోధనకు సరిపోలే బస్సులు కనుగొనబడలేదు",
        live_gps: "లైవ్ GPS",
        gps_simulated: "GPS అనుకరణ",
        on_time: "సమయానికి",
        delayed: "ఆలస్యం",
        driver_label: "డ్రైవర్",
        view_live_gps_map: "లైవ్ GPS మ్యాప్ చూడండి",
        stop_timeline: "స్టాప్ టైమ్‌లైన్",
        standard: "ప్రామాణికం",
        unknown_route: "తెలియని మార్గం",

        // Progress
        no_bus_selected_title: "బస్సు ఎంపిక చేయలేదు",
        no_bus_selected_desc: "స్టాప్-బై-స్టాప్ పురోగతిని చూడటానికి \"బస్సు వెతకండి\" లేదా \"లైవ్ రాడార్\" నుండి ఒక బస్సును ఎంచుకోండి",
        approaching_next_stop: "తదుపరి స్టాప్ సమీపిస్తోంది",
        live_eta: "లైవ్ ఈటీఏ",
        distance_label: "దూరం",
        status_label: "స్థితి",
        stop_by_stop_progress: "స్టాప్-బై-స్టాప్ పురోగతి",
        sync_btn: "సింక్ చేయి",
        verified: "ధ్రువీకరించబడింది",
        min_behind: "నిమిషాలు ఆలస్యం",
        running_on_schedule: "సమయానికి నడుస్తోంది",
        to_next_stop: "తదుపరి స్టాప్ వరకు",
        km_total: "కిమీ మొత్తం",

        // Timeline
        no_stops_data: "స్టాప్‌ల డేటా అందుబాటులో లేదు",
        passed: "దాటింది",
        live_position: "లైవ్ స్థానం",
        from_word: "నుండి",
        eta_label: "ఈటీఏ",
        next_stop: "తదుపరి స్టాప్",
        final_destination: "అంతిమ గమ్యస్థానం",
        terminus: "టెర్మినస్",
        away: "దూరంలో",
        stop_word: "స్టాప్",

        // Map
        live_gps_stream: "లైవ్ GPS స్ట్రీమ్",
        loading: "లోడ్ అవుతోంది...",

        // Complaints
        report_issue_title: "సమస్యను నివేదించండి",
        select_category: "వర్గాన్ని ఎంచుకోండి...",
        describe_issue: "సమస్యను వివరించండి...",
        submit_report: "నివేదికను సమర్పించండి",
        complaint_fill: "దయచేసి వర్గం మరియు వివరణను నమోదు చేయండి.",
        complaint_success: "✓ నివేదిక విజయవంతంగా సమర్పించబడింది!",
        complaint_error: "నివేదికను సమర్పించడంలో లోపం. మళ్ళీ ప్రయత్నించండి.",

        logout: "లాగ్ అవుట్",
    },
};

const PLACE_TRANSLATIONS = {
    'VIJAYAWADA': { hi: 'विजयवाड़ा', te: 'విజయవాడ' },
    'AMALAPURAM': { hi: 'अमलापुरम', te: 'అమలాపురం' },
    'HYDERABAD': { hi: 'हैदराबाद', te: 'హైదరాబాద్' },
    'TIRUPATHI': { hi: 'तिरुपति', te: 'తిరుపతి' },
    'NELLORE': { hi: 'नेल्लोर', te: 'నెల్లూరు' },
    'VSP MADDILAPALEM': { hi: 'विशाखापत्तनम मद्दिलापलेम', te: 'విశాఖపట్నం మద్దిలపాలెం' },
    'VSP MADDILAPALEM CITY BUS STATION': { hi: 'विशाखापत्तनम मद्दिलापलेम सिटी बस स्टेशन', te: 'విశాఖపట్నం మద్దిలపాలెం సిటీ బస్ స్టేషన్' },
    'CITY BUS STATION': { hi: 'सिटी बस स्टेशन', te: 'సిటీ బస్ స్టేషన్' },
    'MEHDIPATNAM DEPOT': { hi: 'मेहदीपट्टनम डिपो', te: 'మెహదీపట్నం డిపో' },
    'AUTONAGAR BUS STATION': { hi: 'ऑटोनगर बस स्टेशन', te: 'ఆటోనగర్ బస్ స్టేషన్' },
    'SADASIVA KONA': { hi: 'सदाशिव कोना', te: 'సదాశివ కోన' },
    'PUTTUR': { hi: 'पुत्तूर', te: 'పుత్తూరు' }
};

let currentLang = 'en';

// Helper for passenger.js dynamic rendering
function t(key, fallback) {
    const dict = TRANSLATIONS[currentLang];
    return dict[key] ?? TRANSLATIONS.en[key] ?? fallback;
}

// Helper to translate place/route names
function tPlace(name) {
    if (!name) return name;
    if (currentLang === 'en') return name;

    // Handle "SOURCE - DESTINATION" format
    if (name.includes(' - ')) {
        return name.split(' - ').map(p => tPlace(p.trim())).join(' - ');
    }
    // Handle "SOURCE -> DESTINATION" format
    if (name.includes(' \u2192 ')) {
        return name.split(' \u2192 ').map(p => tPlace(p.trim())).join(' \u2192 ');
    }
    if (name.includes(' -> ')) {
        return name.split(' -> ').map(p => tPlace(p.trim())).join(' -> ');
    }

    // Direct translation
    const upperName = name.toUpperCase();
    if (PLACE_TRANSLATIONS[upperName] && PLACE_TRANSLATIONS[upperName][currentLang]) {
        return PLACE_TRANSLATIONS[upperName][currentLang];
    }
    
    // Partial translation (e.g. if the name contains a known city)
    let translated = name;
    for (const [eng, trans] of Object.entries(PLACE_TRANSLATIONS)) {
        if (trans[currentLang]) {
            // Use regex with word boundaries to avoid partial word replacement
            const regex = new RegExp(`\\b${eng}\\b`, 'gi');
            translated = translated.replace(regex, trans[currentLang]);
        }
    }
    return translated;
}

/**
 * Apply translations to all static [data-i18n] elements, AND re-render
 * any JS-generated dynamic content (bus cards, timeline, etc.) so switching
 * language mid-session translates absolutely everything on the page.
 */
function applyLanguage(lang) {
    if (!TRANSLATIONS[lang]) lang = 'en';
    currentLang = lang;
    document.documentElement.lang = lang;

    const dict = TRANSLATIONS[lang];
    const fallback = TRANSLATIONS.en;

    // 1. Static text nodes
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const text = dict[key] ?? fallback[key];
        if (text !== undefined) el.textContent = text;
    });

    // 2. Placeholder attributes
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const text = dict[key] ?? fallback[key];
        if (text !== undefined) el.setAttribute('placeholder', text);
    });

    // 3. Title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const text = dict[key] ?? fallback[key];
        if (text !== undefined) el.setAttribute('title', text);
    });

    // 4. innerHTML blocks (demo hints etc.)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        const text = dict[key] ?? fallback[key];
        if (text !== undefined) el.innerHTML = text;
    });

    // Keep <select> in sync
    const switcher = document.getElementById('lang-switcher');
    if (switcher) switcher.value = lang;

    try { localStorage.setItem('preferredLang', lang); } catch (e) { /* storage may be unavailable */ }

    // 5. Re-render dynamic JS content if the functions exist
    if (typeof renderBusList === 'function') {
        try { renderBusList(); } catch (e) { /* ignore if data not loaded yet */ }
    }
    if (typeof updateProgressPanel === 'function' && typeof selectedBus !== 'undefined' && selectedBus) {
        try { loadProgressData(); } catch (e) { /* ignore */ }
    }
    if (typeof renderMapPills === 'function') {
        try { renderMapPills(); } catch (e) { /* ignore */ }
    }
}

// Called directly by the <select onchange="setLanguage(this.value)">
function setLanguage(lang) {
    applyLanguage(lang);
}

document.addEventListener('DOMContentLoaded', () => {
    let saved = 'en';
    try { saved = localStorage.getItem('preferredLang') || 'en'; } catch (e) { /* ignore */ }
    applyLanguage(saved);
});
