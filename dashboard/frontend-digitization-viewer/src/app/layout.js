import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/NavBar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Digitization Viewer",
  description: "Monitor and control your digitization pipeline",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
  <body
    className={`${geistSans.variable} ${geistMono.variable} flex flex-col h-screen antialiased bg-zinc-50 font-sans dark:bg-black`}
  >
    <Navbar />
    <main className="flex-1 flex w-full overflow-hidden">
      {children}
    </main>
  </body>
</html>
  );
}
