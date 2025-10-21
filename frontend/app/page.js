"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <h1 className="text-4xl md:text-6xl font-bold mb-8 text-center">
        AI Verification Hub
      </h1>
      <p className="text-lg md:text-xl mb-12 text-gray-300 text-center max-w-xl">
        Detect deepfakes or fact-check information using cutting-edge AI models.
      </p>
      <div className="flex flex-col md:flex-row gap-6">
        <Link href="/deepfake">
          <button className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-xl text-lg font-semibold transition-all shadow-md hover:scale-105">
            Deepfake Detection
          </button>
        </Link>

        <Link href="/factcheck">
          <button className="px-8 py-4 bg-green-600 hover:bg-green-700 rounded-xl text-lg font-semibold transition-all shadow-md hover:scale-105">
            Fact Checking
          </button>
        </Link>
      </div>
    </main>
  );
}
