// ============================================================
// Smart Public Transport — Passenger Dashboard JS
// Handles: Tab Navigation, Bus Search, Leaflet Map, Progress
// ============================================================

let allBuses = [];
let allRoutes = [];
let selectedBus = null;
let currentFilter = 'all';
let map = null;
let busMarkers = {};
let stopMarkers = [];
let routeLine = null;
let refreshInterval = null;
let progressMiniMap = null;
let progressMiniMarker = null;
let lastTripMatches = [];
let placeSuggestTimer = null;

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadBuses();
    loadRoutes();
    // Auto-refresh bus data every 8 seconds
    setInterval(loadBuses, 8000);
});

// ============================================================
// TAB NAVIGATION
// ============================================================
function switchTab(tabName) {
    // Hide all panels
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    // Show target
    const panel = document.getElementById('tab-' + tabName);
    if (panel) panel.classList.add('active');

    // Update nav styling
    document.querySelectorAll('.nav-tab').forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.remove('text-on-surface-variant');
            btn.classList.add('text-primary', 'font-bold');
        } else {
            btn.classList.remove('text-primary', 'font-bold');
            btn.classList.add('text-on-surface-variant');
        }
    });

    // Initialize map on first visit to Live Radar tab
    if (tabName === 'map') {
        if (!map) {
            setTimeout(initMap, 100);
        } else {
            setTimeout(() => map.invalidateSize(), 100);
        }
    }
    if (tabName === 'progress' && progressMiniMap) {
        setTimeout(() => progressMiniMap.invalidateSize(), 100);
    }
}

// ============================================================
// DATA LOADING
// ============================================================
function loadBuses() {
    fetch('/api/buses')
        .then(r => r.json())
        .then(data => {
            allBuses = data;
            renderBusList();
            if (map) updateMapMarkers();
            renderMapPills();
            // Auto-refresh selected bus progress & map
            if (selectedBus) {
                const updated = allBuses.find(b => String(b.id) === String(selectedBus.id));
                if (updated) {
                    selectedBus = updated;
                    updateProgressPanel();
                    if (map && updated.current_latitude && updated.current_longitude) {
                        if (busMarkers[updated.id]) {
                            busMarkers[updated.id].setLatLng([updated.current_latitude, updated.current_longitude]);
                        }
                        const coordsEl = document.getElementById('map-bus-coords');
                        if (coordsEl) coordsEl.textContent = `GPS: ${Number(updated.current_latitude).toFixed(5)}, ${Number(updated.current_longitude).toFixed(5)}`;
                    }
                }
            }
        })
        .catch(() => {});
}

function loadRoutes() {
    fetch('/api/routes')
        .then(r => r.json())
        .then(data => { allRoutes = data; })
        .catch(() => {});
}

// ============================================================
// BUS SEARCH & FILTER (Find Bus Tab)
// ============================================================
function searchBuses() {
    renderBusList();
}

function setFilter(filter, btn) {
    currentFilter = filter;
    // Update chip styling
    document.querySelectorAll('.filter-chip').forEach(c => {
        c.classList.remove('bg-inverse-surface', 'text-inverse-on-surface', 'border-inverse-surface');
        c.classList.add('bg-white', 'text-on-surface', 'border-outline-variant');
    });
    btn.classList.remove('bg-white', 'text-on-surface', 'border-outline-variant');
    btn.classList.add('bg-inverse-surface', 'text-inverse-on-surface', 'border-inverse-surface');
    renderBusList();
}

function renderBusList() {
    const container = document.getElementById('bus-results-list');
    const query = (document.getElementById('bus-search-input').value || '').toLowerCase();

    let filtered = allBuses.filter(b => {
        // Search filter
        const searchMatch = !query ||
            (b.bus_number || '').toLowerCase().includes(query) ||
            (b.bus_name || '').toLowerCase().includes(query) ||
            (b.route_name || '').toLowerCase().includes(query) ||
            (b.operator || '').toLowerCase().includes(query);

        // Operator filter
        let operatorMatch = true;
        if (currentFilter === 'APSRTC') operatorMatch = b.operator === 'APSRTC';
        else if (currentFilter === 'TGSRTC') operatorMatch = b.operator === 'TGSRTC';
        else if (currentFilter === 'live') operatorMatch = b.gps_source === 'Real' || b.status === 'Active Trip';

        return searchMatch && operatorMatch;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-on-surface-variant text-[14px]">
                <span class="material-symbols-outlined text-[40px] block mb-2 opacity-40">search_off</span>
                ${t('no_buses_found', 'No buses found matching your search')}
            </div>`;
        return;
    }

    container.innerHTML = filtered.map(bus => {
        const isLive = bus.gps_source === 'Real' || bus.status === 'Active Trip';
        const delayBadge = bus.delay_status === 'DELAYED'
            ? `<span class="px-2 py-0.5 rounded-full bg-red-50 text-red-600 text-[11px] font-bold">${t('delayed','DELAYED')} +${bus.delay_minutes || 0}m</span>`
            : (isLive ? `<span class="px-2 py-0.5 rounded-full bg-green-50 text-green-700 text-[11px] font-bold">${t('on_time','ON TIME')}</span>` : '');

        const serviceColor = getServiceColor(bus.service_type);
        const hasCoords = bus.current_latitude && bus.current_longitude;
        const coordsText = hasCoords ? `${Number(bus.current_latitude).toFixed(4)}, ${Number(bus.current_longitude).toFixed(4)}` : '';

        return `
        <div class="bus-result-card" onclick="trackOnMap('${bus.id}')">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-[13px] font-bold font-body" style="background:${serviceColor.bg};color:${serviceColor.text};border:1px solid ${serviceColor.border}">
                        ${bus.bus_number || '--'}
                    </span>
                    <span class="px-2 py-0.5 rounded text-[11px] font-bold uppercase" style="background:${serviceColor.bg};color:${serviceColor.text};border:1px solid ${serviceColor.border}">
                        ${bus.service_type || t('standard','Standard')}
                    </span>
                </div>
                <div class="flex items-center gap-1">
                    ${isLive ? `<span class="w-2.5 h-2.5 rounded-full bg-green-500 live-pulse"></span><span class="text-[11px] font-bold text-green-700">${t('live_gps','LIVE GPS')}</span>` : `<span class="text-[11px] text-on-surface-variant">${t('gps_simulated','GPS Simulated')}</span>`}
                </div>
            </div>
            <div class="flex items-center justify-between mb-2">
                <div class="min-w-0">
                    <p class="font-headline text-[14px] font-bold text-on-surface truncate">${tPlace(bus.route_name) || tPlace(bus.bus_name) || t('unknown_route','Unknown Route')}</p>
                    <p class="text-[12px] text-on-surface-variant">${bus.operator || '--'} • ${tPlace(bus.source) || ''} → ${tPlace(bus.destination) || ''}</p>
                    ${bus.driver_name ? `<p class="text-[12px] text-primary font-bold mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-[15px]">badge</span> ${t('driver_label','Driver')}: ${bus.driver_name}</p>` : ''}
                    ${hasCoords ? `<p class="text-[11px] text-on-surface-variant mt-0.5 font-mono flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">location_on</span> ${coordsText}</p>` : ''}
                </div>
                <div class="flex flex-col items-end gap-1 shrink-0 ml-2">
                    ${delayBadge}
                </div>
            </div>
            <div class="flex items-center gap-2 pt-2 border-t border-outline-variant/20 mt-2" onclick="event.stopPropagation()">
                <button onclick="trackOnMap('${bus.id}')" class="flex-1 py-2 px-3 rounded-lg bg-primary text-white text-[12px] font-bold flex items-center justify-center gap-1 hover:bg-primary-container transition-colors shadow-sm">
                    <span class="material-symbols-outlined text-[16px]">explore</span>
                    ${t('view_live_gps_map','View Live GPS Map')}
                </button>
                <button onclick="selectBus('${bus.id}')" class="flex-1 py-2 px-3 rounded-lg bg-surface-container text-on-surface text-[12px] font-bold flex items-center justify-center gap-1 hover:bg-surface-container-high transition-colors">
                    <span class="material-symbols-outlined text-[16px]">timeline</span>
                    ${t('stop_timeline','Stop Timeline')}
                </button>
            </div>
        </div>`;
    }).join('');
}

function getServiceColor(type) {
    const t = (type || '').toLowerCase();
    if (t.includes('express')) return { bg: '#eff6ff', text: '#1d4ed8', border: '#bfdbfe' };
    if (t.includes('palle') || t.includes('velugu')) return { bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' };
    if (t.includes('super') || t.includes('luxury') || t.includes('deluxe')) return { bg: '#f5f3ff', text: '#7c3aed', border: '#c4b5fd' };
    if (t.includes('garuda') || t.includes('amaravati')) return { bg: '#f0fdfa', text: '#0f766e', border: '#99f6e4' };
    return { bg: '#f8fafc', text: '#475569', border: '#cbd5e1' };
}

// ============================================================
// BUS SELECTION & TRACKING
// ============================================================
function selectBus(busId) {
    const bus = allBuses.find(b => String(b.id) === String(busId));
    if (!bus) return;
    selectedBus = bus;

    // Switch to progress tab
    switchTab('progress');
    loadProgressData();
}

function trackBusFromMap() {
    if (selectedBus) {
        switchTab('progress');
        loadProgressData();
    }
}

function trackOnMap(busId) {
    const bus = allBuses.find(b => String(b.id) === String(busId));
    if (!bus) return;
    selectedBus = bus;

    switchTab('map');

    setTimeout(() => {
        if (!map) initMap();
        if (map) {
            map.invalidateSize();
            if (bus.current_latitude && bus.current_longitude) {
                map.setView([bus.current_latitude, bus.current_longitude], 15, { animate: true });
                if (busMarkers[bus.id]) {
                    busMarkers[bus.id].openPopup();
                }
            }
            showMapBusCard(bus);
            const recenterBtn = document.getElementById('map-recenter-btn');
            if (recenterBtn) recenterBtn.style.display = 'flex';
        }
    }, 120);
}

function recenterSelectedBus() {
    if (!selectedBus || !map) return;
    if (selectedBus.current_latitude && selectedBus.current_longitude) {
        map.setView([selectedBus.current_latitude, selectedBus.current_longitude], 15, { animate: true });
        if (busMarkers[selectedBus.id]) {
            busMarkers[selectedBus.id].openPopup();
        }
    }
}

function loadProgressData() {
    if (!selectedBus) return;

    // Show progress content, hide empty state
    document.getElementById('progress-empty').style.display = 'none';
    document.getElementById('progress-content').style.display = 'flex';

    // Update banner
    document.getElementById('prog-bus-code').textContent = selectedBus.bus_number || '--';
    document.getElementById('prog-service-type').textContent = selectedBus.service_type || t('standard','Standard');
    document.getElementById('prog-operator').textContent = (selectedBus.operator || '--') + ' ' + t('verified','Verified');
    document.getElementById('prog-route-name').textContent = tPlace(selectedBus.route_name) || tPlace(selectedBus.bus_name) || '--';

    const driverInfoEl = document.getElementById('prog-driver-info');
    if (driverInfoEl) {
        driverInfoEl.innerHTML = selectedBus.driver_name 
            ? `<span class="material-symbols-outlined text-[15px]">person</span> ${t('driver_label','Driver')}: <b class="underline">${selectedBus.driver_name}</b>`
            : '';
    }

    // Update delay status
    if (selectedBus.delay_status === 'DELAYED') {
        document.getElementById('prog-delay-status').textContent = t('delayed','DELAYED');
        document.getElementById('prog-delay-status').style.color = '#dc2626';
        document.getElementById('prog-delay-detail').textContent = `+${selectedBus.delay_minutes || 0} ${t('min_behind','min behind')}`;
    } else {
        document.getElementById('prog-delay-status').textContent = t('on_time','ON TIME');
        document.getElementById('prog-delay-status').style.color = '#004d27';
        document.getElementById('prog-delay-detail').textContent = t('running_on_schedule','Running on schedule');
    }

    renderProgressMiniMap();

    // Load stops for this bus's route
    if (selectedBus.route_id) {
        fetch('/api/stops/' + selectedBus.route_id)
            .then(r => r.json())
            .then(stops => {
                renderTimeline(stops);
                updateMetrics(stops);
            })
            .catch(() => {});
    }
}

function updateProgressPanel() {
    if (!selectedBus) return;

    const driverInfoEl = document.getElementById('prog-driver-info');
    if (driverInfoEl) {
        driverInfoEl.innerHTML = selectedBus.driver_name 
            ? `<span class="material-symbols-outlined text-[15px]">person</span> ${t('driver_label','Driver')}: <b class="underline">${selectedBus.driver_name}</b>`
            : '';
    }

    // Update delay status live
    if (selectedBus.delay_status === 'DELAYED') {
        document.getElementById('prog-delay-status').textContent = t('delayed','DELAYED');
        document.getElementById('prog-delay-status').style.color = '#dc2626';
        document.getElementById('prog-delay-detail').textContent = `+${selectedBus.delay_minutes || 0} ${t('min_behind','min behind')}`;
    } else {
        document.getElementById('prog-delay-status').textContent = t('on_time','ON TIME');
        document.getElementById('prog-delay-status').style.color = '#004d27';
        document.getElementById('prog-delay-detail').textContent = t('running_on_schedule','Running on schedule');
    }

    renderProgressMiniMap();

    // Reload stops timeline
    if (selectedBus.route_id) {
        fetch('/api/stops/' + selectedBus.route_id)
            .then(r => r.json())
            .then(stops => {
                renderTimeline(stops);
                updateMetrics(stops);
            })
            .catch(() => {});
    }
}

function renderProgressMiniMap() {
    if (!selectedBus || !selectedBus.current_latitude || !selectedBus.current_longitude) return;

    const coordsEl = document.getElementById('prog-map-coords');
    if (coordsEl) {
        coordsEl.textContent = `${Number(selectedBus.current_latitude).toFixed(5)}, ${Number(selectedBus.current_longitude).toFixed(5)}`;
    }

    const lat = selectedBus.current_latitude;
    const lng = selectedBus.current_longitude;

    if (!progressMiniMap) {
        const miniContainer = document.getElementById('progress-mini-map');
        if (miniContainer) {
            progressMiniMap = L.map('progress-mini-map').setView([lat, lng], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap',
                maxZoom: 19
            }).addTo(progressMiniMap);

            const icon = L.divIcon({
                className: 'custom-bus-icon-mini',
                html: `<div style="width:30px;height:30px;border-radius:50%;background:#16a34a;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.35);border:2px solid white;">
                    <span style="color:white;font-size:16px;" class="material-symbols-outlined">directions_bus</span>
                </div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });

            progressMiniMarker = L.marker([lat, lng], { icon })
                .addTo(progressMiniMap)
                .bindPopup(`<b>${selectedBus.bus_number}</b><br>${t('driver_label','Driver')}: ${selectedBus.driver_name || 'Active'}<br>${t('live_gps','Live GPS')}`)
                .openPopup();
        }
    } else {
        progressMiniMap.setView([lat, lng], 15);
        if (progressMiniMarker) {
            progressMiniMarker.setLatLng([lat, lng]);
            progressMiniMarker.setPopupContent(`<b>${selectedBus.bus_number}</b><br>${t('driver_label','Driver')}: ${selectedBus.driver_name || 'Active'}<br>${t('live_gps','Live GPS')}`);
        }
        setTimeout(() => progressMiniMap.invalidateSize(), 100);
    }
}

function refreshProgress() {
    const icon = document.getElementById('refresh-icon');
    icon.classList.add('animate-spin');
    loadBuses();
    setTimeout(() => icon.classList.remove('animate-spin'), 800);
}

// ============================================================
// STOP-BY-STOP TIMELINE RENDERER
// ============================================================
function renderTimeline(stops) {
    const container = document.getElementById('progress-timeline');
    if (!stops || stops.length === 0) {
        container.innerHTML = `<p class="text-[13px] text-on-surface-variant text-center py-4">${t('no_stops_data','No stops data available')}</p>`;
        return;
    }

    // Determine bus position relative to stops using distance
    const busLat = selectedBus.current_latitude;
    const busLng = selectedBus.current_longitude;
    let closestIdx = 0;
    let minDist = Infinity;

    stops.forEach((s, i) => {
        const d = haversine(busLat, busLng, s.latitude, s.longitude);
        if (d < minDist) { minDist = d; closestIdx = i; }
    });

    // If very close to current stop (<500m), bus has passed it
    const busPassedClosest = minDist < 0.5;
    const currentStopIdx = busPassedClosest ? closestIdx + 1 : closestIdx;

    // Calculate progress height for the filled spine
    const progressPercent = Math.min(100, ((closestIdx + (busPassedClosest ? 1 : 0.5)) / (stops.length - 1)) * 100);

    let html = '';
    // Background spine
    html += `<div class="timeline-spine"></div>`;
    html += `<div class="timeline-progress" style="height:${progressPercent}%"></div>`;

    stops.forEach((stop, i) => {
        const isPassed = i < currentStopIdx;
        const isCurrent = i === currentStopIdx;
        const isLast = i === stops.length - 1;
        const dist = haversine(busLat, busLng, stop.latitude, stop.longitude);
        const distText = dist < 1 ? `${Math.round(dist * 1000)}m ${t('away','away')}` : `${dist.toFixed(1)} km ${t('away','away')}`;

        if (isPassed) {
            // Passed stop
            html += `
            <div class="relative flex items-start gap-3 pb-6">
                <div class="w-4 h-4 rounded-full bg-primary flex items-center justify-center shrink-0 mt-0.5 z-10 ring-4 ring-white">
                    <span class="material-symbols-outlined text-on-primary text-[10px]">check</span>
                </div>
                <div class="flex-1 flex items-baseline justify-between min-w-0">
                    <div class="flex flex-col min-w-0">
                        <span class="text-[14px] font-semibold text-on-surface truncate">${tPlace(stop.stop_name)}</span>
                        <span class="text-[12px] text-on-surface-variant">${stop.area_type || ''}</span>
                    </div>
                    <div class="flex flex-col items-end shrink-0 pl-2">
                        <span class="text-[13px] font-bold text-on-surface">${stop.scheduled_arrival_time || '--'}</span>
                        <span class="text-[11px] text-primary font-medium">${t('passed','Passed')}</span>
                    </div>
                </div>
            </div>`;
        } else if (isCurrent && !isLast) {
            // Live position callout BEFORE this stop
            html += `
            <div class="relative flex items-center gap-3 py-2 my-1 z-20">
                <div class="w-8 h-8 rounded-full bg-primary-container text-on-primary flex items-center justify-center shrink-0 -ml-2 shadow-md ring-4 ring-primary-fixed animate-bounce">
                    <span class="material-symbols-outlined text-[18px]">directions_bus</span>
                </div>
                <div class="flex-1 bg-primary text-on-primary rounded-xl px-3 py-2 shadow-md flex items-center justify-between gap-2">
                    <div class="flex flex-col min-w-0">
                        <div class="flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-primary-fixed animate-ping"></span>
                            <span class="text-[11px] font-bold text-primary-fixed uppercase tracking-wider">${t('live_position','Live Position')}</span>
                        </div>
                        <span class="text-[12px] font-bold text-on-primary truncate">${distText} ${t('from_word','from')} ${tPlace(stop.stop_name)}</span>
                    </div>
                    <span class="px-2 py-0.5 rounded bg-white text-primary text-[13px] font-bold shrink-0">
                        ${estimateETA(dist)} ${t('eta_label','ETA')}
                    </span>
                </div>
            </div>`;

            // Current target stop
            html += `
            <div class="relative flex items-start gap-3 pt-2 pb-6">
                <div class="w-5 h-5 rounded-full bg-tertiary-container text-on-tertiary flex items-center justify-center shrink-0 -ml-0.5 mt-0.5 z-10 ring-4 ring-tertiary-fixed shadow-sm">
                    <span class="material-symbols-outlined text-[12px]">my_location</span>
                </div>
                <div class="flex-1 bg-surface-container-low rounded-xl p-3 flex flex-col gap-1 min-w-0">
                    <div class="flex items-center justify-between">
                        <span class="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed text-[11px] font-bold uppercase">${t('next_stop','Next Stop')}</span>
                        <span class="text-[13px] font-bold text-tertiary-container">${stop.scheduled_arrival_time || '--'}</span>
                    </div>
                    <div class="flex items-baseline justify-between min-w-0">
                        <span class="font-headline text-[16px] font-bold text-on-surface truncate">${tPlace(stop.stop_name)}</span>
                        <span class="text-[12px] font-bold text-tertiary shrink-0 pl-2">${distText}</span>
                    </div>
                </div>
            </div>`;
        } else if (isLast) {
            // Terminus
            html += `
            <div class="relative flex items-start gap-3">
                <div class="w-4 h-4 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shrink-0 mt-0.5 z-10 ring-4 ring-white">
                    <span class="material-symbols-outlined text-[10px]">flag</span>
                </div>
                <div class="flex-1 flex items-baseline justify-between min-w-0">
                    <div class="flex flex-col min-w-0">
                        <span class="text-[14px] font-bold text-on-surface truncate">${tPlace(stop.stop_name)}</span>
                        <span class="text-[12px] text-on-surface-variant">${t('final_destination','Final Destination')}</span>
                    </div>
                    <div class="flex flex-col items-end shrink-0 pl-2">
                        <span class="text-[13px] font-bold text-on-surface">${stop.scheduled_arrival_time || '--'}</span>
                        <span class="text-[11px] text-primary font-bold">${t('terminus','Terminus')}</span>
                    </div>
                </div>
            </div>`;
        } else {
            // Upcoming stop
            html += `
            <div class="relative flex items-start gap-3 pb-6">
                <div class="w-3.5 h-3.5 rounded-full bg-surface-container-highest shrink-0 mt-1 z-10 ring-4 ring-white"></div>
                <div class="flex-1 flex items-baseline justify-between min-w-0">
                    <div class="flex flex-col min-w-0">
                        <span class="text-[14px] font-semibold text-on-surface truncate">${tPlace(stop.stop_name)}</span>
                        <span class="text-[12px] text-on-surface-variant">${stop.area_type || ''}</span>
                    </div>
                    <div class="flex flex-col items-end shrink-0 pl-2">
                        <span class="text-[13px] font-bold text-on-surface">${stop.scheduled_arrival_time || '--'}</span>
                        <span class="text-[11px] text-on-surface-variant">${distText}</span>
                    </div>
                </div>
            </div>`;
        }
    });

    container.innerHTML = html;

    // Update next stop info in metrics
    if (currentStopIdx < stops.length) {
        const nextStop = stops[currentStopIdx];
        document.getElementById('prog-next-stop').textContent = nextStop.stop_name;
        const dist = haversine(busLat, busLng, nextStop.latitude, nextStop.longitude);
        document.getElementById('prog-next-eta').textContent = `${estimateETA(dist)} • ${dist < 1 ? Math.round(dist*1000)+'m' : dist.toFixed(1)+' km'}`;
    }
}

function updateMetrics(stops) {
    if (!selectedBus || !stops || stops.length === 0) return;
    const busLat = selectedBus.current_latitude;
    const busLng = selectedBus.current_longitude;

    // Find closest upcoming stop
    let closestIdx = 0;
    let minDist = Infinity;
    stops.forEach((s, i) => {
        const d = haversine(busLat, busLng, s.latitude, s.longitude);
        if (d < minDist) { minDist = d; closestIdx = i; }
    });

    const distToNext = minDist;
    // Total route distance (first to last stop)
    const totalDist = haversine(stops[0].latitude, stops[0].longitude, stops[stops.length-1].latitude, stops[stops.length-1].longitude);

    document.getElementById('prog-distance').textContent = distToNext < 1 ? `${Math.round(distToNext*1000)}m` : `${distToNext.toFixed(1)} km`;
    document.getElementById('prog-total-dist').textContent = `${t('to_next_stop','to next stop')} • ${totalDist.toFixed(0)} ${t('km_total','km total')}`;
}

// ============================================================
// LEAFLET MAP (Live Radar Tab)
// ============================================================
function initMap() {
    let centerLat = 16.5062;
    let centerLng = 80.6480;
    let zoomLevel = 10;

    if (selectedBus && selectedBus.current_latitude && selectedBus.current_longitude) {
        centerLat = selectedBus.current_latitude;
        centerLng = selectedBus.current_longitude;
        zoomLevel = 15;
    } else if (allBuses.length > 0) {
        const liveBus = allBuses.find(b => b.gps_source === 'Real' || b.status === 'Active Trip') || allBuses[0];
        if (liveBus && liveBus.current_latitude) {
            centerLat = liveBus.current_latitude;
            centerLng = liveBus.current_longitude;
            zoomLevel = 14;
        }
    }

    map = L.map('live-map').setView([centerLat, centerLng], zoomLevel);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    updateMapMarkers();
    renderMapPills();

    if (selectedBus) {
        showMapBusCard(selectedBus);
    }
}

function renderMapPills() {
    const container = document.getElementById('map-live-bus-pills');
    if (!container) return;

    container.innerHTML = allBuses.map(b => {
        const isLive = b.gps_source === 'Real' || b.status === 'Active Trip';
        const isSelected = selectedBus && String(selectedBus.id) === String(b.id);
        const bg = isSelected ? 'bg-primary text-white border-primary shadow-sm' : (isLive ? 'bg-green-50 text-green-800 border-green-300' : 'bg-white/90 text-on-surface border-outline-variant/40');
        const star = (b.bus_number || '').includes('00 C') ? '⭐ ' : '';

        return `<button onclick="trackOnMap('${b.id}')" class="shrink-0 h-7 px-2.5 rounded-full text-[11px] font-bold border transition-all flex items-center gap-1 ${bg}">
            ${isLive ? '<span class="w-1.5 h-1.5 rounded-full bg-green-500 live-pulse"></span>' : ''}
            <span>${star}${b.bus_number}</span>
        </button>`;
    }).join('');
}

function updateMapMarkers() {
    if (!map) return;

    allBuses.forEach(bus => {
        if (!bus.current_latitude || !bus.current_longitude) return;

        const isLive = bus.gps_source === 'Real' || bus.status === 'Active Trip';
        const isSelected = selectedBus && String(selectedBus.id) === String(bus.id);
        const color = isLive ? '#16a34a' : '#475569';
        const border = isSelected ? '3px solid #facc15' : '2px solid white';
        const scale = isSelected ? 'transform:scale(1.2);' : '';

        const icon = L.divIcon({
            className: 'custom-bus-icon',
            html: `<div style="position:relative;width:32px;height:32px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,0.35);border:${border};${scale}">
                ${isLive ? '<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60"></span>' : ''}
                <span style="color:white;font-size:16px;z-index:2;" class="material-symbols-outlined">directions_bus</span>
            </div>`,
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        });

        const popupContent = `
            <div style="font-family:sans-serif;padding:4px;min-width:170px;">
                <div style="font-size:14px;font-weight:bold;color:#004d27;">${bus.bus_number}</div>
                <div style="font-size:12px;color:#555;margin-bottom:4px;">${tPlace(bus.route_name) || tPlace(bus.bus_name) || ''}</div>
                <div style="display:inline-block;padding:2px 6px;border-radius:4px;background:${isLive ? '#dcfce7' : '#f1f5f9'};color:${isLive ? '#15803d' : '#475569'};font-size:11px;font-weight:bold;margin-bottom:4px;">
                    ${isLive ? '🟢 ' + t('live_gps_stream','LIVE GPS STREAM') : t('gps_simulated','GPS Simulated')}
                </div>
                ${bus.driver_name ? `<div style="font-size:11px;color:#1d4ed8;font-weight:bold;">${t('driver_label','Driver')}: ${bus.driver_name}</div>` : ''}
                <div style="font-size:10px;color:#666;font-family:monospace;margin-top:2px;">
                    GPS: ${Number(bus.current_latitude).toFixed(5)}, ${Number(bus.current_longitude).toFixed(5)}
                </div>
            </div>`;

        if (busMarkers[bus.id]) {
            busMarkers[bus.id].setLatLng([bus.current_latitude, bus.current_longitude]);
            busMarkers[bus.id].setIcon(icon);
            busMarkers[bus.id].setPopupContent(popupContent);
        } else {
            const marker = L.marker([bus.current_latitude, bus.current_longitude], { icon })
                .addTo(map)
                .bindPopup(popupContent)
                .on('click', () => {
                    selectedBus = bus;
                    showMapBusCard(bus);
                    const recenterBtn = document.getElementById('map-recenter-btn');
                    if (recenterBtn) recenterBtn.style.display = 'flex';
                });
            marker.bindTooltip(`${bus.bus_number} (${bus.driver_name || bus.operator})`, { direction: 'top', offset: [0, -18] });
            busMarkers[bus.id] = marker;
        }
    });
}

function showMapBusCard(bus) {
    document.getElementById('map-bus-card').style.display = 'block';
    document.getElementById('map-bus-title').textContent = bus.bus_number;
    document.getElementById('map-bus-route').textContent = tPlace(bus.route_name) || tPlace(bus.bus_name) || '';

    const isLive = bus.gps_source === 'Real' || bus.status === 'Active Trip';
    document.getElementById('map-bus-status').textContent = isLive ? t('live_gps','LIVE GPS') : t('gps_simulated','Simulated');
    document.getElementById('map-bus-status-dot').style.background = isLive ? '#16a34a' : '#94a3b8';

    const driverEl = document.getElementById('map-bus-driver');
    if (driverEl) driverEl.textContent = bus.driver_name ? `${t('driver_label','Driver')}: ${bus.driver_name}` : '';

    const coordsEl = document.getElementById('map-bus-coords');
    if (coordsEl) {
        coordsEl.textContent = bus.current_latitude ? `GPS: ${Number(bus.current_latitude).toFixed(5)}, ${Number(bus.current_longitude).toFixed(5)}` : '';
    }

    document.getElementById('map-bus-next-stop').textContent = tPlace(bus.next_stop_name) || t('loading','Loading...');

    // Load stops and draw route on map
    if (bus.route_id) {
        fetch('/api/stops/' + bus.route_id)
            .then(r => r.json())
            .then(stops => {
                drawRouteOnMap(stops, bus);
            })
            .catch(() => {});
    }
}

function drawRouteOnMap(stops, bus) {
    // Clear old route line and stop markers
    if (routeLine) { map.removeLayer(routeLine); routeLine = null; }
    stopMarkers.forEach(m => map.removeLayer(m));
    stopMarkers = [];

    if (!stops || stops.length === 0) {
        if (bus && bus.current_latitude && bus.current_longitude) {
            map.setView([bus.current_latitude, bus.current_longitude], 15);
        }
        return;
    }

    // Draw polyline through stops
    const coords = stops.map(s => [s.latitude, s.longitude]);
    routeLine = L.polyline(coords, { color: '#006837', weight: 4, opacity: 0.8, dashArray: '8 5' }).addTo(map);

    // Add stop markers
    stops.forEach((stop, i) => {
        const isFirst = i === 0;
        const isLast = i === stops.length - 1;
        const color = isFirst ? '#006837' : (isLast ? '#545f73' : '#94a3b8');
        const size = (isFirst || isLast) ? 10 : 7;

        const icon = L.divIcon({
            className: 'stop-icon',
            html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>`,
            iconSize: [size, size],
            iconAnchor: [size/2, size/2]
        });

        const marker = L.marker([stop.latitude, stop.longitude], { icon })
            .addTo(map)
            .bindTooltip(`${tPlace(stop.stop_name)} (${t('stop_word','Stop')} ${stop.stop_order})`, { direction: 'top' });
        stopMarkers.push(marker);
    });

    // If bus has current GPS, ALWAYS include the bus in bounds or center on bus!
    const bounds = routeLine.getBounds();
    if (bus && bus.current_latitude && bus.current_longitude) {
        bounds.extend([bus.current_latitude, bus.current_longitude]);
    }
    const distToFirst = (bus && bus.current_latitude) ? haversine(bus.current_latitude, bus.current_longitude, stops[0].latitude, stops[0].longitude) : 0;
    if (distToFirst > 400 && bus && bus.current_latitude) {
        map.setView([bus.current_latitude, bus.current_longitude], 15);
    } else {
        map.fitBounds(bounds.pad(0.15));
    }
}

// ============================================================
// COMPLAINTS
// ============================================================
function submitComplaint() {
    const category = document.getElementById('complaint-category').value;
    const description = document.getElementById('complaint-description').value;
    const msgEl = document.getElementById('complaint-msg');

    if (!category || !description) {
        msgEl.textContent = t('complaint_fill','Please fill in category and description.');
        msgEl.style.color = '#dc2626';
        return;
    }

    fetch('/api/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            bus_id: selectedBus ? selectedBus.id : null,
            route_id: selectedBus ? selectedBus.route_id : null,
            category: category,
            description: description
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            msgEl.textContent = data.error;
            msgEl.style.color = '#dc2626';
        } else {
            msgEl.textContent = t('complaint_success','✓ Report submitted successfully!');
            msgEl.style.color = '#004d27';
            document.getElementById('complaint-category').value = '';
            document.getElementById('complaint-description').value = '';
        }
    })
    .catch(() => {
        msgEl.textContent = t('complaint_error','Error submitting report. Try again.');
        msgEl.style.color = '#dc2626';
    });
}

// ============================================================
// UTILITIES
// ============================================================
function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function estimateETA(distKm) {
    // Assume average bus speed ~30 km/h in city
    const minutes = Math.round((distKm / 30) * 60);
    if (minutes < 1) return '<1 min';
    if (minutes >= 60) return `${Math.floor(minutes/60)}h ${minutes%60}m`;
    return `${minutes} min`;
}

// ============================================================
// TRIP PLANNER — Source & Destination -> live path ("where is my bus")
// ============================================================
function t(key, fallback) {
    // Small i18n lookup helper local to this file, tolerant of i18n.js
    // not having loaded yet.
    try {
        const dict = (typeof TRANSLATIONS !== 'undefined') ? (TRANSLATIONS[currentLang] || TRANSLATIONS.en) : null;
        return (dict && dict[key]) || fallback;
    } catch (e) {
        return fallback;
    }
}

function onPlaceInput(inputEl, datalistId) {
    const query = inputEl.value.trim();
    clearTimeout(placeSuggestTimer);
    if (query.length < 2) return;
    placeSuggestTimer = setTimeout(() => {
        fetch(`/api/places/suggest?q=${encodeURIComponent(query)}`)
            .then(r => r.json())
            .then(names => {
                const list = document.getElementById(datalistId);
                if (!list) return;
                list.innerHTML = names.map(n => `<option value="${n.replace(/"/g, '&quot;')}"></option>`).join('');
            })
            .catch(() => {});
    }, 250);
}

function swapTripInputs() {
    const src = document.getElementById('trip-source-input');
    const dst = document.getElementById('trip-destination-input');
    const tmp = src.value;
    src.value = dst.value;
    dst.value = tmp;
}

function planTrip() {
    const source = document.getElementById('trip-source-input').value.trim();
    const destination = document.getElementById('trip-destination-input').value.trim();
    const resultsEl = document.getElementById('trip-results');

    if (!source || !destination) {
        resultsEl.innerHTML = `<p class="text-[12px] text-red-600 px-1 pt-1">${t('field_source', 'Source')} &amp; ${t('field_destination', 'Destination')} required.</p>`;
        return;
    }

    resultsEl.innerHTML = `<p class="text-[12px] text-on-surface-variant px-1 pt-1 flex items-center gap-1.5">
        <span class="material-symbols-outlined text-[15px] animate-spin">progress_activity</span> ${t('trip_searching', 'Searching routes…')}
    </p>`;

    fetch(`/api/trip/plan?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}`)
        .then(r => r.json())
        .then(data => {
            lastTripMatches = data.matches || [];
            renderTripResults(lastTripMatches);
        })
        .catch(() => {
            resultsEl.innerHTML = `<p class="text-[12px] text-red-600 px-1 pt-1">Network error. Please try again.</p>`;
        });
}

function renderTripResults(matches) {
    const resultsEl = document.getElementById('trip-results');
    if (!matches || matches.length === 0) {
        resultsEl.innerHTML = `<p class="text-[12px] text-on-surface-variant px-1 pt-1">${t('trip_no_results', 'No routes found between these two places yet.')}</p>`;
        return;
    }

    resultsEl.innerHTML = matches.map((m, i) => {
        const liveCount = (m.buses || []).filter(b => b.latitude && b.longitude).length;
        const bestEta = (m.buses || [])
            .map(b => b.eta_minutes)
            .filter(v => v !== null && v !== undefined)
            .sort((a, b) => a - b)[0];

        return `<div class="border border-outline-variant/40 rounded-lg p-2.5 mt-2 bg-surface-container-low">
            <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                    <p class="text-[12.5px] font-bold text-on-surface truncate">${m.route_name || ('Route #' + m.route_id)}</p>
                    <p class="text-[11px] text-on-surface-variant mt-0.5">
                        <span data-i18n="boarding_at">${t('boarding_at', 'Board at')}</span> <b>${m.boarding_stop}</b> &rarr;
                        <span data-i18n="alight_at">${t('alight_at', 'Alight at')}</span> <b>${m.alighting_stop}</b>
                    </p>
                    <p class="text-[11px] mt-1 ${liveCount > 0 ? 'text-green-700 font-semibold' : 'text-on-surface-variant'}">
                        ${liveCount > 0
                            ? `🟢 ${liveCount} ${t('live_buses_count', 'live bus(es) found')}${bestEta !== undefined ? ' • ETA ~' + bestEta + ' min' : ''}`
                            : 'No live bus on this route right now'}
                    </p>
                </div>
                <button onclick="viewTripOnMap(${i})" class="shrink-0 h-8 px-2.5 rounded-full bg-primary text-on-primary text-[11px] font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-[15px]">map</span> ${t('view_on_map', 'View on Map')}
                </button>
            </div>
        </div>`;
    }).join('');
}

function viewTripOnMap(matchIndex) {
    const match = lastTripMatches[matchIndex];
    if (!match) return;

    switchTab('map');

    const drawIt = () => {
        // Reuse the existing route-drawing logic; adapt field names to
        // what drawRouteOnMap()/haversine() expect (latitude/longitude/stop_order/stop_name).
        const stopsForDraw = (match.path || []).map(p => ({
            latitude: p.lat, longitude: p.lng, stop_order: p.order, stop_name: p.name
        }));

        const liveBus = (match.buses || []).find(b => b.latitude && b.longitude);
        const busForDraw = liveBus ? { current_latitude: liveBus.latitude, current_longitude: liveBus.longitude } : null;

        drawRouteOnMap(stopsForDraw, busForDraw);

        // Plot every live bus on this route with its own marker + ETA popup.
        (match.buses || []).forEach(b => {
            if (!b.latitude || !b.longitude) return;
            const icon = L.divIcon({
                className: 'trip-bus-icon',
                html: `<div style="width:30px;height:30px;border-radius:50%;background:#2563EB;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,0.35);border:2px solid white;">
                    <span style="color:white;font-size:15px;" class="material-symbols-outlined">directions_bus</span>
                </div>`,
                iconSize: [30, 30], iconAnchor: [15, 15]
            });
            L.marker([b.latitude, b.longitude], { icon }).addTo(map).bindPopup(
                `<b>${b.bus_number}</b><br>${b.operator || ''} ${b.service_type || ''}<br>` +
                (b.eta_minutes !== null && b.eta_minutes !== undefined
                    ? `ETA to ${match.alighting_stop}: ~${b.eta_minutes} min (${b.distance_km} km)`
                    : 'ETA unavailable')
            );
        });
    };

    if (!map) {
        setTimeout(() => { initMap(); setTimeout(drawIt, 150); }, 150);
    } else {
        setTimeout(drawIt, 150);
    }
}
