"use client";

import { motion } from "framer-motion";
import { Database, Server, Lock } from "lucide-react";

export function Architecture() {
  return (
    <section className="py-24 sm:py-32 bg-card border-t border-border overflow-hidden relative">
      <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/3 w-[600px] h-[600px] bg-accent/10 rounded-full blur-[100px] opacity-50 pointer-events-none" />
      
      <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="text-base font-semibold leading-7 text-accent"
            >
              The Engine Room
            </motion.h2>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
            >
              Büyük ölçekler için tasarlandı.
            </motion.p>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-6 text-lg leading-8 text-foreground/70"
            >
              Verileriniz izole ve güvende. Karmaşık altyapı dertlerini unutun. Enterprise-grade veritabanı mimarisi (PostgreSQL + RLS) ile her şube ve üye verisi birbirinden kriptografik olarak ayrıdır.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mt-10 flex flex-col gap-4"
            >
              <div className="flex items-center gap-3">
                <div className="flex-none rounded-full bg-brand/20 p-1.5 border border-brand/30">
                  <Database className="h-4 w-4 text-brand" />
                </div>
                <span className="text-foreground font-medium">Multi-tenant İzolasyon</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-none rounded-full bg-brand/20 p-1.5 border border-brand/30">
                  <Server className="h-4 w-4 text-brand" />
                </div>
                <span className="text-foreground font-medium">Transactional Outbox Pattern</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-none rounded-full bg-brand/20 p-1.5 border border-brand/30">
                  <Lock className="h-4 w-4 text-brand" />
                </div>
                <span className="text-foreground font-medium">Sıfır Veri Sızıntısı (RLS)</span>
              </div>
            </motion.div>
          </div>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div className="absolute -inset-4 bg-gradient-to-r from-brand/20 to-accent/20 blur-xl opacity-30 rounded-3xl"></div>
            <div className="relative rounded-2xl bg-background border border-border p-8 shadow-2xl font-mono text-sm text-foreground/60">
              <div className="flex gap-2 mb-6">
                <div className="h-3 w-3 rounded-full bg-rose-500/80" />
                <div className="h-3 w-3 rounded-full bg-amber-500/80" />
                <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
              </div>
              <div className="space-y-2">
                <p><span className="text-brand">SELECT</span> * <span className="text-brand">FROM</span> members</p>
                <p><span className="text-brand">WHERE</span> tenant_id = <span className="text-accent">auth.uid()</span></p>
                <p className="text-foreground/30">-- Row Level Security Enforced</p>
                <p className="text-foreground/30">-- Execution Time: 0.003ms</p>
                <br/>
                <p className="text-emerald-400">STATUS: Isolated & Secure</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
