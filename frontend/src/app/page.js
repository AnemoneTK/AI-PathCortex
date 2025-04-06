import Head from "next/head";
import Image from "next/image";
import Link from "next/link";
import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import Personalities from "@/components/landing/Personalities";
import Technology from "@/components/landing/Technology";
import CTA from "@/components/landing/CTA";
import Footer from "@/components/landing/Footer";
export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <Hero />
      <Features />
      <Personalities />
      <Technology />
      <CTA />
      <Footer />
    </div>
  );
}
