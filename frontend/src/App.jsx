import React, { useState, useEffect, useRef, useCallback } from 'react';
import restaurantClient from './api/restaurantClient';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`session-${Date.now()}`);
  const [isConnected, setIsConnected] = useState(false);
  const [toolCalls, setToolCalls] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [currentOrderId, setCurrentOrderId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Check API connection
    const checkConnection = async () => {
      const healthy = await restaurantClient.checkHealth();
      setIsConnected(healthy);
    };
    checkConnection();

    // Add welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome to our restaurant! I can help you browse our menu, place orders, make reservations, and more. How can I assist you today?',
      timestamp: new Date().toISOString()
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Poll for order status updates
  useEffect(() => {
    if (!currentOrderId) return;

    const pollOrderStatus = async () => {
      try {
        const response = await fetch(`http://localhost:9000/api/orders/recent?session_id=${sessionId}`);
        const data = await response.json();

        const myOrder = data.orders?.find(o => o.id === currentOrderId);
        if (myOrder && myOrder.status === 'ready') {
          // Show notification
          setNotifications(prev => [...prev, {
            id: Date.now(),
            message: `🎉 Your order ${currentOrderId} is ready!`,
            type: 'success'
          }]);
          setCurrentOrderId(null); // Stop polling
        }
      } catch (error) {
        console.error('Error polling order status:', error);
      }
    };

    const interval = setInterval(pollOrderStatus, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, [currentOrderId, sessionId]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    // Prepare message history for context
    const messageHistory = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content,
      timestamp: msg.timestamp
    }));

    // Send to backend with history
    const response = await restaurantClient.sendMessage(
      inputMessage,
      sessionId,
      messageHistory
    );

    setIsTyping(false);
    setIsLoading(false);

    if (response.success && response.response) {
      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.metadata
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Extract tool calls if present
      if (response.metadata?.tool_calls) {
        setToolCalls(prev => [...response.metadata.tool_calls, ...prev]);

        // Check if place_order was called
        const orderPlaced = response.metadata.tool_calls.find(tc => tc.name === 'place_order');
        if (orderPlaced && orderPlaced.result) {
          // Extract order ID from result
          const match = orderPlaced.result.match(/ORD-[A-Z0-9]+/);
          if (match) {
            setCurrentOrderId(match[0]);
            logger.info(`Tracking order: ${match[0]}`);
          }
        }
      }
    } else {
      const errorMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [inputMessage, isLoading, messages, sessionId]);

  const handleQuickAction = useCallback(async (message) => {
    if (isLoading) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsTyping(true);

    const messageHistory = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content,
      timestamp: msg.timestamp
    }));

    const response = await restaurantClient.sendMessage(
      message,
      sessionId,
      messageHistory
    );

    setIsTyping(false);
    setIsLoading(false);

    if (response.success && response.response) {
      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.metadata
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (response.metadata?.tool_calls) {
        setToolCalls(prev => [...response.metadata.tool_calls, ...prev]);
      }
    } else {
      const errorMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [isLoading, messages, sessionId]);

  const QuickAction = useCallback(({ text, message }) => (
    <button
      onClick={() => handleQuickAction(message)}
      disabled={isLoading}
      className="px-3 py-1 bg-white/50 hover:bg-white/70 rounded-full text-sm text-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {text}
    </button>
  ), [handleQuickAction, isLoading]);

  const Message = useCallback(({ message }) => {
    const isUser = message.role === 'user';
    return (
      <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
        {!isUser && (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
            AI
          </div>
        )}
        <div className={`message-bubble ${
          isUser
            ? 'bg-blue-500 text-white'
            : message.isError
              ? 'bg-red-100 text-red-800'
              : 'bg-gray-100 text-gray-800'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.metadata?.tool_calls && (
            <div className="mt-2 pt-2 border-t border-gray-300">
              <span className="text-xs opacity-70">
                🔧 Used {message.metadata.tool_calls.length} tool{message.metadata.tool_calls.length > 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
        {isUser && (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-green-500 flex items-center justify-center text-white text-sm font-bold">
            U
          </div>
        )}
      </div>
    );
  }, []);

  const TypingIndicator = useCallback(() => (
    <div className="flex gap-3 justify-start animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
        AI
      </div>
      <div className="message-bubble bg-gray-100">
        <div className="flex gap-1 p-2">
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
        </div>
      </div>
    </div>
  ), []);

  const ToolCallPanel = useCallback(() => (
    <div className="glass-morphism rounded-2xl p-4 h-full">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">
        🔧 Tool Calls
      </h3>
      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {toolCalls.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            Tool calls will appear here when the agent uses tools
          </p>
        ) : (
          toolCalls.map((tool, index) => (
            <div key={index} className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg p-3 text-sm">
              <div className="font-semibold mb-1">📦 {tool.name}</div>
              <details className="cursor-pointer">
                <summary className="text-xs opacity-90">View details</summary>
                <div className="mt-2 bg-black/20 rounded p-2 text-xs">
                  <div className="mb-2">
                    <span className="font-semibold">Arguments:</span>
                    <pre className="mt-1 overflow-x-auto">
                      {JSON.stringify(tool.arguments, null, 2)}
                    </pre>
                  </div>
                  {tool.result && (
                    <div>
                      <span className="font-semibold">Result:</span>
                      <pre className="mt-1 overflow-x-auto">
                        {typeof tool.result === 'string'
                          ? tool.result.substring(0, 200)
                          : JSON.stringify(tool.result, null, 2).substring(0, 200)}
                        {tool.result.length > 200 ? '...' : ''}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            </div>
          ))
        )}
      </div>
    </div>
  ), [toolCalls]);

  // Toast notification component
  const ToastNotifications = useCallback(() => (
    <div className="fixed top-4 right-4 space-y-2 z-50">
      {notifications.map(notif => (
        <div
          key={notif.id}
          className="glass-morphism rounded-lg p-4 shadow-2xl animate-slide-down min-w-[300px]"
          style={{ animation: 'slideDown 0.3s ease-out' }}
        >
          <div className="flex items-center justify-between">
            <span className="text-gray-800 font-medium">{notif.message}</span>
            <button
              onClick={() => setNotifications(prev => prev.filter(n => n.id !== notif.id))}
              className="ml-4 text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  ), [notifications]);

  return (
    <div className="min-h-screen p-4">
      <ToastNotifications />
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="glass-morphism rounded-2xl p-6 mb-4">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            🍕 Restaurant AI Agent
          </h1>
          <p className="text-gray-600">
            DevFest Pakistan 2025 - Production-Ready AI with Gemini & LangChain
          </p>
          <div className="flex gap-2 mt-4">
            <span className={`px-3 py-1 rounded-full text-sm ${
              isConnected
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {isConnected ? '● Connected' : '○ Disconnected'}
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Gemini 2.0
            </span>
            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
              Session: {sessionId.substring(0, 15)}...
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="glass-morphism rounded-2xl h-[600px] flex flex-col">
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map(message => (
                  <Message key={message.id} message={message} />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-white/20 p-4">
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type your message..."
                    className="flex-1 px-4 py-2 bg-white/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || !inputMessage.trim()}
                    className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Sending...' : 'Send'}
                  </button>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <QuickAction
                    text="🥗 Show vegetarian options"
                    message="What vegetarian options do you have?"
                  />
                  <QuickAction
                    text="🌱 Vegan menu"
                    message="Show me your vegan dishes"
                  />
                  <QuickAction
                    text="📦 Place order"
                    message="I'd like to place an order"
                  />
                  <QuickAction
                    text="📅 Make reservation"
                    message="I want to make a reservation for 4 people"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Tool Calls Panel */}
          <div className="lg:col-span-1">
            <ToolCallPanel />
          </div>
        </div>

        {/* Info Bar */}
        <div className="glass-morphism rounded-2xl p-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-800">Workshop Demo</h3>
              <p className="text-sm text-gray-600">
                This agent uses LangChain's create_agent with Gemini for reasoning and tool execution
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-white/50 hover:bg-white/70 text-gray-700 rounded-lg transition-colors"
            >
              Reset Chat
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;