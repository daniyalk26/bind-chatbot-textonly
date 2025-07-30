// frontend/src/components/ChatWindow.tsx
import React, { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { TranscriptDrawer } from './TranscriptDrawer';
import { WebSocketClient } from '../api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ConversationState {
  currentState: string;
  progress: number;
}

export const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationState, setConversationState] = useState<ConversationState>({
    currentState: 'start',
    progress: 0,
  });
  const [showTranscript, setShowTranscript] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsClient = useRef<WebSocketClient | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  useEffect(() => {
    wsClient.current = new WebSocketClient(
      (data) => {
        if (data.type === 'bot_message') {
          setIsTyping(false);
          const newMessage: Message = {
            id: `msg_${Date.now()}`,
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, newMessage]);
          
          if (data.data?.state) {
            setConversationState(prev => ({
              ...prev,
              currentState: data.data.state,
            }));
          }
        } else if (data.type === 'state_update') {
          setConversationState(data.data);
        }
      },
      () => setIsConnected(true),
      () => setIsConnected(false)
    );
    
    wsClient.current.connect();
    
    return () => {
      wsClient.current?.disconnect();
    };
  }, []);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const sendMessage = () => {
    if (!input.trim() || !isConnected) return;
    
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    wsClient.current?.send({
      type: 'user_message',
      content: input,
    });
    
    setInput('');
    inputRef.current?.focus();
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Insurance Onboarding</h1>
              <p className="text-sm text-gray-600 mt-1">
                {isConnected ? (
                  <span className="flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    Connected
                  </span>
                ) : (
                  <span className="flex items-center">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></span>
                    Connecting...
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowTranscript(true)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View Transcript
              </button>
              
              <div className="w-48">
                <div className="text-xs text-gray-600 mb-1">Progress: {conversationState.progress}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${conversationState.progress}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.map(message => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isTyping && (
            <div className="flex justify-start mb-4">
              <div className="flex items-end">
                <div className="mx-2">
                  <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-sm font-semibold">
                    B
                  </div>
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Input */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                conversationState.currentState === 'completed' 
                  ? 'Onboarding completed!' 
                  : 'Type your response...'
              }
              disabled={!isConnected || conversationState.currentState === 'completed'}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || !input.trim() || conversationState.currentState === 'completed'}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
      
      {/* Transcript Drawer */}
      <TranscriptDrawer
        isOpen={showTranscript}
        onClose={() => setShowTranscript(false)}
        messages={messages}
      />
    </div>
  );
};
