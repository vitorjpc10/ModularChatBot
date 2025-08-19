import React from "react"
import { Bot, User } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AgentWorkflowStep } from "@/types/api"
import { cn } from "@/lib/utils"

interface MessageBubbleProps {
  content: string
  isUser: boolean
  agent?: string
  agentWorkflow?: AgentWorkflowStep[]
  timestamp: Date
}

export function MessageBubble({
  content,
  isUser,
  agent,
  agentWorkflow,
  timestamp,
}: MessageBubbleProps) {
  const getAgentColor = (agentName: string) => {
    switch (agentName) {
      case "RouterAgent":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
      case "KnowledgeAgent":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      case "MathAgent":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
    }
  }

  return (
    <div className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </div>
        </div>
      )}

      <div className={cn("max-w-[70%]", isUser ? "order-first" : "")}>
        <Card
          className={cn(
            isUser ? "bg-primary text-primary-foreground" : "bg-card"
          )}
        >
          <CardContent className="p-3">
            <p className="text-sm whitespace-pre-wrap">{content}</p>
            {!isUser && agent && (
              <div className="mt-2 pt-2 border-t border-border/20">
                <Badge className={cn("text-xs", getAgentColor(agent))}>
                  {agent}
                </Badge>
                {agentWorkflow && agentWorkflow.length > 1 && (
                  <div className="mt-1 text-xs text-muted-foreground">
                    Workflow: {agentWorkflow.map((step) => step.agent).join(" → ")}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
        <p className="text-xs text-muted-foreground mt-1 px-1">
          {timestamp.toLocaleTimeString()}
        </p>
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-secondary-foreground" />
          </div>
        </div>
      )}
    </div>
  )
}
