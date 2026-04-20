'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Sparkles,
  ScanSearch,
  Layers,
  History,
  Wine,
  Activity,
  Github,
} from 'lucide-react';
import { cn } from '@/lib/cn';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

const NAV = [
  { href: '/', label: 'Overview', icon: Sparkles },
  { href: '/analyze', label: 'Analyze', icon: ScanSearch },
  { href: '/batch', label: 'Batch', icon: Layers },
  { href: '/results', label: 'History', icon: History },
];

interface HealthStatus {
  status: string;
  services: Record<string, { available?: boolean; configured?: boolean }>;
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`);
        if (r.ok && !cancelled) setHealth(await r.json());
      } catch {}
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const dotColor =
    health?.status === 'healthy'
      ? 'bg-success'
      : health?.status === 'degraded'
      ? 'bg-warning'
      : 'bg-fg-subtle';

  return (
    <div className="min-h-screen flex bg-bg-subtle">
      {/* Sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 flex-col bg-sidebar-bg text-sidebar-fg border-r border-sidebar-border">
        <div className="px-5 py-5 border-b border-sidebar-border">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shadow-glow-primary">
              <Wine className="h-4 w-4 text-primary-fg" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold text-sidebar-fg-active tracking-tight">
                VinoVerify
              </span>
              <span className="text-[10px] text-sidebar-fg/60 font-medium uppercase tracking-wider">
                Photo Pipeline
              </span>
            </div>
          </Link>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== '/' && pathname?.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                  active
                    ? 'bg-sidebar-active text-sidebar-fg-active font-medium'
                    : 'hover:bg-sidebar-hover hover:text-sidebar-fg-active'
                )}
              >
                <Icon className={cn('h-4 w-4', active ? 'text-primary' : '')} strokeWidth={2} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-sidebar-border space-y-2">
          <div className="px-3 py-2 rounded-md bg-sidebar-hover/40">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-medium uppercase tracking-wider text-sidebar-fg/60">
                System
              </span>
              <span className="flex items-center gap-1.5 text-xs">
                <span className={cn('h-1.5 w-1.5 rounded-full animate-pulse', dotColor)} />
                <span className="text-sidebar-fg-active capitalize">
                  {health?.status ?? 'checking'}
                </span>
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {health?.services &&
                Object.entries(health.services).map(([name, s]) => {
                  const ok = s.available ?? s.configured ?? false;
                  return (
                    <span
                      key={name}
                      title={`${name}: ${ok ? 'ready' : 'unavailable'}`}
                      className={cn(
                        'text-[10px] px-1.5 py-0.5 rounded ring-1',
                        ok
                          ? 'text-success ring-success/20 bg-success/10'
                          : 'text-fg-subtle ring-sidebar-border bg-sidebar-bg'
                      )}
                    >
                      {name}
                    </span>
                  );
                })}
            </div>
          </div>

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 text-xs text-sidebar-fg/60 hover:text-sidebar-fg-active transition-colors"
          >
            <Github className="h-3.5 w-3.5" />
            View source
          </a>
        </div>
      </aside>

      {/* Mobile topbar */}
      <div className="md:hidden fixed top-0 inset-x-0 h-14 bg-sidebar-bg text-sidebar-fg-active flex items-center justify-between px-4 z-40 border-b border-sidebar-border">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
            <Wine className="h-4 w-4 text-primary-fg" />
          </div>
          <span className="font-semibold text-sm">VinoVerify</span>
        </Link>
        <nav className="flex gap-1">
          {NAV.map(({ href, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'p-2 rounded-md',
                  active ? 'bg-sidebar-active text-primary' : 'text-sidebar-fg'
                )}
              >
                <Icon className="h-4 w-4" />
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main */}
      <main className="flex-1 min-w-0 pt-14 md:pt-0">
        <div className="max-w-7xl mx-auto p-6 md:p-10 animate-fade-in">{children}</div>
      </main>
    </div>
  );
}
