import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { Architecture } from "@/components/Architecture";
import { Metrics } from "@/components/Metrics";
import { Cta } from "@/components/Cta";

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <Architecture />
      <Metrics />
      <Cta />
    </>
  );
}
