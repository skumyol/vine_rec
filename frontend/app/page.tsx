'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ScanSearch,
  Layers,
  ShieldCheck,
  Gauge,
  Eye,
  CircuitBoard,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const PIPELINE = [
  {
    icon: ScanSearch,
    title: 'Parse SKU',
    desc: 'Producer · appellation · vineyard · vintage extracted from raw text.',
  },
  {
    icon: Eye,
    title: 'Search & screen',
    desc: 'Bing image search via Playwright, OpenCV-filtered for quality.',
  },
  {
    icon: CircuitBoard,
    title: 'OCR + VLM',
    desc: 'EasyOCR cross-checks label text. Gemini & Qwen verify identity.',
  },
  {
    icon: ShieldCheck,
    title: 'Decide',
    desc: 'Score-based verdict. Returns "no image" before risking a wrong one.',
  },
];

const STATS = [
  { label: 'Target accuracy', value: '90%', sub: 'on 10 test SKUs' },
  { label: 'Baseline', value: '50%', sub: 'before this pipeline' },
  { label: 'Per SKU', value: '~25s', sub: 'parallel + cached' },
];

export default function Home() {
  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="VinoBuzz · Photo Sourcing"
        title="Verify wine bottle photos before they ship."
        description="A verification-first pipeline that finds candidate images, validates label identity with OCR + VLM, and refuses to guess. Built for catalogues at scale."
        actions={
          <>
            <Link href="/batch">
              <Button variant="outline">
                <Layers className="h-4 w-4" />
                Run batch
              </Button>
            </Link>
            <Link href="/analyze">
              <Button>
                Analyze a wine
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </>
        }
      />

      {/* Hero stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {STATS.map((s) => (
          <Card key={s.label} className="p-5">
            <div className="text-xs font-medium uppercase tracking-wider text-fg-muted mb-2">
              {s.label}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-semibold tracking-tight text-fg">
                {s.value}
              </span>
              <span className="text-xs text-fg-subtle">{s.sub}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Pipeline visualization */}
      <section>
        <div className="flex items-end justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Pipeline</h2>
            <p className="text-sm text-fg-muted">
              Four stages. Every candidate passes through verification before acceptance.
            </p>
          </div>
          <span className="text-xs text-fg-subtle font-mono">
            parser → retriever → analyzer → scorer
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {PIPELINE.map((step, i) => (
            <Card key={step.title} className="p-5 relative overflow-hidden group hover:shadow-card transition-shadow">
              <div className="absolute top-3 right-3 text-[10px] font-mono text-fg-subtle">
                0{i + 1}
              </div>
              <div className="h-9 w-9 rounded-lg bg-primary-soft text-primary flex items-center justify-center mb-4 ring-1 ring-primary/10">
                <step.icon className="h-4 w-4" strokeWidth={2.2} />
              </div>
              <div className="font-medium text-fg text-sm mb-1">{step.title}</div>
              <p className="text-xs text-fg-muted leading-relaxed">{step.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 group hover:shadow-card transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="h-10 w-10 rounded-lg bg-fg text-bg flex items-center justify-center">
              <ScanSearch className="h-5 w-5" />
            </div>
            <span className="text-2xs font-medium uppercase tracking-wider text-fg-subtle">
              Single
            </span>
          </div>
          <h3 className="text-base font-semibold mb-1">Analyze one wine</h3>
          <p className="text-sm text-fg-muted mb-5">
            Paste a wine name and vintage. Get a verified bottle photo, confidence score, and reasoning trail.
          </p>
          <Link href="/analyze" className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:gap-2.5 transition-all">
            Open analyzer
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>

        <Card className="p-6 group hover:shadow-card transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="h-10 w-10 rounded-lg bg-primary text-primary-fg flex items-center justify-center">
              <Layers className="h-5 w-5" />
            </div>
            <span className="text-2xs font-medium uppercase tracking-wider text-fg-subtle">
              Batch · 10 SKUs
            </span>
          </div>
          <h3 className="text-base font-semibold mb-1">Run the assignment test set</h3>
          <p className="text-sm text-fg-muted mb-5">
            Process the 10 official SKUs. Live progress, accuracy summary, and exportable verdicts.
          </p>
          <Link href="/batch" className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:gap-2.5 transition-all">
            Open batch runner
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>
      </section>
    </div>
  );
}
