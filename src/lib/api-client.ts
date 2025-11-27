/**
 * EconChat API Client
 *
 * Client for communicating with the EconChat backend API.
 * Supports both REST and streaming (SSE) responses.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface ChatRequest {
  query: string;
  session_id?: string;
  stream?: boolean;
}

interface ChatResponse {
  message_id: string;
  content: string;
  data?: EconomicData;
  visualization?: VisualizationConfig;
  sources?: Source[];
  suggested_followups?: string[];
}

interface EconomicData {
  data: DataPoint[];
  indicator: {
    code: string;
    name: string;
    unit: string;
  };
  countries: Array<{
    name: string;
    iso3: string;
  }>;
  startYear: number;
  endYear: number;
  source: string;
  narrative?: NarrativeResponse;
}

interface DataPoint {
  country: string;
  countryCode: string;
  indicator: string;
  indicatorCode: string;
  year: number;
  value: number | null;
}

interface NarrativeResponse {
  summary: string;
  trend_description?: string;
  peer_comparison?: string;
  notable_flags: string[];
}

interface VisualizationConfig {
  chartType: 'line' | 'bar' | 'area' | 'scatter' | 'multi_line';
  title: string;
  xAxis: string;
  yAxis: string;
  legendPosition?: string;
  colorScheme?: string;
}

interface Source {
  type: string;
  title?: string;
  url?: string;
  indicator?: object;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  entities: {
    countries: Array<{ name: string; iso3: string }>;
    indicators: Array<{ code: string; name: string }>;
    time_periods: Array<{ start: number; end: number }>;
  };
}

interface StreamEvent {
  type: 'start' | 'thinking' | 'tool' | 'content' | 'visualization' | 'done' | 'error';
  content?: string;
  tool?: string;
  status?: string;
  data?: unknown;
  config?: VisualizationConfig;
  message?: string;
}

/**
 * Send a chat query to the backend.
 */
export async function sendQuery(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...request,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to send query');
  }

  return response.json();
}

/**
 * Send a chat query with streaming response.
 * Returns an async generator that yields events as they arrive.
 */
export async function* streamQuery(request: ChatRequest): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...request,
      stream: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to send query');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data) {
            try {
              const event: StreamEvent = JSON.parse(data);
              yield event;

              // Stop on done or error
              if (event.type === 'done' || event.type === 'error') {
                return;
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Create a new chat session.
 */
export async function createSession(title?: string, userId?: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, user_id: userId }),
  });

  if (!response.ok) {
    throw new Error('Failed to create session');
  }

  return response.json();
}

/**
 * List all sessions.
 */
export async function listSessions(userId?: string, limit = 20): Promise<{ sessions: Session[]; total: number }> {
  const params = new URLSearchParams();
  if (userId) params.set('user_id', userId);
  params.set('limit', limit.toString());

  const response = await fetch(`${API_BASE_URL}/sessions?${params}`);

  if (!response.ok) {
    throw new Error('Failed to list sessions');
  }

  return response.json();
}

/**
 * Get a specific session.
 */
export async function getSession(sessionId: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);

  if (!response.ok) {
    throw new Error('Failed to get session');
  }

  return response.json();
}

/**
 * Get messages for a session.
 */
export async function getSessionMessages(sessionId: string, limit = 50): Promise<{ messages: unknown[]; total: number }> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages?limit=${limit}`);

  if (!response.ok) {
    throw new Error('Failed to get session messages');
  }

  return response.json();
}

/**
 * Delete a session.
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
}

/**
 * Get context for a session.
 */
export async function getContext(sessionId: string): Promise<{
  session_id: string;
  entities: object;
  recent_queries: string[];
  preferences: object;
}> {
  const response = await fetch(`${API_BASE_URL}/chat/context/${sessionId}`);

  if (!response.ok) {
    throw new Error('Failed to get context');
  }

  return response.json();
}

/**
 * Submit feedback on a response.
 */
export async function submitFeedback(
  messageId: string,
  rating: number,
  comment?: string
): Promise<{ status: string }> {
  const params = new URLSearchParams({
    message_id: messageId,
    rating: rating.toString(),
  });
  if (comment) params.set('comment', comment);

  const response = await fetch(`${API_BASE_URL}/chat/feedback?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to submit feedback');
  }

  return response.json();
}

/**
 * Export data in various formats.
 */
export async function exportData(
  data: unknown,
  format: 'csv' | 'json' | 'markdown' = 'csv'
): Promise<Blob | object> {
  const response = await fetch(`${API_BASE_URL}/export/data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ data, format }),
  });

  if (!response.ok) {
    throw new Error('Failed to export data');
  }

  if (format === 'json') {
    return response.json();
  }

  return response.blob();
}

/**
 * Check if the backend API is available.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// Export types
export type {
  ChatRequest,
  ChatResponse,
  EconomicData,
  DataPoint,
  NarrativeResponse,
  VisualizationConfig,
  Source,
  Session,
  StreamEvent,
};
