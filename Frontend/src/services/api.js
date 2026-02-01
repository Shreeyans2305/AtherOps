// API Service for AtherOps Backend
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Get system statistics
    async getStats() {
        return this.request('/stats');
    }

    // Get all tickets
    async getTickets() {
        return this.request('/api/tickets');
    }

    // Create a new ticket
    async createTicket(ticketData) {
        return this.request('/api/tickets', {
            method: 'POST',
            body: JSON.stringify(ticketData),
        });
    }

    // Update ticket status
    async updateTicketStatus(ticketId, status) {
        return this.request(`/api/tickets/${ticketId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    // Get a specific ticket
    async getTicket(ticketId) {
        return this.request(`/api/tickets/${ticketId}`);
    }

    // Get recent events timeline
    async getRecentEvents(hours = 24) {
        return this.request(`/api/recent-events?hours=${hours}`);
    }

    // Get agent activity status
    async getAgentActivity() {
        return this.request('/api/agent-activity');
    }
}

export default new ApiService();
