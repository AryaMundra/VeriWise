"use client";

import { motion } from "motion/react";
import React from "react";
import { AuroraBackground } from "@/app/components/aurora-background";
import { useRouter } from "next/navigation";

// Stats data
const stats = [
  { id: 1, name: "Deepfakes Detected", value: "1.2M+" },
  { id: 2, name: "Sources Verified", value: "850K+" },
  { id: 3, name: "Misinformation Flagged", value: "920K+" },
];

export default function VeriwiseHero() {
  const router = useRouter();

  return (
    <AuroraBackground>
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{
          delay: 0.3,
          duration: 0.8,
          ease: "easeInOut",
        }}
        // 👇 Added margin-top to account for navbar height
        className="relative flex flex-col gap-10 items-center justify-center px-4 py-20 text-center min-h-screen mt-24 sm:mt-32"
      >
        {/* Hero text */}
        <div className="text-3xl md:text-7xl font-bold dark:text-white text-center max-w-5xl">
          Uncover the truth behind every text, image, and video with AI.
        </div>

        <div className="font-extralight text-base md:text-4xl dark:text-neutral-200 py-2">
          No other place like this.
        </div>

        {/* CTA Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => router.push("/chat")}
          className="mt-6 relative group"
        >
          <div className="absolute transition-all duration-300 rounded-full -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-75 group-hover:opacity-100 blur group-hover:blur-md" />
          <div className="relative bg-slate-900 rounded-full text-white px-8 py-4 text-lg font-medium shadow-lg hover:shadow-xl transition-all">
            Try Now
          </div>
        </motion.button>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8, ease: "easeOut" }}
          className="mt-16 w-full max-w-6xl px-6"
        >
          <dl className="grid grid-cols-1 sm:grid-cols-3 gap-12 text-center">
            {stats.map((stat) => (
              <div key={stat.id} className="flex flex-col gap-y-3 items-center">
                <dt className="text-base text-gray-300">{stat.name}</dt>
                <dd className="order-first text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </motion.div>
      </motion.div>
    </AuroraBackground>
  );
}
