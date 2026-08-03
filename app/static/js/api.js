const API = {
  async getNodes() {
    const res = await fetch('/api/nodes/');
    if (!res.ok) throw new Error('Failed to fetch nodes');
    return res.json();
  },

  async getEmergencies() {
    const res = await fetch('/api/emergencies/');
    if (!res.ok) throw new Error('Failed to fetch emergencies');
    return res.json();
  },

  async getStats() {
    const res = await fetch('/api/stats/dashboard');
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  async getGatewayStatus() {
    const res = await fetch('/api/gateway/status');
    if (!res.ok) throw new Error('Failed to fetch gateway status');
    return res.json();
  },

  async sendPacket(packetData) {
    const res = await fetch('/api/packets/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(packetData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to send packet');
    }
    return res.json();
  },

  async resolveEmergency(emergencyId, remarks) {
    const res = await fetch(`/api/emergencies/${emergencyId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ remarks })
    });
    if (!res.ok) throw new Error('Failed to resolve emergency');
    return res.json();
  },

  async sendStatusMessage(destinationNode, message) {
    const res = await fetch('/api/outbound/status-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination_node: destinationNode, message: message })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to send status message');
    }
    return res.json();
  },

  async broadcastHazard(message, latitude, longitude) {
    const res = await fetch('/api/outbound/hazard-broadcast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message, latitude: latitude, longitude: longitude })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to broadcast hazard');
    }
    return res.json();
  }
};
