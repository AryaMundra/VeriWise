"use client";
import React, { useState } from "react";
import { Upload, Image, Video, CheckCircle, XCircle, AlertCircle } from "lucide-react";

const DeepfakePage = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mediaType, setMediaType] = useState("image");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setResult(null);
    setError("");

    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setPreview(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please upload a file before submitting.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("media_type", String(mediaType));

      const res = await fetch("http://localhost:8000/api/deepfake", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`HTTP Error ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getResultIcon = () => {
    if (!result) return null;
    const isFake = result.prediction.toLowerCase().includes("fake");
    return isFake ? (
      <XCircle className="w-16 h-16 text-red-500" />
    ) : (
      <CheckCircle className="w-16 h-16 text-green-500" />
    );
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-4 sm:p-6">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
            <AlertCircle className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Deepfake Detector
          </h1>
          <p className="text-gray-600">
            Upload an image or video to analyze its authenticity
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white shadow-2xl rounded-3xl overflow-hidden">
          <div className="p-8">
            {/* Media Type Selector */}
            <div className="flex gap-4 mb-6">
              <button
                type="button"
                onClick={() => {
                  setMediaType("image");
                  setFile(null);
                  setPreview(null);
                  setResult(null);
                }}
                className={`flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-xl font-semibold transition-all ${
                  mediaType === "image"
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg scale-105"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Image className="w-5 h-5" />
                Image
              </button>
              <button
                type="button"
                onClick={() => {
                  setMediaType("video");
                  setFile(null);
                  setPreview(null);
                  setResult(null);
                }}
                className={`flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-xl font-semibold transition-all ${
                  mediaType === "video"
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg scale-105"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Video className="w-5 h-5" />
                Video
              </button>
            </div>

            {/* File Upload Zone */}
            <div className="mb-6">
              <label className="block w-full">
                <div className="border-3 border-dashed border-gray-300 rounded-2xl p-8 text-center hover:border-indigo-400 hover:bg-indigo-50 transition-all cursor-pointer">
                  {preview ? (
                    <div className="space-y-4">
                      {mediaType === "image" ? (
                        <img
                          src={preview}
                          alt="Preview"
                          className="max-h-64 mx-auto rounded-lg shadow-md"
                        />
                      ) : (
                        <video
                          src={preview}
                          controls
                          className="max-h-64 mx-auto rounded-lg shadow-md"
                        />
                      )}
                      <p className="text-sm text-gray-600 font-medium">
                        {file.name}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <Upload className="w-12 h-12 mx-auto text-gray-400" />
                      <div>
                        <p className="text-lg font-semibold text-gray-700">
                          Click to upload {mediaType}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          or drag and drop
                        </p>
                      </div>
                    </div>
                  )}
                </div>
                <input
                  type="file"
                  accept={mediaType === "image" ? "image/*" : "video/*"}
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !file}
              className={`w-full py-4 rounded-xl font-bold text-lg transition-all ${
                loading || !file
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:shadow-xl hover:scale-105 active:scale-95"
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                  Analyzing...
                </span>
              ) : (
                "Analyze Media"
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mx-8 mb-8 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800 font-medium">{error}</p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-8 border-t">
              <div className="flex flex-col items-center text-center mb-6">
                {getResultIcon()}
                <h2 className="text-2xl font-bold text-gray-900 mt-4 mb-2">
                  Analysis Complete
                </h2>
                <p
                  className={`text-3xl font-bold ${
                    result.prediction.toLowerCase().includes("fake")
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {result.prediction}
                </p>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Media Type</p>
                  <p className="text-lg font-bold text-gray-900 capitalize">
                    {result.type}
                  </p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Confidence</p>
                  <p className="text-lg font-bold text-gray-900">
                    {(result.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mb-6">
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-1000 ${
                      result.prediction.toLowerCase().includes("fake")
                        ? "bg-gradient-to-r from-red-500 to-red-600"
                        : "bg-gradient-to-r from-green-500 to-green-600"
                    }`}
                    style={{ width: `${result.confidence * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Details Accordion */}
              {result.details && (
                <details className="bg-white rounded-xl overflow-hidden shadow-sm">
                  <summary className="cursor-pointer p-4 font-semibold text-gray-800 hover:bg-gray-50 transition-colors">
                    View Technical Details
                  </summary>
                  <pre className="p-4 text-xs overflow-auto max-h-60 text-gray-700 bg-gray-50 border-t">
                    {JSON.stringify(result.details, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-600 mt-6">
          Powered by advanced AI detection algorithms
        </p>
      </div>
    </div>
  );
};

export default DeepfakePage;