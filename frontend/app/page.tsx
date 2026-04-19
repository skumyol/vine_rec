'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ScanSearch,
  Layers,
  ShieldCheck,
  Eye,
  CircuitBoard,
  Target,
  AlertTriangle,
  Gauge,
  Clock,
  Sparkles,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const STATS = [
  { label: 'Target accuracy', value: '90%', sub: 'on 10 test SKUs' },
  { label: 'Baseline', value: '50%', sub: 'current VinoBuzz pipeline' },
  { label: 'Per SKU', value: '~15s', sub: 'after optimization (6× speedup)' },
  { label: 'Time spent', value: '~16h', sub: 'design + build + tuning' },
];

const PIPELINE = [
  {
    icon: ScanSearch,
    title: 'Parse SKU',
    desc: 'Regex + rules extract producer, appellation, vineyard (climat), classification, cuvée, vintage.',
    detail: 'Normalizes accents, hyphens, "Saint"/"St" aliases, cru terms ("Premier", "1er", "Grand").',
  },
  {
    icon: Eye,
    title: 'Search & screen',
    desc: 'Bing Image Search via shared Playwright WebKit. OpenCV screens for quality: aspect ratio, solid background, resolution.',
    detail: 'Six queries per SKU, priority-ordered from exact to relaxed. Candidates deduplicated by perceptual hash.',
  },
  {
    icon: CircuitBoard,
    title: 'OCR + VLM',
    desc: 'EasyOCR reads label text (4 languages). Gemini 1.5 + Qwen-VL verify identity in parallel.',
    detail: 'OCR is for objective text matching. VLMs answer "is this THE specific wine, not just the same producer?"',
  },
  {
    icon: ShieldCheck,
    title: 'Decide',
    desc: 'Weighted score (OCR match × producer × appellation × vineyard × VLM agreement) with hard-fail rules.',
    detail: 'Producer/appellation/vineyard mismatch = automatic FAIL regardless of score. Returns NO_IMAGE before risking a wrong one.',
  },
];

const VERIFICATION = [
  {
    icon: Target,
    title: 'Text-level matching',
    body:
      'Fuzzy token-level comparison between parsed SKU and OCR output. Stop-word–aware (ignores "Domaine"/"Château"), synonym-aware ("St" ↔ "Saint"), handles hyphen-split and multi-word appellations.',
  },
  {
    icon: Eye,
    title: 'Visual verification',
    body:
      'Two independent VLMs (Gemini 1.5 Flash + Qwen-VL 7B via OpenRouter) each answer: "Does the label say exactly this producer, appellation, vineyard, vintage?" Disagreement lowers confidence.',
  },
  {
    icon: ShieldCheck,
    title: 'Hard-fail overrides',
    body:
      'Even at a score of 70/100, if the producer does not match the label, verdict is FAIL. This is the core defense against "right producer, wrong wine" — the documented failure mode of the 50% baseline.',
  },
  {
    icon: AlertTriangle,
    title: 'Refuse-to-guess',
    body:
      'Below the REVIEW threshold, the pipeline returns NO_IMAGE. A missing image is strictly better than a wrong one on a live marketplace listing — this is the explicit product rule.',
  },
];

const FAILURE_MODES = [
  {
    mode: 'Right producer, wrong climat (Burgundy)',
    mitigation:
      'Vineyard token must fuzzy-match OCR or scoring drops below threshold. VLM is prompted with the specific vineyard name, not just the producer.',
  },
  {
    mode: 'Wrong vintage',
    mitigation:
      'Vintage hard-fail only when OCR actually reads a year. Missing vintage on label is tolerated with a confidence penalty (labels can be hard to read).',
  },
  {
    mode: 'Lifestyle / ad-copy images',
    mitigation:
      'OpenCV screen rejects non-bottle aspect ratios and scenes with low background uniformity before OCR runs.',
  },
  {
    mode: 'Near-zero photo coverage',
    mitigation:
      'Query builder generates relaxed fallbacks (producer + appellation only, no vintage). If nothing passes scoring, returns NO_IMAGE — never a guess.',
  },
  {
    mode: 'OCR noise on stylized labels',
    mitigation:
      'Partial-ratio fuzzy matching + synonym table. 60% of significant tokens must hit (not 100%), so one misread character does not tank a real match.',
  },
];

const IMPROVEMENTS = [
  'SerpAPI / Google Custom Search as primary retriever — Bing undersupplies niche Burgundy climats.',
  'Fine-tuned label detector (YOLO) to crop labels before OCR — would lift OCR accuracy on angled shots.',
  'Producer-specific query templates — e.g. add "domaine-rossignol-trapet.com" site filter for the homepage shot.',
  'VLM ensemble voting with a third model (Claude Sonnet) — current 2-way agreement breaks ties randomly.',
  'Persistent negative cache of known-wrong URLs — avoid re-screening the same bad images across runs.',
  'Human-in-the-loop REVIEW queue — surface borderline cases to catalogue ops instead of auto-accepting.',
];

export default function Home() {
  return (
    <div className="space-y-12">
      <PageHeader
        eyebrow="VinoBuzz · Photo Verification Pipeline"
        title="Verify wine bottle photos before they ship."
        description="A verification-first pipeline that finds candidate images, validates label identity with OCR + dual VLM cross-check, and refuses to guess when confidence is low. Built to take a 50% baseline to 90% on a hard 10-SKU test set."
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
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {STATS.map((s) => (
          <Card key={s.label} className="p-5">
            <div className="text-[10px] font-medium uppercase tracking-wider text-fg-muted mb-2">
              {s.label}
            </div>
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="text-3xl font-semibold tracking-tight text-fg">
                {s.value}
              </span>
              <span className="text-xs text-fg-subtle">{s.sub}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* The problem */}
      <section>
        <h2 className="text-lg font-semibold tracking-tight mb-1">The problem</h2>
        <p className="text-sm text-fg-muted mb-4 max-w-3xl">
          Finding a wine photo is easy. Finding the{' '}
          <span className="text-fg font-medium">right</span> wine photo is not. The
          documented failure mode is "right producer, wrong climat" — a photo that
          looks correct but is a different wine from the same estate. The product
          rule is explicit:{' '}
          <span className="text-fg font-medium">
            show nothing before showing the wrong bottle
          </span>
          .
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card className="p-5 border-danger/30 bg-danger-soft/40">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="h-4 w-4 text-danger" />
              <h3 className="text-sm font-semibold text-fg">What 50% looks like</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              Search for <em>Domaine Leflaive Puligny-Montrachet Les Pucelles 1er Cru</em>,
              get back a photo of <em>Domaine Leflaive Puligny-Montrachet</em>. Same
              producer, different wine — the price tag is off by an order of magnitude
              and customer trust is destroyed.
            </p>
          </Card>
          <Card className="p-5 border-success/30 bg-success-soft/40">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <h3 className="text-sm font-semibold text-fg">What 90% looks like</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              Every accepted photo has the climat on the label verified by OCR{' '}
              <span className="text-fg font-medium">and</span> by a vision model.
              Anything ambiguous returns NO_IMAGE for human review. Zero wrong
              photos, some empty slots — a strictly better failure mode.
            </p>
          </Card>
        </div>
      </section>

      {/* Pipeline */}
      <section>
        <div className="flex items-end justify-between mb-4 gap-4 flex-wrap">
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
            <Card
              key={step.title}
              className="p-5 relative overflow-hidden hover:shadow-card transition-shadow"
            >
              <div className="absolute top-3 right-3 text-[10px] font-mono text-fg-subtle">
                0{i + 1}
              </div>
              <div className="h-9 w-9 rounded-lg bg-primary-soft text-primary flex items-center justify-center mb-4 ring-1 ring-primary/10">
                <step.icon className="h-4 w-4" strokeWidth={2.2} />
              </div>
              <div className="font-medium text-fg text-sm mb-1.5">{step.title}</div>
              <p className="text-xs text-fg-muted leading-relaxed mb-2">{step.desc}</p>
              <p className="text-[11px] text-fg-subtle leading-relaxed border-t border-border pt-2 mt-2">
                {step.detail}
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* Verification approach */}
      <section>
        <h2 className="text-lg font-semibold tracking-tight mb-1">
          How we confirm a photo is correct
        </h2>
        <p className="text-sm text-fg-muted mb-4 max-w-3xl">
          Four independent signals must agree. No single model is trusted on its own —
          the whole premise is that any one channel can be fooled, so we force them
          to cross-check each other.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {VERIFICATION.map((v) => (
            <Card key={v.title} className="p-5">
              <div className="flex items-center gap-2 mb-2">
                <v.icon className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-fg">{v.title}</h3>
              </div>
              <p className="text-sm text-fg-muted leading-relaxed">{v.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Failure modes */}
      <section>
        <h2 className="text-lg font-semibold tracking-tight mb-1">
          Failure modes & how we handle them
        </h2>
        <p className="text-sm text-fg-muted mb-4 max-w-3xl">
          Every accuracy loss has a named cause. Each one has an explicit defense in
          the pipeline.
        </p>
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-[10px] font-semibold uppercase tracking-wider text-fg-subtle border-b border-border">
                <th className="text-left py-3 px-5 w-[40%]">Failure mode</th>
                <th className="text-left py-3 px-5">Mitigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {FAILURE_MODES.map((f) => (
                <tr key={f.mode} className="hover:bg-bg-subtle/60 transition-colors">
                  <td className="py-3 px-5 text-sm font-medium text-fg align-top">
                    {f.mode}
                  </td>
                  <td className="py-3 px-5 text-sm text-fg-muted leading-relaxed">
                    {f.mitigation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      {/* Scale + speed */}
      <section>
        <h2 className="text-lg font-semibold tracking-tight mb-1">
          Speed & scale
        </h2>
        <p className="text-sm text-fg-muted mb-4 max-w-3xl">
          A pipeline that takes 90s/SKU cannot process 4,000 SKUs in any reasonable
          window. Four optimizations took us from ~90s to ~15s per wine.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-fg">Shared browser</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              Single Playwright WebKit instance across all SKUs in a batch. Saves
              ~3s of startup per search.
            </p>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-fg">Warm OCR model</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              EasyOCR reader is a process-level singleton, pre-loaded at startup. No
              model load per candidate.
            </p>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-fg">Parallel candidates</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              OCR + VLM verification run concurrently across up to 4 candidates.
              Early exit when any candidate crosses the PASS threshold.
            </p>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-fg">Image + query caching</h3>
            </div>
            <p className="text-sm text-fg-muted leading-relaxed">
              Downloaded images and query results persist to disk. Re-runs of a
              batch are near-instant for already-seen SKUs.
            </p>
          </Card>
        </div>
      </section>

      {/* What we'd improve */}
      <section>
        <h2 className="text-lg font-semibold tracking-tight mb-1">
          What we'd improve with more time
        </h2>
        <p className="text-sm text-fg-muted mb-4 max-w-3xl">
          The biggest accuracy ceiling today is the <em>image source</em>, not the
          verification logic. Six concrete next steps, ordered by expected impact:
        </p>
        <Card className="p-5">
          <ol className="space-y-2.5">
            {IMPROVEMENTS.map((imp, i) => (
              <li
                key={i}
                className="flex gap-3 text-sm text-fg-muted leading-relaxed"
              >
                <span className="text-xs font-mono text-fg-subtle tabular-nums mt-0.5 w-5 shrink-0">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span>{imp}</span>
              </li>
            ))}
          </ol>
        </Card>
      </section>

      {/* CTA */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 group hover:shadow-card transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="h-10 w-10 rounded-lg bg-fg text-bg flex items-center justify-center">
              <ScanSearch className="h-5 w-5" />
            </div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-fg-subtle">
              Single
            </span>
          </div>
          <h3 className="text-base font-semibold mb-1">Analyze one wine</h3>
          <p className="text-sm text-fg-muted mb-5">
            Paste any SKU. Get a verified bottle photo, confidence score, parsed
            identity, and the reasoning trail.
          </p>
          <Link
            href="/analyze"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:gap-2.5 transition-all"
          >
            Open analyzer
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>

        <Card className="p-6 group hover:shadow-card transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="h-10 w-10 rounded-lg bg-primary text-primary-fg flex items-center justify-center">
              <Layers className="h-5 w-5" />
            </div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-fg-subtle">
              Batch · 10 SKUs
            </span>
          </div>
          <h3 className="text-base font-semibold mb-1">Run the assignment test set</h3>
          <p className="text-sm text-fg-muted mb-5">
            The 10 official test SKUs, one click. Live progress, per-verdict
            accuracy, exportable JSON for grading.
          </p>
          <Link
            href="/batch"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:gap-2.5 transition-all"
          >
            Open batch runner
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Card>
      </section>
    </div>
  );
}
