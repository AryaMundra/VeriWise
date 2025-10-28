"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const links = [
    { href: "/", label: "Home" },
    { href: "#about", label: "About" },
    { href: "#features", label: "Features" },
    { href: "/chat", label: "Try Now" },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-40 py-4 sm:py-6 transition-all duration-500 ${
          isScrolled
            ? "bg-zinc-50/90 dark:bg-zinc-900/90 backdrop-blur-md shadow-md border-b border-zinc-200/50 dark:border-zinc-700/50"
            : "bg-transparent"
        }`}
      >
        <div className="px-4 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">

            {/* Logo */}
            <Link href="/" className="flex items-center space-x-3 group">
              <div>
                <span className="font-bold text-lg text-zinc-900 dark:text-white">
                  Veriwise
                </span>
                <span className="block text-xs text-zinc-500 dark:text-zinc-300 leading-none">
                  AI Verification
                </span>
              </div>
            </Link>

            {/* Mobile Menu Toggle */}
            <button
              type="button"
              className="md:hidden text-zinc-900 dark:text-white p-2 hover:bg-zinc-200/40 dark:hover:bg-zinc-800/40 rounded-lg transition"
              onClick={toggleMenu}
              aria-label="Toggle menu"
            >
              <div className="w-6 h-6 flex flex-col justify-center items-center space-y-1">
                <span
                  className={`block h-0.5 w-6 bg-current transition ${
                    isMenuOpen ? "rotate-45 translate-y-1.5" : ""
                  }`}
                />
                <span
                  className={`block h-0.5 w-6 bg-current transition ${
                    isMenuOpen ? "opacity-0" : ""
                  }`}
                />
                <span
                  className={`block h-0.5 w-6 bg-current transition ${
                    isMenuOpen ? "-rotate-45 -translate-y-1.5" : ""
                  }`}
                />
              </div>
            </button>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1 bg-zinc-200/40 dark:bg-zinc-800/40 backdrop-blur-xl rounded-full px-2 py-1 border border-zinc-300/40 dark:border-zinc-700/40">
              {links.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    pathname === href
                      ? "bg-indigo-500/20 text-indigo-700 dark:text-white dark:bg-indigo-500/30"
                      : "text-zinc-700 dark:text-zinc-300 hover:bg-indigo-500/20 hover:text-indigo-700 dark:hover:text-white"
                  }`}
                >
                  {label}
                </Link>
              ))}
            </nav>

            {/* Desktop CTA */}
            <Link
              href="/chat"
              className="hidden md:inline-flex px-6 py-2 text-sm font-medium text-white rounded-full transition
                bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500
                hover:shadow-md hover:scale-105"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Mobile Fullscreen Menu */}
      <div
        className={`fixed inset-0 z-30 md:hidden transition-all duration-500 ${
          isMenuOpen ? "visible opacity-100" : "invisible opacity-0"
        }`}
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-zinc-900/90 backdrop-blur-md"
          onClick={closeMenu}
        />

        {/* Menu Items */}
        <div
          className={`relative h-full flex flex-col items-center justify-center space-y-10 transition ${
            isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
          }`}
        >
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={closeMenu}
              className="text-3xl font-semibold text-white hover:text-indigo-300 transition"
            >
              {label}
            </Link>
          ))}

          <Link
            href="/chat"
            onClick={closeMenu}
            className="px-8 py-3 text-lg font-medium rounded-full text-white
            bg-gradient-to-r from-indigo-600 via-purple-500 to-pink-500
            hover:scale-105 transition shadow-lg shadow-indigo-500/20"
          >
            Get Started
          </Link>
        </div>
      </div>
    </>
  );
}
