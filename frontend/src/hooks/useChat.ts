import { useState, useCallback, useEffect } from "react"
import {
  ChatRequest,
  ChatResponse,
  ConversationResponse,
  ConversationCreate,
  AgentWorkflowStep,
} from "@/types/api"
import {
  sendChatMessage,
  createConversation,
  getUserConversations,
  deleteConversation,
  updateConversationTitle,
} from "@/lib/api"

interface Message {
  id: string
  content: string
  isUser: boolean
  agent?: string
  agentWorkflow?: AgentWorkflowStep[]
  timestamp: Date
}

interface UseChatReturn {
  messages: Message[]
  conversations: ConversationResponse[]
  activeConversationId: string
  isLoading: boolean
  error: string | null
  sendMessage: (content: string) => Promise<void>
  createNewConversation: () => Promise<void>
  selectConversation: (conversationId: string) => void
  deleteConversation: (conversationId: string) => Promise<void>
  updateConversationTitle: (conversationId: string, title: string) => Promise<void>
  loadConversations: () => Promise<void>
}

export function useChat(userId: string = "default-user"): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadConversations = useCallback(async () => {
    try {
      const userConversations = await getUserConversations(userId)
      setConversations(userConversations)
      
      // Set active conversation to the most recent one
      if (userConversations.length > 0 && !activeConversationId) {
        setActiveConversationId(userConversations[0].conversation_id)
      }
    } catch (err) {
      setError("Failed to load conversations")
      console.error("Error loading conversations:", err)
    }
  }, [userId, activeConversationId])

  const createNewConversation = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const newConversationId = `conv-${Date.now()}`
      const conversationData: ConversationCreate = {
        conversation_id: newConversationId,
        user_id: userId,
        title: "New Conversation",
      }
      
      const newConversation = await createConversation(conversationData)
      
      setConversations((prev) => [newConversation, ...prev])
      setActiveConversationId(newConversationId)
      setMessages([])
    } catch (err) {
      setError("Failed to create new conversation")
      console.error("Error creating conversation:", err)
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !activeConversationId) return

    try {
      setIsLoading(true)
      setError(null)

      // Add user message immediately
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        content: content.trim(),
        isUser: true,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage])

      // Send to API
      const request: ChatRequest = {
        message: content.trim(),
        user_id: userId,
        conversation_id: activeConversationId,
      }

      const response: ChatResponse = await sendChatMessage(request)

      // Add bot response
      const botMessage: Message = {
        id: `msg-${Date.now()}-bot`,
        content: response.response,
        isUser: false,
        agent: response.agent_workflow?.[response.agent_workflow.length - 1]?.agent,
        agentWorkflow: response.agent_workflow,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, botMessage])

      // Update conversation title if this is the first message
      if (messages.length === 0) {
        const title = content.length > 30 ? content.substring(0, 30) + "..." : content
        await updateConversationTitle(activeConversationId, title)
        
        // Update local state
        setConversations((prev) =>
          prev.map((conv) =>
            conv.conversation_id === activeConversationId
              ? { ...conv, title }
              : conv
          )
        )
      }

      // Refresh conversations to update message count
      await loadConversations()
    } catch (err) {
      setError("Failed to send message")
      console.error("Error sending message:", err)
      
      // Add error message
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        content: "Sorry, I encountered an error processing your request. Please try again.",
        isUser: false,
        agent: "ErrorHandler",
        timestamp: new Date(),
      }
      
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [activeConversationId, userId, messages.length, loadConversations])

  const selectConversation = useCallback((conversationId: string) => {
    setActiveConversationId(conversationId)
    setMessages([]) // Clear messages - in a real app, you'd load them from the API
    setError(null)
  }, [])

  const deleteConversationHandler = useCallback(async (conversationId: string) => {
    try {
      await deleteConversation(conversationId)
      
      setConversations((prev) =>
        prev.filter((conv) => conv.conversation_id !== conversationId)
      )
      
      // If we deleted the active conversation, select the first available one
      if (conversationId === activeConversationId) {
        const remainingConversations = conversations.filter(
          (conv) => conv.conversation_id !== conversationId
        )
        
        if (remainingConversations.length > 0) {
          setActiveConversationId(remainingConversations[0].conversation_id)
        } else {
          setActiveConversationId("")
          setMessages([])
        }
      }
    } catch (err) {
      setError("Failed to delete conversation")
      console.error("Error deleting conversation:", err)
    }
  }, [activeConversationId, conversations])

  const updateConversationTitleHandler = useCallback(async (
    conversationId: string,
    title: string
  ) => {
    try {
      const updatedConversation = await updateConversationTitle(conversationId, title)
      
      setConversations((prev) =>
        prev.map((conv) =>
          conv.conversation_id === conversationId ? updatedConversation : conv
        )
      )
    } catch (err) {
      setError("Failed to update conversation title")
      console.error("Error updating conversation title:", err)
    }
  }, [])

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  return {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    error,
    sendMessage,
    createNewConversation,
    selectConversation,
    deleteConversation: deleteConversationHandler,
    updateConversationTitle: updateConversationTitleHandler,
    loadConversations,
  }
}
