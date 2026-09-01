/**
 * PLB Interactive Map Module
 * Manages Leaflet map display, node markers, and emergency visualization
 */

let plbMap = null;
const markers = new Map(); // { node_id: leaflet_marker }
const emergencyMarkers = new Map(); // { emergency_id: leaflet_marker }
let mapUpdateInterval = null;
const MAP_UPDATE_INTERVAL = 10000; // 10 seconds

// Valid coordinate ranges
const VALID_LATITUDE = [-90, 90];
const VALID_LONGITUDE = [-180, 180];

/**
 * Validate GPS coordinates
 */
function isValidCoordinate(lat, lng) {
  if (lat === null || lng === null || lat === undefined || lng === undefined) {
    return false;
  }
  const latitude = parseFloat(lat);
  const longitude = parseFloat(lng);
  return (
    !isNaN(latitude) &&
    !isNaN(longitude) &&
    latitude >= VALID_LATITUDE[0] &&
    latitude <= VALID_LATITUDE[1] &&
    longitude >= VALID_LONGITUDE[0] &&
    longitude <= VALID_LONGITUDE[1]
  );
}

/**
 * Get marker icon color based on node status
 */
function getNodeMarkerColor(status) {
  switch (status?.toUpperCase()) {
    case 'ONLINE':
      return '#22c55e'; // green
    case 'OFFLINE':
      return '#6b7280'; // grey
    case 'EMERGENCY':
      return '#dc2626'; // red
    default:
      return '#3b82f6'; // blue
  }
}

/**
 * Get marker icon based on node status
 */
function getNodeMarkerIcon(status) {
  const color = getNodeMarkerColor(status);
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">📍</div>`,
    iconSize: [30, 30],
    className: 'node-marker',
  });
}

/**
 * Get marker icon for SOS/Emergency
 */
function getEmergencyMarkerIcon(eventType) {
  let emoji = '🚨';
  if (eventType?.toUpperCase() === 'HAZARD') {
    emoji = '⚠️';
  }
  return L.divIcon({
    html: `<div style="width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-size: 24px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">${emoji}</div>`,
    iconSize: [35, 35],
    className: 'emergency-marker',
  });
}

/**
 * Create or update node marker on map
 */
function updateNodeMarker(node) {
  if (!isValidCoordinate(node.latitude, node.longitude)) {
    if (markers.has(node.node_id)) {
      plbMap.removeLayer(markers.get(node.node_id));
      markers.delete(node.node_id);
    }
    return;
  }

  const icon = getNodeMarkerIcon(node.status);
  const popupContent = `
    <div style="min-width: 200px;">
      <strong style="font-size: 14px;">${node.node_id}</strong><br>
      <small style="color: #666;">
        Status: <span style="color: ${getNodeMarkerColor(node.status)}; font-weight: bold;">${node.status || 'UNKNOWN'}</span><br>
        Battery: ${node.battery?.toFixed(1) || '-'}%<br>
        Location: ${node.latitude?.toFixed(4) || '-'}, ${node.longitude?.toFixed(4) || '-'}<br>
        Last Seen: ${new Date(node.last_seen).toLocaleTimeString()}<br>
        ${node.rssi !== null ? `RSSI: ${node.rssi} dBm<br>` : ''}
        ${node.snr !== null ? `SNR: ${node.snr} dB` : ''}
      </small>
    </div>
  `;

  if (markers.has(node.node_id)) {
    const existingMarker = markers.get(node.node_id);
    existingMarker.setLatLng([node.latitude, node.longitude]);
    existingMarker.setIcon(icon);
    existingMarker.setPopupContent(popupContent);
  } else {
    const marker = L.marker([node.latitude, node.longitude], { icon })
      .bindPopup(popupContent)
      .addTo(plbMap);
    markers.set(node.node_id, marker);
  }
}

/**
 * Create or update emergency marker on map
 */
function updateEmergencyMarker(emergency) {
  if (!isValidCoordinate(emergency.latitude, emergency.longitude)) {
    if (emergencyMarkers.has(emergency.emergency_id)) {
      plbMap.removeLayer(emergencyMarkers.get(emergency.emergency_id));
      emergencyMarkers.delete(emergency.emergency_id);
    }
    return;
  }

  const icon = getEmergencyMarkerIcon(emergency.event_type);
  const timestamp = new Date(emergency.timestamp).toLocaleString();
  const popupContent = `
    <div style="min-width: 220px;">
      <strong style="font-size: 14px; color: #dc2626;">🚨 ${emergency.event_type || 'EMERGENCY'}</strong><br>
      <small style="color: #666;">
        Emergency ID: ${emergency.emergency_id}<br>
        Node: ${emergency.node_id}<br>
        Priority: ${emergency.priority || '-'}<br>
        Location: ${emergency.latitude?.toFixed(4) || '-'}, ${emergency.longitude?.toFixed(4) || '-'}<br>
        Timestamp: ${timestamp}<br>
        Status: ${emergency.resolved ? '<span style="color: #22c55e;">RESOLVED</span>' : '<span style="color: #dc2626;">ACTIVE</span>'}<br>
        ${emergency.remarks ? `Remarks: ${emergency.remarks}` : ''}
      </small>
    </div>
  `;

  if (emergencyMarkers.has(emergency.emergency_id)) {
    const existingMarker = emergencyMarkers.get(emergency.emergency_id);
    existingMarker.setLatLng([emergency.latitude, emergency.longitude]);
    existingMarker.setIcon(icon);
    existingMarker.setPopupContent(popupContent);
  } else {
    const marker = L.marker([emergency.latitude, emergency.longitude], { icon })
      .bindPopup(popupContent)
      .addTo(plbMap);
    emergencyMarkers.set(emergency.emergency_id, marker);
  }
}

/**
 * Remove stale markers (nodes/emergencies no longer in data)
 */
function removeStaleMarkers(activeNodeIds, activeEmergencyIds) {
  markers.forEach((marker, nodeId) => {
    if (!activeNodeIds.has(nodeId)) {
      plbMap.removeLayer(marker);
      markers.delete(nodeId);
    }
  });

  emergencyMarkers.forEach((marker, emergencyId) => {
    if (!activeEmergencyIds.has(emergencyId)) {
      plbMap.removeLayer(marker);
      emergencyMarkers.delete(emergencyId);
    }
  });
}

/**
 * Fit map bounds to active markers
 */
function fitMapToBounds() {
  const allMarkers = Array.from(markers.values()).concat(Array.from(emergencyMarkers.values()));
  if (allMarkers.length === 0) return;

  if (allMarkers.length === 1) {
    plbMap.setView(allMarkers[0].getLatLng(), 15);
  } else {
    const group = new L.featureGroup(allMarkers);
    plbMap.fitBounds(group.getBounds().pad(0.1));
  }
}

/**
 * Fetch and update nodes on the map
 */
async function updateNodesOnMap() {
  try {
    const response = await fetch('/api/nodes/');
    if (!response.ok) throw new Error('Failed to fetch nodes');
    const nodes = await response.json();

    const activeNodeIds = new Set();
    nodes.forEach((node) => {
      activeNodeIds.add(node.node_id);
      updateNodeMarker(node);
    });

    return activeNodeIds;
  } catch (err) {
    console.error('Error updating nodes on map:', err);
    return new Set();
  }
}

/**
 * Fetch and update emergency events on the map
 */
async function updateEmergenciesOnMap() {
  try {
    const response = await fetch('/api/emergencies/');
    if (!response.ok) throw new Error('Failed to fetch emergencies');
    const emergencies = await response.json();

    const activeEmergencyIds = new Set();
    emergencies.forEach((emergency) => {
      activeEmergencyIds.add(emergency.emergency_id);
      updateEmergencyMarker(emergency);
    });

    return activeEmergencyIds;
  } catch (err) {
    console.error('Error updating emergencies on map:', err);
    return new Set();
  }
}

/**
 * Perform live update of map data
 */
async function performMapUpdate() {
  const activeNodeIds = await updateNodesOnMap();
  const activeEmergencyIds = await updateEmergenciesOnMap();
  removeStaleMarkers(activeNodeIds, activeEmergencyIds);
  fitMapToBounds();
}

/**
 * Initialize Leaflet map with layers
 */
function initializeMap() {
  console.log('🗺️  Starting map initialization...');
  
  if (typeof L === 'undefined') {
    console.error('❌ Leaflet library not loaded!');
    console.error('    Check browser console for script loading errors');
    return;
  }

  const container = document.getElementById('plb-map-container');
  if (!container) {
    console.error('❌ Map container div not found');
    return;
  }

  console.log('✓ Container dimensions:', {
    width: container.offsetWidth,
    height: container.offsetHeight,
    computed: window.getComputedStyle(container)
  });

  try {
    // Create map centered on India (default view)
    console.log('🔨 Creating Leaflet map with L.map()...');
    plbMap = L.map('plb-map-container', {
      center: [20, 78],
      zoom: 5,
      preferCanvas: false
    });
    console.log('✓ Map instance created successfully');

    // Street map layer (default) - OpenStreetMap
    console.log('📍 Adding Street Map layer from OpenStreetMap...');
    const streetLayer = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
      }
    ).addTo(plbMap);
    console.log('✓ Street Map layer added and activated');

    // Satellite layer (MapTiler or fallback)
    console.log('🛰️  Creating Satellite layer...');
    const maptilerApiKey = document.getElementById('maptiler-api-key')?.value || '';
    console.log('   MapTiler API Key present:', !!maptilerApiKey);
    
    const satelliteLayer = L.tileLayer(
      maptilerApiKey
        ? `https://api.maptiler.com/maps/satellite/{z}/{x}/{y}.jpg?key=${maptilerApiKey}`
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution: maptilerApiKey
          ? '© MapTiler © OpenStreetMap contributors'
          : '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
      }
    );
    console.log('✓ Satellite layer created');

    // Layer control for switching maps
    console.log('🎮 Adding layer control...');
    const baseLayers = {
      'Street Map': streetLayer,
      'Satellite': satelliteLayer,
    };
    L.control.layers(baseLayers, {}, { position: 'topleft' }).addTo(plbMap);
    console.log('✓ Layer control added');

    // Load data from APIs
    console.log('📡 Fetching node and emergency data...');
    performMapUpdate();

    // Start live update polling
    if (mapUpdateInterval) clearInterval(mapUpdateInterval);
    mapUpdateInterval = setInterval(performMapUpdate, MAP_UPDATE_INTERVAL);
    console.log(`✓ Live polling started (${MAP_UPDATE_INTERVAL}ms interval)`);

    console.log('✅ PLB Map successfully initialized and ready!');
    console.log('   Center: [20°, 78°] (India)');
    console.log('   Zoom: 5');
    console.log('   Nodes will appear as colored markers');
    console.log('   Emergencies will appear as red/orange markers');
  } catch (err) {
    console.error('❌ CRITICAL ERROR during map initialization:');
    console.error('   Message:', err.message);
    console.error('   Stack:', err.stack);
    console.error('   Full error:', err);
  }
}

// ── Locate on Map feature ───────────────────────────────────────────
let locateMarker = null;

/**
 * Get a distinctive "locate" marker icon (purple pulsing pin)
 */
function getLocateMarkerIcon(label) {
  const displayLabel = label || '📍';
  return L.divIcon({
    html: `<div style="
      background: #a855f7;
      width: 34px; height: 34px;
      border-radius: 50%;
      border: 3px solid #fff;
      display: flex; align-items: center; justify-content: center;
      font-weight: bold; color: #fff; font-size: 13px;
      box-shadow: 0 0 0 4px rgba(168,85,247,0.35), 0 2px 8px rgba(0,0,0,0.4);
      animation: locatePulse 1.5s ease-in-out infinite;
    ">${displayLabel.charAt(0).toUpperCase()}</div>
    <style>
      @keyframes locatePulse {
        0%, 100% { box-shadow: 0 0 0 4px rgba(168,85,247,0.35), 0 2px 8px rgba(0,0,0,0.4); }
        50%      { box-shadow: 0 0 0 10px rgba(168,85,247,0.15), 0 2px 8px rgba(0,0,0,0.4); }
      }
    </style>`,
    iconSize: [34, 34],
    className: 'locate-marker',
  });
}

/**
 * Place a marker on the map at the coordinates entered in the Locate toolbar.
 * Reads values from #locate-lat, #locate-lng, and #locate-label.
 */
function locateOnMap() {
  const latInput = document.getElementById('locate-lat');
  const lngInput = document.getElementById('locate-lng');
  const labelInput = document.getElementById('locate-label');

  const lat = parseFloat(latInput?.value);
  const lng = parseFloat(lngInput?.value);
  const label = labelInput?.value?.trim() || '';

  if (!isValidCoordinate(lat, lng)) {
    alert('Please enter valid coordinates.\nLatitude: -90 to 90\nLongitude: -180 to 180');
    return;
  }

  if (!plbMap) {
    console.error('Map is not initialized yet.');
    return;
  }

  // Remove previous locate marker if present
  if (locateMarker) {
    plbMap.removeLayer(locateMarker);
    locateMarker = null;
  }

  const icon = getLocateMarkerIcon(label);
  const popupContent = `
    <div style="min-width: 180px;">
      <strong style="font-size: 14px; color: #a855f7;">📍 ${label || 'Located Point'}</strong><br>
      <small style="color: #666;">
        Latitude: ${lat.toFixed(4)}<br>
        Longitude: ${lng.toFixed(4)}
      </small>
    </div>
  `;

  locateMarker = L.marker([lat, lng], { icon })
    .bindPopup(popupContent)
    .addTo(plbMap)
    .openPopup();

  // Fly to the located point with a smooth animation
  plbMap.flyTo([lat, lng], 15, { duration: 1.2 });
}

/**
 * Remove the locate marker from the map and clear the toolbar inputs.
 */
function clearLocateMarker() {
  if (locateMarker && plbMap) {
    plbMap.removeLayer(locateMarker);
    locateMarker = null;
  }

  const latInput = document.getElementById('locate-lat');
  const lngInput = document.getElementById('locate-lng');
  const labelInput = document.getElementById('locate-label');
  if (latInput) latInput.value = '';
  if (lngInput) lngInput.value = '';
  if (labelInput) labelInput.value = '';
}

// ── Map cleanup ─────────────────────────────────────────────────────

/**
 * Destroy and clean up map
 */
function destroyMap() {
  if (mapUpdateInterval) clearInterval(mapUpdateInterval);
  if (locateMarker) locateMarker = null;
  if (plbMap) {
    plbMap.remove();
    plbMap = null;
  }
  markers.clear();
  emergencyMarkers.clear();
}

// Initialize map when Leaflet is available and DOM is ready
function initMapWhenReady() {
  console.log('🗺️  initMapWhenReady() called');
  console.log('   Leaflet available:', typeof L !== 'undefined');
  
  if (typeof L === 'undefined') {
    console.log('⏳ Leaflet not available yet, retrying...');
    setTimeout(initMapWhenReady, 100);
    return;
  }

  const mapContainer = document.getElementById('plb-map-container');
  if (!mapContainer) {
    console.error('❌ Map container not found');
    return;
  }

  console.log('✓ Container found, initializing map in 50ms...');
  setTimeout(() => {
    try {
      initializeMap();
    } catch (err) {
      console.error('❌ Map init error:', err);
      console.error(err.stack);
    }
  }, 50);
}

// Console notification
console.log('🗺️  map.js loaded');

// Start initialization
if (document.readyState === 'loading') {
  console.log('⏳ Waiting for DOM...');
  document.addEventListener('DOMContentLoaded', () => {
    console.log('✓ DOM ready, starting map init');
    initMapWhenReady();
  });
} else {
  console.log('✓ DOM already ready, starting map init');
  initMapWhenReady();
}
