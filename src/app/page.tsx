'use client';

import { useRef, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import ChatInput from '@/components/ChatInput';
import MessageBubble from '@/components/MessageBubble';
import SuggestedQueries from '@/components/SuggestedQueries';
import QuickActions from '@/components/QuickActions';
import { Database, Trash2, Globe, TrendingUp, LineChart } from 'lucide-react';

export default function Home() {
  const { messages, isLoading, lastData, processQuery, clearMessages } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleQuerySubmit = (query: string) => {
    processQuery(query);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center">
              <LineChart className="w-6 h-6 text-accent" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-text-primary">EconChat</h1>
              <p className="text-xs text-text-secondary">Economic Data Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="btn btn-ghost text-sm"
                title="Clear conversation"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-5xl mx-auto h-full flex flex-col">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center space-y-8 text-center">
                <div className="space-y-4">
                  <div className="w-20 h-20 mx-auto rounded-2xl bg-accent/20 flex items-center justify-center">
                    <Globe className="w-10 h-10 text-accent" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-2">
                      Welcome to EconChat
                    </h2>
                    <p className="text-text-secondary max-w-md mx-auto">
                      Ask questions about any economic indicator. Get data, charts, and analyst-grade insights in seconds.
                    </p>
                  </div>
                </div>

                {/* Features */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl">
                  <div className="card text-left">
                    <Database className="w-8 h-8 text-accent mb-2" />
                    <h3 className="font-semibold text-text-primary mb-1">Authoritative Sources</h3>
                    <p className="text-sm text-text-secondary">
                      World Bank, OECD, FRED, and more
                    </p>
                  </div>
                  <div className="card text-left">
                    <TrendingUp className="w-8 h-8 text-success mb-2" />
                    <h3 className="font-semibold text-text-primary mb-1">Smart Analysis</h3>
                    <p className="text-sm text-text-secondary">
                      Trends, comparisons, and context
                    </p>
                  </div>
                  <div className="card text-left">
                    <LineChart className="w-8 h-8 text-warning mb-2" />
                    <h3 className="font-semibold text-text-primary mb-1">Visualizations</h3>
                    <p className="text-sm text-text-secondary">
                      Charts and tables, export-ready
                    </p>
                  </div>
                </div>

                {/* Suggested queries */}
                <div className="w-full max-w-2xl">
                  <SuggestedQueries onSelect={handleQuerySubmit} />
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Quick actions (when data available) */}
          {lastData && messages.length > 0 && !isLoading && (
            <div className="px-4 py-2 border-t border-border">
              <QuickActions currentData={lastData} onAction={handleQuerySubmit} />
            </div>
          )}

          {/* Input area */}
          <div className="border-t border-border bg-surface/50 backdrop-blur-lg p-4">
            <div className="max-w-3xl mx-auto">
              <ChatInput
                onSubmit={handleQuerySubmit}
                disabled={isLoading}
                placeholder="Ask about GDP, inflation, unemployment, trade, FDI, debt..."
              />
              <p className="text-xs text-text-secondary mt-2 text-center">
                Data from World Bank Open Data (CC BY 4.0). Press Enter to send.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
