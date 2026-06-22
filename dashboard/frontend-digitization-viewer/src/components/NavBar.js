"use client"

import React from "react"
import Link from "next/link"

export default function Navbar({ activePage, setActivePage }) {
  return (
    <nav className="w-full h-12 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
      {/* Logo / Title */}
      <div className="text-xl font-bold text-gray-800">
        Document Pipeline
      </div>

      {/* Nav Items */}
      <div className="flex space-x-4">
        <Link
            href="/stats"
        >
            <button
            className={`px-4 py-2 rounded-md font-medium transition ${
                activePage === "stats"
                ? "bg-gray-200 text-gray-900"
                : "text-gray-600 hover:bg-gray-100"
            }`}
            //   onClick={() => setActivePage("stats")}
            >
            Stats
            </button>
        </Link>

        <Link
            href="/viewer"
        >
        <button
          className={`px-4 py-2 rounded-md font-medium transition ${
            activePage === "viewer"
              ? "bg-gray-200 text-gray-900"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          Document Viewer
        </button>
        </Link>

        <Link href="/token-analysis">
          <button
            className={`px-4 py-2 rounded-md font-medium transition ${
              activePage === "token-analysis"
                ? "bg-gray-200 text-gray-900"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            Token Analysis
          </button>
        </Link>
      </div>
    </nav>
  )
}