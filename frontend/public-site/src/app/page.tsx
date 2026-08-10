import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { Architecture } from "@/components/Architecture";
import { Pricing } from "@/components/Pricing";
import { Metrics } from "@/components/Metrics";
import { Cta } from "@/components/Cta";

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <Architecture />
      <Pricing />
      <Metrics />
      <Cta />
    </>
  );
}
