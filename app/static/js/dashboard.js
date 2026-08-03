let currentResolvingId = null;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  setupWebSocket();
});

async function initDashboard() {
  await refreshStats();
  await refreshGatewayStatus();
  await refreshNodes();
  await refreshEmergencies();

  // Periodic polling fallback every 10s
  setInterval(async () => {
    await refreshStats();
    await refreshGatewayStatus();
    await refreshNodes();
    await refreshEmergencies();
  }, 10000);
}

async function refreshStats() {
  try {
    const stats = await API.getStats();
    document.getElementById('stat-total-nodes').textContent = stats.total_nodes;
    document.getElementById('stat-online-nodes').textContent = stats.online_nodes;
    document.getElementById('stat-offline-nodes').textContent = stats.offline_nodes;
    document.getElementById('stat-active-emergencies').textContent = stats.active_emergencies;
    document.getElementById('stat-deliv-confirmations').textContent = stats.delivery_confirmations_sent;
  } catch (err) {
    console.error('Stats update error:', err);
  }
}

async function refreshGatewayStatus() {
  try {
    const gw = await API.getGatewayStatus();
    document.getElementById('lora-freq').textContent = `${gw.frequency_mhz} MHz`;
    document.getElementById('lora-rssi').textContent = `${gw.current_rssi} dBm`;
    document.getElementById('lora-snr').textContent = `${gw.current_snr} dB`;
    document.getElementById('lora-rate').textContent = gw.packets_per_second;
    document.getElementById('lora-ack-rate').textContent = `${gw.ack_success_rate}%`;
    document.getElementById('lora-deliv-rate').textContent = `${gw.delivery_success_rate}%`;
  } catch (err) {
    console.error('Gateway status update error:', err);
  }
}

async function refreshNodes() {
  try {
    const nodes = await API.getNodes();
    const tbody = document.getElementById('nodes-table-body');
    if (!tbody) return;

    if (nodes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-secondary);">No wearable nodes registered yet. Send a Heartbeat or Emergency packet to register.</td></tr>`;
      return;
    }

    tbody.innerHTML = nodes.map(node => {
      const statusClass = node.status === 'ONLINE' ? 'badge-online' : (node.status === 'EMERGENCY' ? 'badge-emergency' : 'badge-offline');
      const battFillClass = node.battery < 20 ? 'battery-low' : (node.battery < 50 ? 'battery-medium' : '');
      const lastSeen = new Date(node.last_seen).toLocaleString();
      const gpsStr = (node.latitude !== null && node.longitude !== null) ? `${node.latitude.toFixed(4)}, ${node.longitude.toFixed(4)}` : 'N/A';
      const rfStr = (node.rssi !== null && node.snr !== null) ? `${node.rssi} dBm / ${node.snr} dB` : '-';
      const activeEmgBadge = node.current_emergency ? `<span class="badge badge-sos">${node.current_emergency}</span>` : '<span style="color: var(--accent-green);">NONE</span>';
      const packetTypeBadge = node.packet_type ? `<span class="badge badge-hb">${node.packet_type}</span>` : '-';

      return `
        <tr>
          <td><strong>${node.node_id}</strong></td>
          <td><span class="badge ${statusClass}"><span class="indicator ${node.status.toLowerCase()}"></span> ${node.status}</span></td>
          <td>
            <div class="battery-bar-bg"><div class="battery-bar-fill ${battFillClass}" style="width: ${node.battery}%"></div></div>
            ${node.battery}%
          </td>
          <td>${lastSeen}</td>
          <td>${gpsStr}</td>
          <td>${rfStr}</td>
          <td>${activeEmgBadge}</td>
          <td>${packetTypeBadge}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Nodes update error:', err);
  }
}

async function refreshEmergencies() {
  try {
    const emergencies = await API.getEmergencies();
    const tbody = document.getElementById('emergencies-table-body');
    if (!tbody) return;

    if (emergencies.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color: var(--text-secondary);">No emergency events recorded. System operating normally.</td></tr>`;
      return;
    }

    tbody.innerHTML = emergencies.map(emg => {
      const badgeClass = emg.event_type === 'SOS' ? 'badge-sos' : (emg.event_type === 'FALL' ? 'badge-fall' : 'badge-hazard');
      const gpsStr = (emg.latitude && emg.longitude) ? `${emg.latitude.toFixed(4)}, ${emg.longitude.toFixed(4)}` : 'N/A';
      const timestamp = new Date(emg.timestamp).toLocaleString();
      const vitalsStr = `HR: ${emg.heart_rate || '-'} | SpO2: ${emg.spo2 || '-'}% | Temp: ${emg.temperature || '-'}°C`;
      const batt = emg.battery ? `${emg.battery}%` : '-';

      const delivConfirmBadge = `<span class="badge badge-online">CONFIRMED VIA MESH</span>`;

      const resolveCol = emg.resolved
        ? `<span class="badge badge-online">RESOLVED</span>`
        : `<button class="btn btn-resolve" onclick="openResolveModal('${emg.emergency_id}')">Resolve</button>`;

      return `
        <tr>
          <td><span class="badge ${badgeClass}">${emg.event_type}</span></td>
          <td><strong>${emg.node_id}</strong></td>
          <td>${gpsStr}</td>
          <td>${timestamp}</td>
          <td>${batt}</td>
          <td><small>${vitalsStr}</small></td>
          <td>${emg.remarks || '-'}</td>
          <td>${delivConfirmBadge}</td>
          <td>${resolveCol}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Emergencies update error:', err);
  }
}

/* Operator Control Handlers */
async function submitStatusMessage() {
  const destNode = document.getElementById('outbound-dest-node').value.trim();
  const msgText = document.getElementById('outbound-msg-preset').value;

  if (!destNode) {
    alert('Please enter a Target Node ID.');
    return;
  }

  try {
    const res = await API.sendStatusMessage(destNode, msgText);
    alert(`Status Message Queued!\nID: ${res.message_id}\nTarget: ${destNode}\nMessage: ${msgText}`);
  } catch (err) {
    alert('Failed to send status message: ' + err.message);
  }
}

async function submitHazardBroadcast() {
  const msgText = document.getElementById('hazard-msg').value.trim();
  const lat = parseFloat(document.getElementById('hazard-lat').value);
  const lng = parseFloat(document.getElementById('hazard-lng').value);

  if (!msgText) {
    alert('Please enter a Hazard description.');
    return;
  }

  try {
    const res = await API.broadcastHazard(msgText, lat, lng);
    alert(`Hazard Alert Broadcast Queued!\nID: ${res.message_id}\nMessage: ${msgText}`);
  } catch (err) {
    alert('Failed to broadcast hazard: ' + err.message);
  }
}

/* Modal for Emergency Resolution */
function openResolveModal(emergencyId) {
  currentResolvingId = emergencyId;
  document.getElementById('modal-emergency-id').textContent = emergencyId;
  document.getElementById('resolve-remarks').value = '';
  document.getElementById('resolve-modal').classList.add('active');
}

function closeResolveModal() {
  document.getElementById('resolve-modal').classList.remove('active');
  currentResolvingId = null;
}

async function submitResolve() {
  const remarks = document.getElementById('resolve-remarks').value.trim();
  if (!remarks) {
    alert('Please enter resolution remarks.');
    return;
  }

  try {
    await API.resolveEmergency(currentResolvingId, remarks);
    closeResolveModal();
    await refreshStats();
    await refreshNodes();
    await refreshEmergencies();
  } catch (err) {
    alert('Failed to resolve emergency: ' + err.message);
  }
}

/* Modal for Packet Simulation */
function openSimulateModal() {
  fillPreset('HEARTBEAT');
  document.getElementById('simulate-modal').classList.add('active');
}

function closeSimulateModal() {
  document.getElementById('simulate-modal').classList.remove('active');
}

function toggleEmergencyFields() {
  const pType = document.getElementById('sim-packet-type').value;
  const fields = document.getElementById('sim-emergency-fields');
  if (pType === 'HEARTBEAT') {
    fields.style.display = 'none';
  } else {
    fields.style.display = 'block';
  }
}

function fillPreset(type) {
  const randNum = Math.floor(Math.random() * 9000) + 1000;
  const nodeNum = Math.floor(Math.random() * 5) + 1;
  const node_id = `NODE_0${nodeNum}`;

  document.getElementById('sim-packet-type').value = type;
  document.getElementById('sim-node-id').value = node_id;
  document.getElementById('sim-battery').value = Math.floor(Math.random() * 40) + 60;
  toggleEmergencyFields();

  if (type === 'HEARTBEAT') {
    document.getElementById('sim-packet-id').value = `HB-${randNum}`;
  } else {
    document.getElementById('sim-packet-id').value = `PKT-${randNum}`;
    document.getElementById('sim-latitude').value = (21.14 + (Math.random() * 0.05)).toFixed(4);
    document.getElementById('sim-longitude').value = (79.08 + (Math.random() * 0.05)).toFixed(4);
    document.getElementById('sim-hr').value = type === 'SOS' ? 145 : (type === 'FALL' ? 128 : 110);
    document.getElementById('sim-spo2').value = Math.floor(Math.random() * 6) + 92;
    document.getElementById('sim-temp').value = (37.0 + Math.random() * 2.5).toFixed(1);
  }
}

async function submitSimulatedPacket() {
  const pType = document.getElementById('sim-packet-type').value;
  const packetId = document.getElementById('sim-packet-id').value.trim();
  const nodeId = document.getElementById('sim-node-id').value.trim();
  const battery = parseFloat(document.getElementById('sim-battery').value);

  if (!packetId || !nodeId) {
    alert('Please enter Packet ID and Node ID.');
    return;
  }

  const payload = {
    packet_id: packetId,
    node_id: nodeId,
    source_node_id: nodeId,
    previous_hop_id: nodeId,
    destination_id: 'GATEWAY',
    packet_type: pType,
    battery: battery
  };

  if (pType !== 'HEARTBEAT') {
    payload.emergency_id = `EMG-${nodeId}-${packetId}`;
    payload.sequence_number = 1;
    payload.latitude = parseFloat(document.getElementById('sim-latitude').value);
    payload.longitude = parseFloat(document.getElementById('sim-longitude').value);
    payload.heart_rate = parseInt(document.getElementById('sim-hr').value);
    payload.spo2 = parseFloat(document.getElementById('sim-spo2').value);
    payload.temperature = parseFloat(document.getElementById('sim-temp').value);
    payload.sos = pType === 'SOS';
    payload.fall_detected = pType === 'FALL';
  }

  try {
    const res = await API.sendPacket(payload);
    closeSimulateModal();
    alert(`Success! Packet processed by Gateway.\nMessage: ${res.message}`);
    await refreshStats();
    await refreshNodes();
    await refreshEmergencies();
  } catch (err) {
    alert('Error sending packet: ' + err.message);
  }
}

function setupWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

  const socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connected to gateway.');
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      console.log('WebSocket message received:', msg);
      refreshStats();
      refreshGatewayStatus();
      refreshNodes();
      refreshEmergencies();
    } catch (e) {
      console.error('Error parsing WS message:', e);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket connection closed. Reconnecting in 5s...');
    setTimeout(setupWebSocket, 5000);
  };
}
