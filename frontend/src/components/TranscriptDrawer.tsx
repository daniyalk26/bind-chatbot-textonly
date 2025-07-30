import React from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface TranscriptDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  messages: Message[];
}

export const TranscriptDrawer: React.FC<TranscriptDrawerProps> = ({
  isOpen,
  onClose,
  messages,
}) => {
  if (!isOpen) return null;

  const exportTranscript = () => {
    const transcript = messages
      .map(
        (m) => `[${m.timestamp.toLocaleString()}] ${m.role.toUpperCase()}: ${m.content}`
      )
      .join('\n\n');

    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* Drawer */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">Chat Transcript</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className="border-b pb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-xs font-semibold ${
                        message.role === 'user' ? 'text-blue-600' : 'text-gray-600'
                      }`}
                    >
                      {message.role.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800">{message.content}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t">
            <button
              onClick={exportTranscript}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Export Transcript
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
