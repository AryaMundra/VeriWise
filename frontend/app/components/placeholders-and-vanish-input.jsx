// "use client";

// import { AnimatePresence, motion } from "motion/react";
// import { useCallback, useEffect, useRef, useState } from "react";
// import { SendHorizonal, Image, Video } from "lucide-react";
// import { cn } from "@/lib/utils";

// export function PlaceholdersAndVanishInput({
//   placeholders,
//   onChange,
//   onSubmit,
//   onImageSelect,
//  onVideoSelect,
// }) {
//   const [currentPlaceholder, setCurrentPlaceholder] = useState(0);

//   const intervalRef = useRef(null);
//   const startAnimation = () => {
//     intervalRef.current = setInterval(() => {
//       setCurrentPlaceholder((prev) => (prev + 1) % placeholders.length);
//     }, 3000);
//   };
//   const handleVisibilityChange = () => {
//     if (document.visibilityState !== "visible" && intervalRef.current) {
//       clearInterval(intervalRef.current); // Clear the interval when the tab is not visible
//       intervalRef.current = null;
//     } else if (document.visibilityState === "visible") {
//       startAnimation(); // Restart the interval when the tab becomes visible
//     }
//   };

//   useEffect(() => {
//     startAnimation();
//     document.addEventListener("visibilitychange", handleVisibilityChange);

//     return () => {
//       if (intervalRef.current) {
//         clearInterval(intervalRef.current);
//       }
//       document.removeEventListener("visibilitychange", handleVisibilityChange);
//     };
//   }, [placeholders]);

//   const canvasRef = useRef(null);
//   const newDataRef = useRef([]);
//   const inputRef = useRef(null);
//   const [value, setValue] = useState("");
//   const [animating, setAnimating] = useState(false);

//   const draw = useCallback(() => {
//     if (!inputRef.current) return;
//     const canvas = canvasRef.current;
//     if (!canvas) return;
//     const ctx = canvas.getContext("2d");
//     if (!ctx) return;

//     canvas.width = 800;
//     canvas.height = 800;
//     ctx.clearRect(0, 0, 800, 800);
//     const computedStyles = getComputedStyle(inputRef.current);

//     const fontSize = parseFloat(computedStyles.getPropertyValue("font-size"));
//     ctx.font = `${fontSize * 2}px ${computedStyles.fontFamily}`;
//     ctx.fillStyle = "#FFF";
//     ctx.fillText(value, 16, 40);

//     const imageData = ctx.getImageData(0, 0, 800, 800);
//     const pixelData = imageData.data;
//     const newData = [];

//     for (let t = 0; t < 800; t++) {
//       let i = 4 * t * 800;
//       for (let n = 0; n < 800; n++) {
//         let e = i + 4 * n;
//         if (
//           pixelData[e] !== 0 &&
//           pixelData[e + 1] !== 0 &&
//           pixelData[e + 2] !== 0
//         ) {
//           newData.push({
//             x: n,
//             y: t,
//             color: [
//               pixelData[e],
//               pixelData[e + 1],
//               pixelData[e + 2],
//               pixelData[e + 3],
//             ],
//           });
//         }
//       }
//     }

//     newDataRef.current = newData.map(({ x, y, color }) => ({
//       x,
//       y,
//       r: 1,
//       color: `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${color[3]})`,
//     }));
//   }, [value]);

//   useEffect(() => {
//     draw();
//   }, [value, draw]);

//   const animate = (start) => {
//     const animateFrame = (pos = 0) => {
//       requestAnimationFrame(() => {
//         const newArr = [];
//         for (let i = 0; i < newDataRef.current.length; i++) {
//           const current = newDataRef.current[i];
//           if (current.x < pos) {
//             newArr.push(current);
//           } else {
//             if (current.r <= 0) {
//               current.r = 0;
//               continue;
//             }
//             current.x += Math.random() > 0.5 ? 1 : -1;
//             current.y += Math.random() > 0.5 ? 1 : -1;
//             current.r -= 0.05 * Math.random();
//             newArr.push(current);
//           }
//         }
//         newDataRef.current = newArr;
//         const ctx = canvasRef.current?.getContext("2d");
//         if (ctx) {
//           ctx.clearRect(pos, 0, 800, 800);
//           newDataRef.current.forEach((t) => {
//             const { x: n, y: i, r: s, color: color } = t;
//             if (n > pos) {
//               ctx.beginPath();
//               ctx.rect(n, i, s, s);
//               ctx.fillStyle = color;
//               ctx.strokeStyle = color;
//               ctx.stroke();
//             }
//           });
//         }
//         if (newDataRef.current.length > 0) {
//           animateFrame(pos - 8);
//         } else {
//           setValue("");
//           setAnimating(false);
//         }
//       });
//     };
//     animateFrame(start);
//   };

//   const handleKeyDown = (e) => {
//     if (e.key === "Enter" && !animating) {
//       vanishAndSubmit();
//     }
//   };

//   const vanishAndSubmit = () => {
//     setAnimating(true);
//     draw();

//     const value = inputRef.current?.value || "";
//     if (value && inputRef.current) {
//       const maxX = newDataRef.current.reduce((prev, current) => (current.x > prev ? current.x : prev), 0);
//       animate(maxX);
//     }
//   };

//   const handleSubmit = (e) => {
//     e.preventDefault();
//     vanishAndSubmit();
//     onSubmit && onSubmit(e);
//   };
//   return (
//   <form
//     className={cn(
//       "w-full relative max-w-3xl mx-auto bg-[#1a1a1a]/90 dark:bg-[#111]/90 backdrop-blur-xl",
//       "h-14 rounded-full shadow-[0_4px_20px_rgba(0,0,0,0.4)]",
//       "border border-[#2a2a2a] flex items-center px-3 gap-2",
//       "fixed bottom-6 left-1/2 -translate-x-1/2"
//     )}
//     onSubmit={handleSubmit}
//   >
//     {/* Hidden canvas used for vanish animation */}
//     <canvas
//       ref={canvasRef}
//       className={cn(
//         "absolute pointer-events-none text-base transform scale-50",
//         "top-[10%] left-14 origin-top-left filter invert dark:invert-0",
//         !animating ? "opacity-0" : "opacity-100"
//       )}
//     />

//     {/* Upload Image */}
//     <button
//       type="button"
//       onClick={onImageSelect}
//       className="p-2 rounded-full hover:bg-[#2a2a2a] transition"
//     >
//       <Image className="w-5 h-5 text-gray-400" />
//     </button>

//     {/* Upload Video */}
//     <button
//       type="button"
//       onClick={onVideoSelect}
//       className="p-2 rounded-full hover:bg-[#2a2a2a] transition"
//     >
//       <Video className="w-5 h-5 text-gray-400" />
//     </button>

//     {/* Text Input */}
//     <input
//       ref={inputRef}
//       value={value}
//       onChange={(e) => { if (!animating) setValue(e.target.value); onChange?.(e); }}
//       onKeyDown={handleKeyDown}
//       type="text"
//       className={cn(
//         "flex-1 bg-transparent border-none text-white text-sm sm:text-base",
//         "focus:outline-none placeholder-gray-500",
//         "px-2",
//         animating && "text-transparent"
//       )}
//     />

//     {/* Floating Placeholder Animation */}
//     <div className="absolute inset-0 flex items-center pointer-events-none pl-20">
//       <AnimatePresence>
//         {!value && (
//           <motion.p
//             key={currentPlaceholder}
//             initial={{ opacity: 0, y: 4 }}
//             animate={{ opacity: 1, y: 0 }}
//             exit={{ opacity: 0, y: -6 }}
//             transition={{ duration: 0.2 }}
//             className="text-gray-500 text-sm truncate"
//           >
//             {placeholders[currentPlaceholder]}
//           </motion.p>
//         )}
//       </AnimatePresence>
//     </div>

//     {/* Send Button */}
//     <button
//       disabled={!value}
//       type="submit"
//       className="h-9 w-9 rounded-full flex items-center justify-center disabled:opacity-40 bg-indigo-600 hover:bg-indigo-500 transition"
//     >
//       <SendHorizonal className="h-4 w-4 text-white" />
//     </button>
//   </form>

//   );
// }
"use client";

import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Image, Video, X, Send } from "lucide-react";

export function PlaceholdersAndVanishInput({
  placeholders,
  onChange,
  onSubmit,
}) {
  const [currentPlaceholder, setCurrentPlaceholder] = useState(0);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [value, setValue] = useState("");
  const [animating, setAnimating] = useState(false);

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const inputRef = useRef(null);
  const canvasRef = useRef(null);
  const newDataRef = useRef([]);

  // === Rotate Placeholder Text ===
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentPlaceholder((p) => (p + 1) % placeholders.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [placeholders]);

  // === Canvas Draw (for vanish animation) ===
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx || !inputRef.current) return;

    canvas.width = 800;
    canvas.height = 800;
    ctx.clearRect(0, 0, 800, 800);

    const style = getComputedStyle(inputRef.current);
    const fontSize = parseFloat(style.getPropertyValue("font-size"));
    ctx.font = `${fontSize * 2}px ${style.fontFamily}`;
    ctx.fillStyle = "#fff";
    ctx.fillText(value, 16, 40);

    const imageData = ctx.getImageData(0, 0, 800, 800);
    const pixels = imageData.data;
    const newData = [];

    for (let y = 0; y < 800; y++) {
      for (let x = 0; x < 800; x++) {
        const idx = (y * 800 + x) * 4;
        if (pixels[idx + 3] > 0) {
          newData.push({
            x,
            y,
            color: `rgba(${pixels[idx]},${pixels[idx + 1]},${pixels[idx + 2]},${pixels[idx + 3]})`,
          });
        }
      }
    }
    newDataRef.current = newData;
  }, [value]);

  useEffect(() => {
    draw();
  }, [value, draw]);

  // === Animate vanish effect ===
  const animateVanish = (start) => {
    const animateFrame = (pos = start) => {
      requestAnimationFrame(() => {
        const ctx = canvasRef.current?.getContext("2d");
        if (!ctx) return;
        ctx.clearRect(0, 0, 800, 800);

        newDataRef.current.forEach((dot) => {
          dot.x += Math.random() > 0.5 ? 1 : -1;
          dot.y += Math.random() > 0.5 ? 1 : -1;
          dot.r = (dot.r || 1) - 0.05;
          if (dot.r > 0) {
            ctx.fillStyle = dot.color;
            ctx.fillRect(dot.x, dot.y, dot.r, dot.r);
          }
        });

        newDataRef.current = newDataRef.current.filter((d) => d.r > 0);
        if (newDataRef.current.length > 0) animateFrame(pos - 8);
        else {
          setValue("");
          setAnimating(false);
        }
      });
    };
    animateFrame(start);
  };

  // === Trigger submit ===
  const vanishAndSubmit = () => {
    if (!value.trim() && !selectedImage && !selectedVideo) return;

    setAnimating(true);
    draw();
    const maxX = newDataRef.current.reduce((a, c) => (c.x > a ? c.x : a), 0);
    animateVanish(maxX);

    onSubmit?.({
      value,
      image: selectedImage?.file || null,
      video: selectedVideo?.file || null,
    });
  };

  // === File Handlers ===
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage({ file, preview: URL.createObjectURL(file) });
    }
  };

  const handleVideoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedVideo({ file, preview: URL.createObjectURL(file) });
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    imageInputRef.current.value = "";
  };

  const removeVideo = () => {
    setSelectedVideo(null);
    videoInputRef.current.value = "";
  };

  return (
    <div className="w-full flex flex-col items-center justify-end space-y-3 fixed bottom-6 right-0 left-0 sm:left-[15rem] sm:right-[2rem] px-4">
      {/* === Media Previews === */}
      {(selectedImage || selectedVideo) && (
        <div className="relative w-full max-w-xl mx-auto rounded-lg overflow-hidden shadow-lg border border-gray-700 bg-black/30 backdrop-blur-md">
          {selectedImage && (
            <div className="relative">
              <img
                src={selectedImage.preview}
                alt="Preview"
                className="w-full object-contain max-h-64"
              />
              <button
                onClick={removeImage}
                className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full p-1.5 transition"
                title="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          {selectedVideo && (
            <div className="relative">
              <video
                src={selectedVideo.preview}
                controls
                className="w-full object-contain max-h-64"
              />
              <button
                onClick={removeVideo}
                className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full p-1.5 transition"
                title="Remove video"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* === Input Box === */}
      <div
        className={cn(
          "w-full relative max-w-xl mx-auto bg-white/10 dark:bg-zinc-900/80 h-12 rounded-full overflow-hidden",
          "border border-gray-700 shadow-md backdrop-blur-md transition duration-200 flex items-center px-4"
        )}
      >
        <canvas
          ref={canvasRef}
          className={cn(
            "absolute pointer-events-none text-base transform scale-50 top-[20%] left-4 origin-top-left filter invert dark:invert-0",
            !animating ? "opacity-0" : "opacity-100"
          )}
        />

        {/* Image Upload */}
        <button
          type="button"
          onClick={() => imageInputRef.current?.click()}
          className="p-2 rounded-full hover:bg-white/10 transition"
        >
          <Image className="w-5 h-5 text-gray-400" />
        </button>
        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageSelect}
        />

        {/* Video Upload */}
        <button
          type="button"
          onClick={() => videoInputRef.current?.click()}
          className="p-2 rounded-full hover:bg-white/10 transition"
        >
          <Video className="w-5 h-5 text-gray-400" />
        </button>
        <input
          ref={videoInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={handleVideoSelect}
        />

        {/* Text Input */}
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => {
            if (!animating) setValue(e.target.value);
            onChange?.(e);
          }}
          onKeyDown={(e) => e.key === "Enter" && vanishAndSubmit()}
          type="text"
          placeholder=""
          className={cn(
            "flex-1 bg-transparent border-none text-white text-sm sm:text-base px-2 focus:outline-none placeholder-gray-400",
            animating && "text-transparent"
          )}
        />

        {/* Submit Button */}
        <button
          type="button"
          onClick={vanishAndSubmit}
          className="p-2 rounded-full bg-blue-600 hover:bg-blue-700 text-white transition ml-1"
          title="Send"
        >
          <Send className="w-4 h-4" />
        </button>

        {/* Placeholder Animation */}
        <div className="absolute inset-0 flex items-center pl-28 pointer-events-none">
          <AnimatePresence mode="wait">
            {!value && (
              <motion.p
                key={`placeholder-${currentPlaceholder}`}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                transition={{ duration: 0.3 }}
                className="text-gray-400 text-sm sm:text-base truncate"
              >
                {placeholders[currentPlaceholder]}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
