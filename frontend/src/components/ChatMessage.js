import React from 'react';
import { User, Bot } from 'lucide-react';
import { cn } from '../utils/cn';

const ChatMessage = ({ message, isTyping = false }) => {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      "flex items-start space-x-3 mb-4 animate-slide-up",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
          <Bot className="w-5 h-5 text-primary-600" />
        </div>
      )}
      
      <div className={cn(
        "flex flex-col max-w-xs lg:max-w-md",
        isUser && "items-end"
      )}>
        <div className={cn(
          "message-bubble",
          isUser ? "message-user" : "message-assistant"
        )}>
          {isTyping ? (
            <div className="flex items-center space-x-1">
              <span>AI is typing</span>
              <div className="loading-dots"></div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
          )}
        </div>
        
        <div className={cn(
          "text-xs text-gray-500 mt-1",
          isUser ? "text-right" : "text-left"
        )}>
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage; 