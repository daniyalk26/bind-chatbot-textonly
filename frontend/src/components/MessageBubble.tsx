import React from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}>
      <div className={`flex items-end max-w-[70%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`mx-2 ${isUser ? 'order-2' : 'order-1'}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-semibold ${
              isUser ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            {isUser ? 'U' : 'B'}
          </div>
        </div>

        {/* Bubble */}
        <div
          className={`px-4 py-2 rounded-2xl ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : 'bg-gray-100 text-gray-800 rounded-bl-sm'
          } ${isUser ? 'order-1' : 'order-2'}`}
        >
          <p className="text-sm leading-relaxed">{message.content}</p>
          <span
            className={`text-xs mt-1 block ${isUser ? 'text-blue-100' : 'text-gray-500'}`}
          >
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
