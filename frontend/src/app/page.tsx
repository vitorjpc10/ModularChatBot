"use client"

import React, { useRef, useEffect } from "react"
import { Bot } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble } from "@/components/chat/MessageBubble"
import { LoadingMessage } from "@/components/chat/LoadingMessage"
import { ConversationSidebar } from "@/components/chat/ConversationSidebar"
import { ChatInput } from "@/components/chat/ChatInput"
import { useChat } from "@/hooks/useChat"

export default function ChatPage() {
  const {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    error,
    sendMessage,
    createNewConversation,
    selectConversation,
    deleteConversation,
  } = useChat("default-user")

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [inputMessage, setInputMessage] = React.useState("")

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return
    
    await sendMessage(inputMessage)
    setInputMessage("")
  }

  const activeConversation = conversations.find(
    (c) => c.conversation_id === activeConversationId
  )

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onConversationSelect={selectConversation}
        onNewConversation={createNewConversation}
        onDeleteConversation={deleteConversation}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border p-6">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-montserrat font-black text-foreground mb-2">
              Modular AI Chatbot System
            </h1>
            <p className="text-muted-foreground">
              Intelligent routing between specialized agents:{" "}
              <strong>RouterAgent</strong> for decision making,{" "}
              <strong>KnowledgeAgent</strong> for information retrieval, and{" "}
              <strong>MathAgent</strong> for calculations.
            </p>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-montserrat font-semibold text-foreground mb-2">
                  Start a conversation
                </h3>
                <p className="text-muted-foreground">
                  Ask me about fees, calculations, or general questions!
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  content={message.content}
                  isUser={message.isUser}
                  agent={message.agent}
                  agentWorkflow={message.agentWorkflow}
                  timestamp={message.timestamp}
                />
              ))
            )}
            {isLoading && <LoadingMessage />}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 p-4 mx-4 mb-4 rounded-md">
            <p className="text-destructive text-sm">{error}</p>
          </div>
        )}

        {/* Input Area */}
        <ChatInput
          value={inputMessage}
          onChange={setInputMessage}
          onSend={handleSendMessage}
          disabled={isLoading || !activeConversationId}
        />
      </div>
    </div>
  )
}
