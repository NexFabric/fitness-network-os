"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export function Cta() {
  return (
    <section id="demo" className="relative isolate overflow-hidden bg-background py-24 sm:py-32">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,var(--color-brand-deep)_0%,transparent_100%)] opacity-20" />
      <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-card shadow-xl shadow-brand/10 ring-1 ring-border sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />
      
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Kulübünüzü yeni sürüme yükseltin.
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-6 text-lg leading-8 text-foreground/70"
          >
            Klasik yazılımların hantallığından kurtulun. Athletic Ops Console ile tanışın ve operasyonunuzu geleceğe taşıyın.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-10 flex items-center justify-center gap-x-6"
          >
            <a
              href="mailto:hello@gymclubnex.com"
              className="group flex items-center gap-2 rounded-lg bg-brand px-8 py-4 text-base font-semibold text-white shadow-sm hover:bg-brand-deep focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand transition-all"
            >
              Demoyu Başlat
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
