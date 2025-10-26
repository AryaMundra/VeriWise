"use client";

import { motion } from "motion/react";
import React from "react";
import { AuroraBackground } from "@/app/components/aurora-background";
import { useRouter } from "next/navigation";

export default function VeriwiseHero() {
  const router = useRouter();
  
  return (
    <>
      <AuroraBackground>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.3,
            duration: 0.8,
            ease: "easeInOut",
          }}
          className="relative flex flex-col gap-6 items-center justify-center px-4 py-20 text-center min-h-screen"
        >
          <div className="text-3xl md:text-7xl font-bold dark:text-white text-center">
            Detect deepfakes and fact check text, images and videos all in one place.
          </div>
          <div className="font-extralight text-base md:text-4xl dark:text-neutral-200 py-4">
            No other place like this
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
        </motion.div>
      </AuroraBackground>
    </>
  );
}