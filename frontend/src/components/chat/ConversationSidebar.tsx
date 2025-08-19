import React from "react"
import { Plus, MessageSquare, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ConversationResponse } from "@/types/api"
import { cn } from "@/lib/utils"

interface ConversationSidebarProps {
  conversations: ConversationResponse[]
  activeConversationId: string
  onConversationSelect: (conversationId: string) => void
  onNewConversation: () => void
  onDeleteConversation: (conversationId: string) => void
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onConversationSelect,
  onNewConversation,
  onDeleteConversation,
}: ConversationSidebarProps) {
  return (
    <div className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-montserrat font-bold text-sidebar-foreground">
            Conversations
          </h2>
          <Button
            onClick={onNewConversation}
            size="sm"
            className="bg-sidebar-primary hover:bg-sidebar-primary/90 text-sidebar-primary-foreground"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2">
          {conversations.map((conversation) => (
            <Card
              key={conversation.conversation_id}
              className={cn(
                "mb-2 cursor-pointer transition-colors group",
                conversation.conversation_id === activeConversationId
                  ? "bg-sidebar-accent border-sidebar-primary"
                  : "hover:bg-sidebar-accent/50"
              )}
              onClick={() => onConversationSelect(conversation.conversation_id)}
            >
              <CardContent className="p-3">
                <div className="flex items-start gap-2">
                  <MessageSquare className="h-4 w-4 mt-1 text-sidebar-foreground/60" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-sidebar-foreground truncate">
                      {conversation.title}
                    </p>
                    <p className="text-xs text-sidebar-foreground/60">
                      {conversation.message_count} messages
                    </p>
                    <p className="text-xs text-sidebar-foreground/40">
                      {new Date(conversation.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-sidebar-foreground/60 hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteConversation(conversation.conversation_id)
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
