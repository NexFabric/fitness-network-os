"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

const defaultStats = [
  { id: 1, name: "Uptime", value: "99.9%" },
  { id: 2, name: "Veri Kaybı", value: "Sıfır" },
  { id: 3, name: "Günlük Geçiş", value: "10K+" },
];

export function Metrics() {
  const [stats, setStats] = useState(defaultStats);

  useEffect(() => {
    fetch(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/telemetry/public")
      .then(res => res.json())
      .then(data => {
        setStats([
          { id: 1, name: "Uptime", value: data.uptime || "99.99%" },
          { id: 2, name: "Veri Kaybı", value: data.data_loss_status || "Sıfır" },
          { id: 3, name: "Günlük Geçiş", value: data.daily_transitions || "12.4K+" },
        ]);
      })
      .catch(err => console.error("Telemetry fetch error:", err));
  }, []);

  return (
    <section className="bg-background py-24 sm:py-32 relative overflow-hidden border-t border-border">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-brand/10 blur-[100px] rounded-full pointer-events-none"></div>
      
      <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-2xl lg:max-w-none text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 rounded border border-brand/20 bg-brand/5 px-3 py-1 text-sm font-medium text-brand mb-6"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
            Sistem Durumu
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Kanıtlanmış Performans
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-4 text-lg text-foreground/60"
          >
            Sayılar yalan söylemez. Operasyonlarınızı kesintisiz sürdürün.
          </motion.p>
          
          <dl className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3">
            {stats.map((stat, index) => (
              <motion.div 
                key={stat.id} 
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex flex-col bg-background/50 backdrop-blur-md border border-brand/20 hover:border-brand/50 p-8 rounded-xl transition-all duration-300 shadow-[0_0_15px_rgba(13,148,136,0.05)] hover:shadow-[0_0_30px_rgba(13,148,136,0.15)] group relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-brand/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <dt className="text-sm font-mono leading-6 text-foreground/60 uppercase tracking-wider relative z-10">{stat.name}</dt>
                <dd className="order-first text-4xl font-bold tracking-tight text-foreground group-hover:text-brand transition-colors sm:text-5xl mb-4 relative z-10">{stat.value}</dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}
