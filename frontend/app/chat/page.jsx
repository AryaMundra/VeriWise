"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Send, Image, Video, X, ChevronLeft, Menu, Plus, MessageSquare, Loader2 } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

// LayoutTextFlip Component
function LayoutTextFlip({ text, words }) {
  const [currentWord, setCurrentWord] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentWord((prev) => (prev + 1) % words.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [words]);

  return (
    <div className="text-4xl font-bold">
      <span className="text-white">{text}</span>
      <span className="ml-2 text-indigo-400">
        {words[currentWord]}
      </span>
    </div>
  );
}

export default function MultimodalAnalyzer() {
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [video, setVideo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentPlaceholder, setCurrentPlaceholder] = useState(0);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const textareaRef = useRef(null);

  const placeholders = [
    "Enter text for analysis...",
    "Analyze media authenticity...",
    "Detect deepfakes and verify content...",
    "Check facts and sources..."
  ];

  // Rotate placeholders
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentPlaceholder((prev) => (prev + 1) % placeholders.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (!text && !image && !video) return;

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
      // --- Integrated fetch with robust error handling ---
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      // Check for non-OK responses
      if (!response.ok) {
        let errBody = null;
        try {
          errBody = await response.json();
        } catch (e) {
          errBody = { error: `HTTP ${response.status}` };
        }

        const errorMessage = {
          id: (Date.now() + 1).toString(),
          type: 'error',
          text: `Server error: ${JSON.stringify(errBody)}`,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }

      // --- Success case ---
      const data = await response.json();
console.log("SUMMARY FOUND:", data.results.summary);

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        data: data,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => {
        const updated = [...prev, assistantMessage];
        setChats(prevChats =>
          prevChats.map(chat =>
            chat.id === activeChatId
              ? {
                ...chat,
                messages: updated,
                title:
                  chat.title === 'New Analysis' && text
                    ? text.substring(0, 30) + '...'
                    : chat.title,
              }
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


  // const formatResult = (data) => {
  //   if (!data || !data.results) return null;

  //   return (
  //     <div className="space-y-4">
  //       {data.combined && (
  //         <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-blue-300 mb-2">Combined Analysis</h4>
  //           <p className="text-sm text-blue-200">{data.combined.short}</p>
  //           {data.combined.confidence_score !== undefined && (
  //             <p className="text-xs text-blue-400 mt-2">Confidence: {(data.combined.confidence_score * 100).toFixed(1)}%</p>
  //           )}
  //         </div>
  //       )}

  //       {data.results.bias && (
  //         <div className="bg-purple-900/30 border border-purple-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-purple-300 mb-2">Bias Analysis</h4>
  //           <p className="text-sm text-purple-200">Label: {data.results.bias.label}</p>
  //           <p className="text-xs text-purple-400">Score: {(data.results.bias.score * 100).toFixed(1)}%</p>
  //         </div>
  //       )}

  //       {data.results.ai_image && (
  //         <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-green-300 mb-2">AI Image Detection</h4>
  //           <p className="text-sm text-green-200">Prediction: {data.results.ai_image.predicted_class}</p>
  //           <p className="text-xs text-green-400">Confidence: {(data.results.ai_image.confidence * 100).toFixed(1)}%</p>
  //         </div>
  //       )}

  //       {data.results.manipulated && (
  //         <div className="bg-orange-900/30 border border-orange-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-orange-300 mb-2">Manipulation Detection</h4>
  //           <p className="text-sm text-orange-200">Prediction: {data.results.manipulated.prediction}</p>
  //           <p className="text-xs text-orange-400">Confidence: {(data.results.manipulated.confidence * 100).toFixed(1)}%</p>
  //         </div>
  //       )}

  //       {(data.results.video || data.results.video_analysis || data.results.video_result) && (
  //         <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-red-300 mb-2">Video Analysis</h4>
  //           {(
  //             data.results.video?.overall_verdict ||
  //             data.results.video_analysis?.overall_verdict ||
  //             data.results.video_result?.overall_verdict
  //           ) && (
  //               <>
  //                 <p className="text-sm text-red-200">
  //                   Verdict: {
  //                     data.results.video?.overall_verdict.verdict ||
  //                     data.results.video_analysis?.overall_verdict.verdict ||
  //                     data.results.video_result?.overall_verdict.verdict
  //                   }
  //                 </p>

  //                 <p className="text-xs text-red-400">
  //                   Risk Level: {
  //                     data.results.video?.overall_verdict.risk_level ||
  //                     data.results.video_analysis?.overall_verdict.risk_level ||
  //                     data.results.video_result?.overall_verdict.risk_level
  //                   }
  //                 </p>
  //               </>
  //             )}
  //         </div>
  //       )}


  //       {data.results.factcheck && data.results.factcheck.summary && (
  //         <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4 backdrop-blur-sm">
  //           <h4 className="font-semibold text-yellow-300 mb-2">Fact Check</h4>
  //           <div className="text-sm text-yellow-200 space-y-1">
  //             {typeof data.results.factcheck.summary === 'object' ? (
  //               Object.entries(data.results.factcheck.summary).map(([key, value]) => (
  //                 <p key={key}><span className="font-medium">{key}:</span> {JSON.stringify(value)}</p>
  //               ))
  //             ) : (
  //               <p>{JSON.stringify(data.results.factcheck.summary)}</p>
  //             )}
  //           </div>
  //         </div>
  //       )}
  //     </div>
  //   );
  // };
const formatResult = (data) => {
  if (!data) return null;

  // ✅ normalize structure
  const results = data.results || {};
  const sections = [];

  // ✅ SUMMARY (fixed)
  const summaryText = results.summary || data.summary;
  if (summaryText) {
    sections.push(
      <div
        key="summary"
        className="bg-indigo-900/30 border border-indigo-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-indigo-300 mb-2">Summary</h4>
        <p className="text-sm text-indigo-200 whitespace-pre-line">
          {summaryText}
        </p>
      </div>
    );
  }

  // ---------- COMBINED ANALYSIS ----------
  if (results.combined) {
    sections.push(
      <div
        key="combined"
        className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-blue-300 mb-2">Combined Analysis</h4>
        <p className="text-sm text-blue-200">{results.combined.short}</p>
        {results.combined.confidence_score !== undefined && (
          <p className="text-xs text-blue-400 mt-2">
            Confidence: {(results.combined.confidence_score * 100).toFixed(1)}%
          </p>
        )}
      </div>
    );
  }

  // ---------- BIAS ANALYSIS ----------
  if (results.bias) {
    sections.push(
      <div
        key="bias"
        className="bg-purple-900/30 border border-purple-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-purple-300 mb-2">Bias Analysis</h4>
        <p className="text-sm text-purple-200">Label: {results.bias.label}</p>
        <p className="text-xs text-purple-400">
          Score: {(results.bias.score * 100).toFixed(1)}%
        </p>
      </div>
    );
  }

  // ---------- AI IMAGE DETECTION ----------
  if (results.ai_image) {
    sections.push(
      <div
        key="ai_image"
        className="bg-green-900/30 border border-green-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-green-300 mb-2">
          AI Image Detection
        </h4>
        <p className="text-sm text-green-200">
          Prediction: {results.ai_image.predicted_class}
        </p>
        <p className="text-xs text-green-400">
          Confidence: {(results.ai_image.confidence * 100).toFixed(1)}%
        </p>
      </div>
    );
  }

  // ---------- MANIPULATION DETECTION ----------
  if (results.manipulated) {
    sections.push(
      <div
        key="manipulated"
        className="bg-orange-900/30 border border-orange-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-orange-300 mb-2">
          Manipulation Detection
        </h4>
        <p className="text-sm text-orange-200">
          Prediction: {results.manipulated.prediction}
        </p>
        <p className="text-xs text-orange-400">
          Confidence: {(results.manipulated.confidence * 100).toFixed(1)}%
        </p>
        {results.manipulated.is_manipulated !== undefined && (
          <p className="text-xs text-orange-300 mt-1">
            Is Manipulated: {results.manipulated.is_manipulated ? "Yes" : "No"}
          </p>
        )}
        {results.manipulated.summary && (
          <p className="text-xs text-orange-200 mt-2">
            {results.manipulated.summary}
          </p>
        )}
      </div>
    );
  }

  // ---------- VIDEO ANALYSIS ----------
  const video =
    results.video || results.video_analysis || results.video_result;
  if (video) {
    sections.push(
      <div
        key="video"
        className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-red-300 mb-2">Video Analysis</h4>

        {video.overall_verdict && (
          <>
            <p className="text-sm text-red-200">
              Verdict: {video.overall_verdict.verdict}
            </p>
            <p className="text-xs text-red-400">
              Risk Level: {video.overall_verdict.risk_level}
            </p>
          </>
        )}

        {video.visual_detection && (
          <div className="mt-3 pt-3 border-t border-red-700/30">
            <p className="text-xs text-red-300 mb-1">Visual Detection:</p>
            <p className="text-xs text-red-400">
              Overall: {video.visual_detection.overall_prediction} (
              {(video.visual_detection.overall_confidence * 100).toFixed(1)}%)
            </p>
          </div>
        )}

        {Array.isArray(video.audio_detection) && (
          <div className="mt-2">
            <p className="text-xs text-red-300 mb-1">Audio Detection:</p>
            {video.audio_detection.map((audio, idx) => (
              <p key={idx} className="text-xs text-red-400">
                {audio.label}: {(audio.score * 100).toFixed(1)}%
              </p>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ---------- FACT CHECK ----------
  if (results.factcheck && Object.keys(results.factcheck).length > 0) {
    const { summary, claim_detail, raw_text, token_count } = results.factcheck;
    sections.push(
      <div
        key="factcheck"
        className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-yellow-300 mb-2">Fact Check</h4>

        {raw_text && (
          <p className="text-sm text-yellow-200 mb-2">Text: "{raw_text}"</p>
        )}

        {summary && (
          <p className="text-sm text-yellow-200 whitespace-pre-line">
            {typeof summary === "object"
              ? JSON.stringify(summary)
              : summary}
          </p>
        )}

        {Array.isArray(claim_detail) && (
          <div className="mt-2 space-y-1 text-xs text-yellow-300">
            <p className="font-semibold text-yellow-400">Claim Details:</p>
            {claim_detail.map((claim, i) => (
              <p key={i} className="text-yellow-200">
                {JSON.stringify(claim)}
              </p>
            ))}
          </div>
        )}

        {token_count && (
          <p className="text-xs text-yellow-400 mt-2">
            Token Count: {token_count}
          </p>
        )}
      </div>
    );
  }

  // ---------- FALLBACK ----------
  if (sections.length === 0) {
    sections.push(
      <div
        key="fallback"
        className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-4 backdrop-blur-sm"
      >
        <h4 className="font-semibold text-gray-300 mb-2">No Results</h4>
        <p className="text-sm text-gray-400">
          No recognizable analysis data found.
        </p>
      </div>
    );
  }

  return <div className="space-y-4">{sections}</div>;
};



  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      {/* Gradient Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
        </div>
      </div>

      {/* Sidebar */}
      {sidebarOpen && (
        <>
          <div
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          />

          <aside className="fixed lg:relative w-64 h-full bg-gray-800/90 backdrop-blur-xl border-r border-gray-700/50 z-50 flex flex-col">
            <div className="p-4 border-b border-gray-700/50 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Chats</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden p-1 hover:bg-gray-700/50 rounded transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <button
              onClick={createNewChat}
              className="m-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-lg p-3 flex items-center justify-center gap-2 transition-all duration-300 shadow-lg"
            >
              <Plus className="w-5 h-5" />
              New Chat
            </button>

            <div className="flex-1 overflow-y-auto">
              {chats.map(chat => (
                <div
                  key={chat.id}
                  onClick={() => switchChat(chat.id)}
                  className={`p-3 mx-2 mb-2 rounded-lg cursor-pointer group flex items-center justify-between transition-all duration-200 ${currentChatId === chat.id
                      ? 'bg-gray-700/70 shadow-lg'
                      : 'hover:bg-gray-700/50'
                    }`}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <MessageSquare className="w-4 h-4 flex-shrink-0 text-indigo-400" />
                    <span className="text-sm truncate text-white">{chat.title}</span>
                  </div>
                  <button
                    onClick={(e) => deleteChat(chat.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600/50 rounded transition-all"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              ))}
            </div>
          </aside>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Header */}
        <header className="bg-gray-800/80 backdrop-blur-xl border-b border-gray-700/50 p-4">
          <div className="max-w-4xl mx-auto flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
              >
                <Menu className="w-6 h-6 text-gray-400" />
              </button>
            )}
            <h1 className="text-xl font-semibold text-white">Multimodal Analysis</h1>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center px-4 min-h-[400px]">
                <div>
                  <LayoutTextFlip
                    text="Ask Anything"
                    words={[
                      "DeepFake Detection",
                      "Fact Checking",
                      "Media Verification",
                      "AI Insights",
                    ]}
                  />
                </div>
                <p className="mt-6 text-lg text-gray-400 max-w-2xl leading-relaxed">
                  Interact with VeriWise to analyze text, images, or videos. Get real-time insights on authenticity and truthfulness
                </p>
              </div>
            )}

            {messages.map(message => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-3xl ${message.type === 'user'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                    : 'bg-gray-800/70 border border-gray-700/50 text-white'
                  } rounded-2xl p-4 backdrop-blur-sm shadow-lg`}>
                  {message.type === 'user' && (
                    <div className="space-y-3">
                      {message.text && <p className="text-sm">{message.text}</p>}
                      {message.image && (
                        <img src={message.image} alt="Uploaded" className="rounded-lg max-w-xs border border-gray-600/50" />
                      )}
                      {message.video && (
                        <video src={message.video} controls className="rounded-lg max-w-xs border border-gray-600/50" />
                      )}
                    </div>
                  )}
                  {message.type === 'assistant' && formatResult(message.data)}
                  {message.type === 'error' && (
                    <p className="text-sm text-red-400">{message.text}</p>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800/70 border border-gray-700/50 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
                  <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="bg-gray-800/80 backdrop-blur-xl border-t border-gray-700/50 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="space-y-3">
              <div className="relative bg-gray-700/50 backdrop-blur-md border border-gray-600/50 rounded-2xl shadow-xl focus-within:border-indigo-500 transition-all duration-300">
                {/* File Previews */}
                {(image || video) && (
                  <div className="px-4 pt-3 pb-2 border-b border-gray-600/50 flex gap-2">
                    {image && (
                      <div className="relative group">
                        <img
                          src={URL.createObjectURL(image)}
                          alt="Preview"
                          className="h-16 w-16 object-cover rounded-lg border border-gray-600/50"
                        />
                        <button
                          type="button"
                          onClick={() => setImage(null)}
                          className="absolute -top-1 -right-1 bg-red-600 hover:bg-red-700 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                    {video && (
                      <div className="relative group">
                        <video
                          src={URL.createObjectURL(video)}
                          className="h-16 w-16 object-cover rounded-lg border border-gray-600/50"
                        />
                        <button
                          type="button"
                          onClick={() => setVideo(null)}
                          className="absolute -top-1 -right-1 bg-red-600 hover:bg-red-700 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Placeholder */}
                {!text && (
                  <div
                    className="absolute left-4 top-4 pointer-events-none text-gray-500 transition-all duration-300"
                    style={{ marginTop: (image || video) ? '76px' : '0' }}
                  >
                    {placeholders[currentPlaceholder]}
                  </div>
                )}

                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  className="w-full bg-transparent text-white px-4 py-4 pr-36 resize-none focus:outline-none max-h-[200px] overflow-y-auto"
                  style={{ minHeight: '56px' }}
                />

                {/* Action Buttons */}
                <div className="absolute right-2 bottom-2 flex items-center gap-2">
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
                    className={`p-2.5 rounded-xl transition-all ${image
                        ? 'bg-gray-600/40 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-600/60 hover:bg-gray-600 text-gray-300 hover:text-indigo-400'
                      }`}
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
                    className={`p-2.5 rounded-xl transition-all ${video
                        ? 'bg-gray-600/40 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-600/60 hover:bg-gray-600 text-gray-300 hover:text-indigo-400'
                      }`}
                  >
                    <Video className="w-5 h-5" />
                  </button>

                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={isLoading || (!text.trim() && !image && !video)}
                    className={`p-2.5 rounded-xl transition-all duration-300 ${isLoading || (!text.trim() && !image && !video)
                        ? 'bg-gray-600/60 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg hover:shadow-indigo-500/50'
                      }`}
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <p className="text-xs text-gray-500 text-center">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}