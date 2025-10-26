"use client";

import { useState } from "react";
import ResultCard from "./ResultCard";

const NEXT_PUBLIC_API_URL="http://localhost:8000"

async function uploadMedia(file, endpoint) {
  const formData = new FormData();
  formData.append("media_file", file);

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/${endpoint}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Failed to fetch response from backend");
  return res.json();
}

export default function FileUploader() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file");
    setLoading(true);
    try {
      const data = await uploadMedia(file, "deepfake");
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Error uploading file");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6 bg-white rounded-2xl shadow-lg mt-10">
      <h1 className="text-2xl font-semibold mb-4 text-center">Deepfake Detector</h1>

      <input
        type="file"
        accept="video/*,image/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="block w-full text-sm text-gray-700 border border-gray-300 rounded-lg p-2"
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
      >
        {loading ? "Analyzing..." : "Upload & Analyze"}
      </button>

      {result && <ResultCard data={result} />}
    </div>
  );
}