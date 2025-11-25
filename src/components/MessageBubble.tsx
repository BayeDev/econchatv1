'use client';

import { ChatMessage } from '@/lib/types';
import DataVisualization from './DataVisualization';
import { User, Bot, AlertCircle } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (message.isLoading) {
    return (
      <div className="flex gap-3 fade-in">
        <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <div className="bg-surface rounded-xl p-4 inline-block">
            <div className="flex gap-1">
              <span className="typing-dot w-2 h-2 bg-text-secondary rounded-full"></span>
              <span className="typing-dot w-2 h-2 bg-text-secondary rounded-full"></span>
              <span className="typing-dot w-2 h-2 bg-text-secondary rounded-full"></span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-surface-light' : 'bg-accent/20'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-text-secondary" />
        ) : (
          <Bot className="w-5 h-5 text-accent" />
        )}
      </div>

      <div className={`flex-1 ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`${isUser ? 'max-w-[80%]' : 'max-w-full'}`}>
          {/* Error message */}
          {message.error && (
            <div className="bg-error/10 border border-error/30 rounded-xl p-4 mb-3 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
              <p className="text-error">{message.error}</p>
            </div>
          )}

          {/* Message content */}
          <div className={`rounded-xl p-4 ${
            isUser ? 'bg-accent text-white' : 'bg-surface'
          }`}>
            <div className="message-content whitespace-pre-wrap">
              {message.content}
            </div>
          </div>

          {/* Data visualization - multiple indicators */}
          {message.multipleData && message.multipleData.length > 1 && message.multipleNarratives && (
            <div className="mt-4 space-y-4">
              {message.multipleData.map((data, index) => (
                <DataVisualization
                  key={data.indicator.code}
                  data={data}
                  narrative={message.multipleNarratives![index]}
                />
              ))}
            </div>
          )}

          {/* Data visualization - single indicator */}
          {message.data && message.narrative && (!message.multipleData || message.multipleData.length <= 1) && (
            <div className="mt-4">
              <DataVisualization data={message.data} narrative={message.narrative} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
