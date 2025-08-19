export interface ChatRequest {
  message: string
  user_id: string
  conversation_id: string
}

export interface AgentWorkflowStep {
  agent: string
  decision?: string
  execution_time: number
}

export interface ChatResponse {
  response: string
  source_agent_response: string
  agent_workflow: AgentWorkflowStep[]
  conversation_id: string
  execution_time: number
}

export interface Conversation {
  conversation_id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface Message {
  id: string
  conversation_id: string
  content: string
  response: string
  source_agent: string
  source_agent_response: string
  agent_workflow: AgentWorkflowStep[]
  execution_time: number
  created_at: string
}

export interface ConversationCreate {
  conversation_id: string
  user_id: string
  title: string
}

export interface ConversationResponse {
  conversation_id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationStats {
  conversation_id: string
  total_messages: number
  average_response_time: number
  agent_usage: Record<string, number>
  created_at: string
  last_activity: string
}
