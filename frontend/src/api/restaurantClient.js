const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9000';

class RestaurantClient {
  constructor() {
    this.baseUrl = API_URL;
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  async sendMessage(message, sessionId, messageHistory = [], customerName = 'Workshop User') {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          message_history: messageHistory,
          context: {
            session_id: sessionId,
            customer_name: customerName,
            message_count: messageHistory.length,
            current_order_id: null,
            current_reservation_id: null
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        success: false,
        error: error.message || 'Failed to send message'
      };
    }
  }

  async resetSession(sessionId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      return response.ok;
    } catch (error) {
      console.error('Error resetting session:', error);
      return false;
    }
  }
}

export default new RestaurantClient();