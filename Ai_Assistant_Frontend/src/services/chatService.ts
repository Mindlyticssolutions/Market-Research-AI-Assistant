/**
 * Chat Service
 * Handles communication with backend chat endpoints
 * AI Assistant uses this for RAG/KAG-powered responses
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/chat';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp?: string;
  sources?: string[];
}

export interface ChatResponse {
  session_id: string;
  agent: string;
  response: string;
  timestamp: string;
  sources?: string[];
  plot?: string;
}

export interface ChatRequest {
  message: string;
  agent?: string;
  session_id?: string;
  context?: Record<string, unknown>;
}

// Session management
let currentSessionId: string | null = null;

export const chatService = {
  /**
   * Send a message to the AI Assistant
   * Returns the agent's response with optional RAG sources
   */
  sendMessage: async (message: string, agent: string = 'orchestrator'): Promise<ChatResponse> => {
    const response = await axios.post<ChatResponse>(`${API_BASE_URL}/send`, {
      message,
      agent,
      session_id: currentSessionId,
    });

    // Store session ID for conversation continuity
    currentSessionId = response.data.session_id;

    return response.data;
  },

  /**
   * Get chat history for current session
   */
  getHistory: async (): Promise<{ messages: ChatMessage[]; message_count: number }> => {
    if (!currentSessionId) {
      return { messages: [], message_count: 0 };
    }

    const response = await axios.get(`${API_BASE_URL}/history/${currentSessionId}`);
    return response.data;
  },

  /**
   * Clear chat history
   */
  clearHistory: async (): Promise<void> => {
    if (currentSessionId) {
      await axios.delete(`${API_BASE_URL}/history/${currentSessionId}`);
      currentSessionId = null;
    }
  },

  /**
   * Get current session ID
   */
  getSessionId: (): string | null => currentSessionId,

  /**
   * Reset session (start new conversation)
   */
  resetSession: (): void => {
    currentSessionId = null;
  },

  /**
   * Get WebSocket URL for streaming chat
   */
  getStreamUrl: (sessionId?: string): string => {
    const sid = sessionId || currentSessionId || crypto.randomUUID();
    return `ws://localhost:8000/api/v1/chat/ws/${sid}`;
  },
};
