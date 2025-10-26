"use client";
import { UploadCloud, Lock, Server } from "lucide-react";

const features = [
  {
    name: "Push to deploy.",
    description:
      "Lorem ipsum, dolor sit amet consectetur adipisicing elit. Maiores impedit perferendis suscipit eaque, iste dolor cupiditate blanditiis ratione.",
    icon: UploadCloud,
  },
  {
    name: "SSL certificates.",
    description:
      "Anim aute id magna aliqua ad ad non deserunt sunt. Qui irure qui lorem cupidatat commodo.",
    icon: Lock,
  },
  {
    name: "Database backups.",
    description:
      "Ac tincidunt sapien vehicula erat auctor pellentesque rhoncus. Et magna sit morbi lobortis.",
    icon: Server,
  },
];

export default function Example() {
  return (
    <div className="overflow-hidden bg-zinc-50 dark:bg-zinc-900 py-24 sm:py-32 transition-colors">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 sm:gap-y-20 lg:mx-0 lg:max-w-none lg:grid-cols-2">
          
          {/* Left Content */}
          <div className="lg:pt-4 lg:pr-8">
            <div className="lg:max-w-lg">
              <h2 className="text-base font-semibold text-indigo-600 dark:text-indigo-400">
                Deploy faster
              </h2>
              <p className="mt-2 text-4xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-5xl">
                A better workflow
              </p>
              <p className="mt-6 text-lg text-zinc-600 dark:text-zinc-300">
                Lorem ipsum, dolor sit amet consectetur adipisicing elit. Maiores
                impedit perferendis suscipit eaque, iste dolor cupiditate
                blanditiis ratione.
              </p>

              <dl className="mt-10 max-w-xl space-y-8 text-zinc-700 dark:text-zinc-400 lg:max-w-none">
                {features.map((feature) => (
                  <div key={feature.name} className="relative pl-9">
                    <dt className="inline font-semibold text-zinc-900 dark:text-white">
                      <feature.icon
                        aria-hidden="true"
                        className="absolute top-1 left-1 size-5 text-indigo-600 dark:text-indigo-400"
                      />
                      {feature.name}
                    </dt>{" "}
                    <dd className="inline">{feature.description}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          {/* Right Image */}
          <img
            alt="Product screenshot"
            src="https://tailwindcss.com/plus-assets/img/component-images/dark-project-app-screenshot.png"
            width={2432}
            height={1442}
            className="w-3xl max-w-none rounded-xl 
                       shadow-xl ring-1 ring-zinc-200/50 dark:ring-white/10 
                       sm:w-228 md:-ml-4 lg:-ml-0"
          />
        </div>
      </div>
    </div>
  );
}
