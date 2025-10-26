"use client";
// import FileUploader from "@/app/components/FileUploader";
// import Link from "next/link";

// export default function Home() {
//   return (
//     <main className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
//       <h1 className="text-4xl md:text-6xl font-bold mb-8 text-center">
//         AI Verification Hub
//       </h1>
//       <p className="text-lg md:text-xl mb-12 text-gray-300 text-center max-w-xl">
//         Detect deepfakes or fact-check information using cutting-edge AI models.
//       </p>
//       <div className="flex flex-col md:flex-row gap-6">
//         <Link href="/deepfake">
//           <button className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-xl text-lg font-semibold transition-all shadow-md hover:scale-105">
//             Deepfake Detection
//           </button>
//         </Link>

//         <Link href="/factcheck">
//           <button className="px-8 py-4 bg-green-600 hover:bg-green-700 rounded-xl text-lg font-semibold transition-all shadow-md hover:scale-105">
//             Fact Checking
//           </button>
//         </Link>
//       </div>
//       <FileUploader />
//     </main>
//   );
// }
import React, { useState, useEffect, useRef } from 'react';
import { Send, Image, Video, Type, Plus, MessageSquare, Loader2, X, ChevronLeft, Menu } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

export default function MultimodalAnalyzer() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [video, setVideo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);

  // Load chats from localStorage on mount
  useEffect(() => {
    const savedChats = localStorage.getItem('multimodal_chats');
    if (savedChats) {
      const parsedChats = JSON.parse(savedChats);
      setChats(parsedChats);
      if (parsedChats.length > 0) {
        setCurrentChatId(parsedChats[0].id);
        setMessages(parsedChats[0].messages);
      }
    }
  }, []);

  // Save chats to localStorage whenever they change
  useEffect(() => {
    if (chats.length > 0) {
      localStorage.setItem('multimodal_chats', JSON.stringify(chats));
    }
  }, [chats]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const createNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: 'New Analysis',
      messages: [],
      createdAt: new Date().toISOString(),
    };
    setChats([newChat, ...chats]);
    setCurrentChatId(newChat.id);
    setMessages([]);
    setText('');
    setImage(null);
    setVideo(null);
  };

  const switchChat = (chatId) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
      setText('');
      setImage(null);
      setVideo(null);
    }
  };

  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    const updatedChats = chats.filter(c => c.id !== chatId);
    setChats(updatedChats);
    if (currentChatId === chatId) {
      if (updatedChats.length > 0) {
        setCurrentChatId(updatedChats[0].id);
        setMessages(updatedChats[0].messages);
      } else {
        setCurrentChatId(null);
        setMessages([]);
      }
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
    }
  };

  const handleVideoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideo(file);
    }
  };

  const handleSubmit = async () => {
    if (!text && !image && !video) {
      alert('Please provide at least one input (text, image, or video)');
      return;
    }

    // Create user message
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      text: text || null,
      image: image ? URL.createObjectURL(image) : null,
      video: video ? URL.createObjectURL(video) : null,
      timestamp: new Date().toISOString(),
    };

    // If no current chat, create one
    let activeChatId = currentChatId;
    if (!activeChatId) {
      const newChat = {
        id: Date.now().toString(),
        title: text ? text.substring(0, 30) + '...' : 'New Analysis',
        messages: [],
        createdAt: new Date().toISOString(),
      };
      setChats([newChat, ...chats]);
      activeChatId = newChat.id;
      setCurrentChatId(activeChatId);
    }

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Prepare form data
    const formData = new FormData();
    if (text) formData.append('text', text);
    if (image) formData.append('image', image);
    if (video) formData.append('video', video);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // Create assistant message
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        data: data,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => {
        const updated = [...prev, assistantMessage];
        
        // Update chat in chats array
        setChats(prevChats => 
          prevChats.map(chat => 
            chat.id === activeChatId 
              ? { ...chat, messages: updated, title: chat.title === 'New Analysis' && text ? text.substring(0, 30) + '...' : chat.title }
              : chat
          )
        );
        
        return updated;
      });

    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        text: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setText('');
      setImage(null);
      setVideo(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (videoInputRef.current) videoInputRef.current.value = '';
    }
  };

  const formatResult = (data) => {
    if (!data || !data.results) return null;

    return (
      <div className="space-y-4">
        {data.combined && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Combined Analysis</h4>
            <p className="text-sm text-blue-800">{data.combined.short}</p>
            {data.combined.confidence_score !== undefined && (
              <p className="text-xs text-blue-600 mt-2">Confidence: {(data.combined.confidence_score * 100).toFixed(1)}%</p>
            )}
          </div>
        )}

        {data.results.bias && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-semibold text-purple-900 mb-2">Bias Analysis</h4>
            <p className="text-sm text-purple-800">Label: {data.results.bias.label}</p>
            <p className="text-xs text-purple-600">Score: {(data.results.bias.score * 100).toFixed(1)}%</p>
          </div>
        )}

        {data.results.ai_image && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-semibold text-green-900 mb-2">AI Image Detection</h4>
            <p className="text-sm text-green-800">Prediction: {data.results.ai_image.predicted_class}</p>
            <p className="text-xs text-green-600">Confidence: {(data.results.ai_image.confidence * 100).toFixed(1)}%</p>
          </div>
        )}

        {data.results.manipulated && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h4 className="font-semibold text-orange-900 mb-2">Manipulation Detection</h4>
            <p className="text-sm text-orange-800">Prediction: {data.results.manipulated.prediction}</p>
            <p className="text-xs text-orange-600">Confidence: {(data.results.manipulated.confidence * 100).toFixed(1)}%</p>
          </div>
        )}

        {data.results.video && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-semibold text-red-900 mb-2">Video Analysis</h4>
            {data.results.video.overall_verdict && (
              <>
                <p className="text-sm text-red-800">Verdict: {data.results.video.overall_verdict.verdict}</p>
                <p className="text-xs text-red-600">Risk Level: {data.results.video.overall_verdict.risk_level}</p>
              </>
            )}
          </div>
        )}

        {data.results.factcheck && data.results.factcheck.summary && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-yellow-900 mb-2">Fact Check</h4>
            <div className="text-sm text-yellow-800 space-y-1">
              {typeof data.results.factcheck.summary === 'object' ? (
                Object.entries(data.results.factcheck.summary).map(([key, value]) => (
                  <p key={key}><span className="font-medium">{key}:</span> {JSON.stringify(value)}</p>
                ))
              ) : (
                <p>{JSON.stringify(data.results.factcheck.summary)}</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} bg-gray-900 text-white transition-all duration-300 overflow-hidden flex flex-col`}>
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Chats</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-gray-800 rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>
        
        <button
          onClick={createNewChat}
          className="m-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-3 flex items-center justify-center gap-2 transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Chat
        </button>

        <div className="flex-1 overflow-y-auto">
          {chats.map(chat => (
            <div
              key={chat.id}
              onClick={() => switchChat(chat.id)}
              className={`p-3 mx-2 mb-2 rounded-lg cursor-pointer group flex items-center justify-between ${
                currentChatId === chat.id ? 'bg-gray-700' : 'hover:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm truncate">{chat.title}</span>
              </div>
              <button
                onClick={(e) => deleteChat(chat.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600 rounded transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className={`${sidebarOpen ? 'hidden' : 'block'} p-2 hover:bg-gray-100 rounded-lg`}
          >
            <Menu className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold text-gray-900">Multimodal Analysis</h1>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg font-medium">Start a new analysis</p>
                <p className="text-sm">Upload an image, video, or enter text to begin</p>
              </div>
            </div>
          )}

          {messages.map(message => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl ${message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'} rounded-lg p-4 shadow-sm`}>
                {message.type === 'user' && (
                  <div className="space-y-3">
                    {message.text && <p className="text-sm">{message.text}</p>}
                    {message.image && (
                      <img src={message.image} alt="Uploaded" className="rounded max-w-xs" />
                    )}
                    {message.video && (
                      <video src={message.video} controls className="rounded max-w-xs" />
                    )}
                  </div>
                )}
                {message.type === 'assistant' && formatResult(message.data)}
                {message.type === 'error' && (
                  <p className="text-sm text-red-600">{message.text}</p>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto space-y-3">
            {/* File Preview */}
            {(image || video) && (
              <div className="flex gap-2">
                {image && (
                  <div className="relative">
                    <img src={URL.createObjectURL(image)} alt="Preview" className="h-20 w-20 object-cover rounded border" />
                    <button
                      type="button"
                      onClick={() => setImage(null)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {video && (
                  <div className="relative">
                    <video src={URL.createObjectURL(video)} className="h-20 w-20 object-cover rounded border" />
                    <button
                      type="button"
                      onClick={() => setVideo(null)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Input Row */}
            <div className="flex gap-2">
              <input
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text for analysis..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={!!image}
                className={`p-3 rounded-lg border transition-colors ${
                  image 
                    ? 'bg-blue-100 border-blue-300 text-blue-600' 
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
                title="Upload Image"
              >
                <Image className="w-5 h-5" />
              </button>

              <input
                type="file"
                ref={videoInputRef}
                onChange={handleVideoSelect}
                accept="video/*"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => videoInputRef.current?.click()}
                disabled={!!video}
                className={`p-3 rounded-lg border transition-colors ${
                  video 
                    ? 'bg-blue-100 border-blue-300 text-blue-600' 
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
                title="Upload Video"
              >
                <Video className="w-5 h-5" />
              </button>

              <button
                onClick={handleSubmit}
                disabled={isLoading || (!text && !image && !video)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}