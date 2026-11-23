/**
 * JBD Travels API Client Service
 */

const API_BASE = '/api';

const api = {
  getToken() {
    return localStorage.getItem('jbd_token');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('jbd_token', token);
    } else {
      localStorage.removeItem('jbd_token');
    }
  },

  getUser() {
    const userStr = localStorage.getItem('jbd_user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    if (user) {
      localStorage.setItem('jbd_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('jbd_user');
    }
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.message || `Request failed with status ${response.status}`);
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async register(userData) {
    const res = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    if (res.token) {
      this.setToken(res.token);
      this.setUser(res.user);
    }
    return res;
  },

  async login(emailOrUsername, password, role = null) {
    const payload = { email_or_username: emailOrUsername, password };
    if (role) payload.role = role;
    const res = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.token) {
      this.setToken(res.token);
      this.setUser(res.user);
    }
    return res;
  },

  logout() {
    this.setToken(null);
    this.setUser(null);
  },

  async getMe() {
    return await this.request('/auth/me');
  },

  // Destinations
  async getDestinations(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/destinations${query ? '?' + query : ''}`);
  },

  async getDestination(id) {
    return await this.request(`/destinations/${id}`);
  },

  // Recommendations
  async getAiRecommendations(data) {
    return await this.request('/recommendations/destinations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async generateItinerary(data) {
    return await this.request('/recommendations/itinerary', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // Flights
  async searchFlights(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/flights/search${query ? '?' + query : ''}`);
  },

  // Hotels
  async getHotels(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/hotels${query ? '?' + query : ''}`);
  },

  async getHotel(id) {
    return await this.request(`/hotels/${id}`);
  },

  // Travel Docs
  async checkTravelDocs(origin, destination) {
    const query = new URLSearchParams({ origin, destination }).toString();
    return await this.request(`/travel-docs/check?${query}`);
  },

  async getSupportedCountries() {
    return await this.request('/travel-docs/countries');
  },

  // Itineraries
  async getItineraries() {
    return await this.request('/itineraries');
  },

  async getItinerary(id) {
    return await this.request(`/itineraries/${id}`);
  },

  async saveItinerary(data) {
    return await this.request('/itineraries', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateItinerary(id, data) {
    return await this.request(`/itineraries/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async deleteItinerary(id) {
    return await this.request(`/itineraries/${id}`, {
      method: 'DELETE'
    });
  },

  async submitInquiry(id, data = {}) {
    return await this.request(`/itineraries/${id}/inquire`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // Admin & Management
  async getAdminDashboard() {
    return await this.request('/admin/dashboard');
  },

  async getAgentSummary() {
    return await this.request('/admin/agent-summary');
  },

  async getAdminHotels() {
    return await this.request('/admin/hotels');
  },

  async createAdminHotel(data) {
    return await this.request('/admin/hotels', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateAdminHotel(id, data) {
    return await this.request(`/admin/hotels/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async deleteAdminHotel(id) {
    return await this.request(`/admin/hotels/${id}`, {
      method: 'DELETE'
    });
  },

  async getAdminInquiries() {
    return await this.request('/admin/inquiries');
  },

  async updateAdminInquiry(id, data) {
    return await this.request(`/admin/inquiries/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async getAdminSettings() {
    return await this.request('/admin/settings');
  },

  async updateAdminSettings(data) {
    return await this.request('/admin/settings', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
};

window.api = api;
