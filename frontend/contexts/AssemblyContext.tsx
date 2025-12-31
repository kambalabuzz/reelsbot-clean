"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type AssemblyState = {
  videoId: string;
  progress: number;
  startedAt: number;
};

type AssemblyContextType = {
  activeAssemblies: Map<string, AssemblyState>;
  startAssembly: (videoId: string) => void;
  updateProgress: (videoId: string, progress: number) => void;
  completeAssembly: (videoId: string) => void;
  isAssembling: (videoId: string) => boolean;
  getProgress: (videoId: string) => number;
};

const AssemblyContext = createContext<AssemblyContextType | null>(null);
const ASSEMBLY_TTL_MS = 30 * 60 * 1000;

export function AssemblyProvider({ children }: { children: ReactNode }) {
  const [activeAssemblies, setActiveAssemblies] = useState<Map<string, AssemblyState>>(new Map());

  const isStale = (assembly: AssemblyState) => Date.now() - assembly.startedAt > ASSEMBLY_TTL_MS;

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("active_assemblies");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          const map = new Map(Object.entries(parsed).map(([k, v]: [string, any]) => [k, v as AssemblyState]));
          const cleaned = new Map(Array.from(map.entries()).filter(([, value]) => !isStale(value)));
          setActiveAssemblies(cleaned);
        } catch (e) {
          console.error("Failed to parse assemblies:", e);
        }
      }
    }
  }, []);

  // Save to localStorage whenever state changes
  useEffect(() => {
    if (typeof window !== "undefined") {
      const obj = Object.fromEntries(activeAssemblies);
      localStorage.setItem("active_assemblies", JSON.stringify(obj));
    }
  }, [activeAssemblies]);

  const startAssembly = (videoId: string) => {
    setActiveAssemblies(prev => {
      const next = new Map(prev);
      next.set(videoId, {
        videoId,
        progress: 5,
        startedAt: Date.now(),
      });
      return next;
    });
  };

  const updateProgress = (videoId: string, progress: number) => {
    setActiveAssemblies(prev => {
      const next = new Map(prev);
      const existing = next.get(videoId);
      if (existing) {
        next.set(videoId, { ...existing, progress });
      }
      return next;
    });
  };

  const completeAssembly = (videoId: string) => {
    setActiveAssemblies(prev => {
      const next = new Map(prev);
      next.delete(videoId);
      return next;
    });
  };

  const isAssembling = (videoId: string) => {
    const assembly = activeAssemblies.get(videoId);
    return !!assembly && !isStale(assembly);
  };

  const getProgress = (videoId: string) => {
    const assembly = activeAssemblies.get(videoId);
    if (!assembly || isStale(assembly)) return 0;
    return assembly.progress || 0;
  };

  return (
    <AssemblyContext.Provider
      value={{
        activeAssemblies,
        startAssembly,
        updateProgress,
        completeAssembly,
        isAssembling,
        getProgress,
      }}
    >
      {children}
    </AssemblyContext.Provider>
  );
}

export function useAssembly() {
  const context = useContext(AssemblyContext);
  if (!context) {
    throw new Error("useAssembly must be used within AssemblyProvider");
  }
  return context;
}
