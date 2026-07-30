import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2 } from 'lucide-react';

export default function ChatInterface({ documentId }) {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! I can answer questions about this document. What would you like to know?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { id: Date.now(), role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Based on my analysis of this document, here's what I found regarding "${userMsg.content}": The document contains relevant information that matches your query. Please note that this is a demo response - connect to the backend API for real AI-powered answers.`,
      };
      setMessages((prev) => [...prev, aiMsg]);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-[400px] border border-gray-200 dark:border-dark-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-bg">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-saffron-500" />
          <h3 className="text-sm font-semibold">AI Document Assistant</h3>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-primary-500 text-white rounded-br-md'
                  : 'bg-gray-100 dark:bg-dark-bg text-gray-700 dark:text-dark-text rounded-bl-md'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-saffron-500 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 dark:bg-dark-bg rounded-2xl rounded-bl-md px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 border-t border-gray-200 dark:border-dark-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about this document..."
            className="flex-1 px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-bg text-sm outline-none focus:ring-2 focus:ring-primary-500/20"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="p-2 rounded-lg bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
