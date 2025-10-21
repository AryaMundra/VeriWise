"use client"
import { useState } from "react";
import axios from "axios";
import { Upload, CheckCircle, XCircle, AlertCircle, Search, FileVideo } from "lucide-react";

export default function Home() {
  const [videoFile, setVideoFile] = useState(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const form = new FormData();
      if (videoFile) form.append("video", videoFile);
      form.append("text_input", text);
      const resp = await axios.post("http://localhost:8000/api/verify", form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000
      });
      setResult(resp.data);
    } catch (err) {
      console.error(err);
      setResult({ verdict: "ERROR", justification: err.message || "Request failed" });
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setVideoFile(e.dataTransfer.files[0]);
    }
  };

  const getVerdictIcon = (verdict) => {
    switch(verdict?.toUpperCase()) {
      case "TRUE": return <CheckCircle className="w-8 h-8 text-green-500" />;
      case "FALSE": return <XCircle className="w-8 h-8 text-red-500" />;
      case "ERROR": return <AlertCircle className="w-8 h-8 text-red-500" />;
      default: return <AlertCircle className="w-8 h-8 text-yellow-500" />;
    }
  };

  const getVerdictColor = (verdict) => {
    switch(verdict?.toUpperCase()) {
      case "TRUE": return "bg-green-50 border-green-200";
      case "FALSE": return "bg-red-50 border-red-200";
      case "ERROR": return "bg-red-50 border-red-200";
      default: return "bg-yellow-50 border-yellow-200";
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.7) return "text-green-600";
    if (score >= 0.4) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
            <Search className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-black mb-2">
            Multimodal FactCheck
          </h1>
          <p className="text-black">Verify claims with AI-powered analysis</p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <form onSubmit={submit} className="space-y-6">
            {/* Text Input */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Claim Text
              </label>
              <textarea 
                value={text} 
                onChange={(e)=>setText(e.target.value)}
                placeholder="Enter the claim you want to verify..."
                rows={5}
                className="w-full px-4 py-3 border border-gray-300 text-gray-400 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
              />
            </div>

            {/* Video Upload */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Video Evidence (Optional)
              </label>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
                  dragActive 
                    ? "border-blue-500 bg-blue-50" 
                    : "border-gray-300 hover:border-gray-400"
                }`}
              >
                <input 
                  type="file" 
                  accept="video/*" 
                  onChange={(e)=>setVideoFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="text-center">
                  {videoFile ? (
                    <div className="flex items-center justify-center space-x-3">
                      <FileVideo className="w-6 h-6 text-blue-500" />
                      <span className="text-gray-700 font-medium">{videoFile.name}</span>
                      <button
                        type="button"
                        onClick={(e) => {e.stopPropagation(); setVideoFile(null);}}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-600 mb-1">
                        <span className="text-blue-600 font-semibold">Click to upload</span> or drag and drop
                      </p>
                      <p className="text-sm text-gray-500">MP4, MOV, AVI up to 100MB</p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button 
              type="submit" 
              disabled={loading || !text.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Verifying Claim...
                </span>
              ) : (
                "Verify Claim"
              )}
            </button>
          </form>
        </div>

        {/* Results Card */}
        {result && (
          <div className={`rounded-2xl shadow-xl p-8 border-2 ${getVerdictColor(result.verdict)} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
            <div className="flex items-start space-x-4 mb-6">
              {getVerdictIcon(result.verdict)}
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900 mb-1">
                  Verdict: {result.verdict}
                </h3>
                {result.score !== undefined && result.score !== null && (
                  <p className={`text-lg font-semibold ${getScoreColor(result.score)}`}>
                    Confidence Score: {(result.score * 100).toFixed(1)}%
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white bg-opacity-50 rounded-xl p-4">
                <h4 className="font-semibold text-gray-900 mb-2">Justification</h4>
                <p className="text-gray-700 leading-relaxed">{result.justification}</p>
              </div>

              {result.evidence && result.evidence.length > 0 && (
                <div className="bg-white bg-opacity-50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Evidence Sources</h4>
                  <ul className="space-y-2">
                    {result.evidence.map((e, i) => (
                      <li key={i} className="flex items-start space-x-2">
                        <span className="text-blue-600 font-semibold mt-0.5">•</span>
                        <a 
                          href={e.url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline flex-1"
                        >
                          {e.snippet || e.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
// "use client"
// import { useState } from "react";
// import axios from "axios";

// export default function Home() {
//   const [videoFile, setVideoFile] = useState(null);
//   const [text, setText] = useState("");
//   const [result, setResult] = useState(null);
//   const [loading, setLoading] = useState(false);

//   const submit = async (e) => {
//     e.preventDefault();
//     setLoading(true);
//     setResult(null);
//     try {
//       const form = new FormData();
//       if (videoFile) form.append("video", videoFile);
//       form.append("text_input", text);
//       const resp = await axios.post("http://localhost:8000/api/verify", form, {
//         headers: { "Content-Type": "multipart/form-data" },
//         timeout: 120000
//       });
//       setResult(resp.data);
//     } catch (err) {
//       console.error(err);
//       setResult({ verdict: "ERROR", justification: err.message || "Request failed" });
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div style={{maxWidth:800, margin:"40px auto", fontFamily:"system-ui, sans-serif"}}>
//       <h1>Multimodal FactCheck Prototype</h1>
//       <form onSubmit={submit}>
//         <div style={{marginBottom:12}}>
//           <label>Claim text (or explanation):</label><br />
//           <textarea value={text} onChange={(e)=>setText(e.target.value)} rows={4} style={{width:"100%"}} />
//         </div>
//         <div style={{marginBottom:12}}>
//           <label>Video (optional):</label><br />
//           <input type="file" accept="video/*" onChange={(e)=>setVideoFile(e.target.files[0])} />
//         </div>
//         <button type="submit" disabled={loading} style={{padding:"8px 14px"}}>
//           {loading ? "Verifying..." : "Verify Claim"}
//         </button>
//       </form>

//       {result && (
//         <div style={{marginTop:20, border:"1px solid #ddd", padding:12, borderRadius:8}}>
//           <h3>Result: {result.verdict}</h3>
//           <p><strong>Score:</strong> {result.score ?? "—"}</p>
//           <p><strong>Justification:</strong> {result.justification}</p>
//           <div>
//             <strong>Evidence:</strong>
//             <ul>
//               {result.evidence?.map((e, i)=>(
//                 <li key={i}><a href={e.url} target="_blank" rel="noreferrer">{e.snippet || e.url}</a></li>
//               )) ?? <li>No evidence returned</li>}
//             </ul>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }