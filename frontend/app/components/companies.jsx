"use client";
import { ShieldCheck, Search, Video, Layers } from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    name: "DeepFake Detection",
    description:
      "Detect manipulated or AI-generated images and videos with cutting-edge deep learning models.",
    icon: Video,
  },
  {
    name: "Text Claim Verification",
    description:
      "Analyze textual statements and retrieve factual evidence from trusted online sources.",
    icon: Search,
  },
  {
    name: "Multimodal Analysis",
    description:
      "Combine insights from text, images, and videos to deliver comprehensive verification results.",
    icon: Layers,
  },
  {
    name: "Secure and Transparent",
    description:
      "All verifications are processed with privacy and integrity, ensuring your data stays protected.",
    icon: ShieldCheck,
  },
];

export default function Example() {
  return (
    <div
      id="features"
      className="overflow-hidden bg-zinc-50 dark:bg-zinc-900 py-24 sm:py-32 transition-colors"
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          viewport={{ once: true, amount: 0.3 }}
          className="mx-auto grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 
                     sm:gap-y-20 lg:mx-0 lg:max-w-none lg:grid-cols-2"
        >
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: "easeOut", delay: 0.2 }}
            viewport={{ once: true }}
            className="lg:pt-4 lg:pr-8"
          >
            <div className="lg:max-w-lg">
              <h2 className="text-base font-semibold text-indigo-600 dark:text-indigo-400">
                AI Powered Verification
              </h2>
              <p className="mt-2 text-4xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-5xl">
                Built for truth in the digital age
              </p>
              <p className="mt-6 text-lg text-zinc-600 dark:text-zinc-300">
                VeriWise empowers users to authenticate digital content effortlessly 
                from identifying DeepFakes to verifying online claims ensuring 
                reliability in an era of misinformation.
              </p>

              <dl className="mt-10 max-w-xl space-y-8 text-zinc-700 dark:text-zinc-400 lg:max-w-none">
                {features.map((feature, index) => (
                  <motion.div
                    key={feature.name}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.5,
                      ease: "easeOut",
                      delay: 0.2 + index * 0.1,
                    }}
                    viewport={{ once: true }}
                    className="relative pl-9"
                  >
                    <dt className="inline font-semibold text-zinc-900 dark:text-white">
                      <feature.icon
                        aria-hidden="true"
                        className="absolute top-1 left-1 size-5 text-indigo-600 dark:text-indigo-400"
                      />
                      {feature.name}
                    </dt>{" "}
                    <dd className="inline">{feature.description}</dd>
                  </motion.div>
                ))}
              </dl>
            </div>
          </motion.div>

          {/* Right Image */}
          <motion.img
            alt="Product screenshot"
            src="disp.png"
            width={2432}
            height={1442}
            className="w-3xl max-w-none rounded-xl shadow-xl 
                       ring-1 ring-zinc-200/50 dark:ring-white/10 
                       sm:w-228 md:-ml-4 lg:-ml-0"
            initial={{ opacity: 0, x: 60 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
            viewport={{ once: true }}
          />
        </motion.div>
      </div>
    </div>
  );
}
