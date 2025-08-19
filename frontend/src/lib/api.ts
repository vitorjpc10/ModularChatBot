import {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationCreate,
  ConversationResponse,
  ConversationStats,
} from "@/types/api"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new ApiError(response.status, `API request failed: ${response.statusText}`)
  }

  return response.json()
}

// Chat API
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(request),
  })
}

// Conversation API
export async function createConversation(
  conversation: ConversationCreate
): Promise<ConversationResponse> {
  return apiRequest<ConversationResponse>("/conversations", {
    method: "POST",
    body: JSON.stringify(conversation),
  })
}

export async function getConversation(
  conversationId: string
): Promise<ConversationResponse> {
  return apiRequest<ConversationResponse>(`/conversations/${conversationId}`)
}

export async function getUserConversations(
  userId: string,
  limit: number = 50,
  offset: number = 0
): Promise<ConversationResponse[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  
  return apiRequest<ConversationResponse[]>(`/conversations/user/${userId}?${params}`)
}

export async function updateConversationTitle(
  conversationId: string,
  title: string
): Promise<ConversationResponse> {
  return apiRequest<ConversationResponse>(`/conversations/${conversationId}/title`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  })
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiRequest(`/conversations/${conversationId}`, {
    method: "DELETE",
  })
}

export async function getConversationStats(
  conversationId: string
): Promise<ConversationStats> {
  return apiRequest<ConversationStats>(`/conversations/${conversationId}/stats`)
}

// Messages API
export async function getConversationMessages(
  conversationId: string,
  limit: number = 50,
  offset: number = 0
): Promise<any[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  
  return apiRequest<any[]>(`/messages/conversation/${conversationId}?${params}`)
}

// Health check
export async function checkHealth(): Promise<{ status: string }> {
  return apiRequest<{ status: string }>("/health")
}
