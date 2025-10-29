"use client";
import React from "react";
import { motion } from "framer-motion";
import { MessageCircle } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="bg-zinc-50 dark:bg-zinc-900 flex flex-col transition-colors">
      {/* CTA Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        viewport={{ once: true }}
        className="py-12 px-6 flex items-center justify-center"
      >
        <div className="max-w-4xl w-full">
          <div className="relative p-10 rounded-3xl border border-white/20 dark:border-white/10 shadow-2xl bg-white/30 dark:bg-white/5 backdrop-blur-md">
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-500/10 via-transparent to-indigo-500/5 pointer-events-none" />
            
            <h3 className="relative text-3xl font-bold text-zinc-900 dark:text-white mb-4 text-center">
              Ready to verify truth in the digital world?
            </h3>
            <p className="relative text-zinc-700 dark:text-zinc-300 mb-8 max-w-2xl mx-auto text-center text-lg">
              Join us in building the future of trustworthy technology at IIT Mandi.
              Whether you're a beginner or an expert, there's a place for you in our mission.
            </p>
            <div className="flex justify-center relative">
              <motion.a
                href="/chat"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all duration-300 font-medium shadow-lg shadow-indigo-600/20"
              >
                <MessageCircle className="w-5 h-5" />
                Start Chatting Now
              </motion.a>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
        className="mt-0 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-900/80 backdrop-blur-md transition-colors"
      >
        <div className="max-w-7xl mx-auto px-6 py-10">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            viewport={{ once: true }}
            className="pt-6 border-t border-zinc-200 dark:border-zinc-800 flex flex-col md:flex-row justify-between items-center gap-4"
          >
            <p className="text-zinc-600 dark:text-zinc-400 text-sm">
              © 2025 VeriWise. All rights reserved.
            </p>
            <div className="flex gap-6">
              {["Privacy Policy", "Terms of Service", "Cookie Policy"].map((item, i) => (
                <motion.a
                  key={i}
                  href="#"
                  whileHover={{ scale: 1.05 }}
                  className="text-zinc-600 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 text-sm transition-colors"
                >
                  {item}
                </motion.a>
              ))}
            </div>
          </motion.div>
        </div>
      </motion.footer>
    </div>
  );
}
