import React from 'react';
import { Check, Sparkles, Cpu, ShieldCheck, FileCheck, Lock, Scale } from 'lucide-react';

export default function PricingSection({ onSelectPlan }) {
  return (
    <section id="pricing" className="max-w-5xl mx-auto mb-12 px-2 content-visibility-auto">
      <div className="text-center mb-8">
        <div className="inline-block mb-2">
          <span className="calm-pill">
            <Scale className="w-3.5 h-3.5 text-blue-600" />
            <span>High-Impact Value Packs</span>
          </span>
        </div>
        <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Transparent Audit Credit Packs</h3>
        <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-xl mx-auto">
          Pay once for what you audit. No forced subscriptions or hidden recurring charges. Credits never expire.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Free Starter */}
        <div className="liquid-glass-card p-6 flex flex-col justify-between border-slate-200">
          <div>
            <span className="doc-tag text-[10px] px-2 py-0.5 mb-2 bg-slate-100 text-slate-700">STARTER</span>
            <h4 className="font-bold text-slate-900 text-lg">Free Starter</h4>
            <div className="text-2xl font-black text-slate-800 my-2">
              ₹0 <span className="text-xs font-normal text-slate-500">/ forever</span>
            </div>
            <p className="text-xs text-slate-500 mb-4">Essential risk detection for immediate contract checks.</p>
            <ul className="space-y-2.5 text-xs text-slate-600">
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> <strong>3 Complete Document Audits</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> Standard 4-Pillar Playbook Check</li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> Real-Time Risk Level Highlighting</li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> Confidential Document Processing</li>
              <li className="flex items-center gap-2 text-slate-400">✕ Attorney Counter-Clause Drafting</li>
              <li className="flex items-center gap-2 text-slate-400">✕ Official Signed Audit PDF Certificate</li>
            </ul>
          </div>
          <div className="mt-6 p-2.5 bg-slate-100/90 rounded-xl text-center text-xs font-bold text-slate-600">
            Active on Sign Up
          </div>
        </div>

        {/* Standard Pack (10 Uses - ₹199) */}
        <div className="liquid-glass-card p-6 border-blue-400 flex flex-col justify-between shadow-lg relative bg-gradient-to-b from-white to-sky-50/40">
          <div className="absolute top-0 right-0 bg-blue-600 text-white text-[9px] font-extrabold px-3 py-0.5 rounded-bl-xl uppercase tracking-wider">
            MOST POPULAR
          </div>
          <div>
            <span className="doc-tag text-[10px] px-2 py-0.5 mb-2 bg-blue-100 text-blue-800 border-blue-200">POPULAR</span>
            <h4 className="font-extrabold text-slate-900 text-lg">Standard Pack</h4>
            <div className="text-2xl font-black text-blue-700 my-2">
              ₹199 <span className="text-xs font-normal text-slate-500">/ 10 Audits</span>
            </div>
            <p className="text-xs text-blue-600 font-bold mb-4">Only ₹19.9 per audit • Credits Never Expire</p>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> <strong>+10 Legal Document Audits</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> <strong>Attorney Counter-Draft Clauses</strong> (Copy & paste ready)</li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> <strong>5 Specialized Legal Disciplines</strong> (Property, Medical, Crime, Corporate, Estate)</li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> Multilingual Audio Briefings (EN, HI, BN, TA)</li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" /> 24/7 AI Legal Counsel Consultation</li>
            </ul>
          </div>
          <button
            onClick={() => onSelectPlan({ name: 'Standard Pack (10 Uses)', price: 199, uses: 10, engine: 'Standard AI' })}
            className="w-full mt-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Unlock 10 Audits • ₹199</span>
          </button>
        </div>

        {/* Pro Power Pack (30 Uses - ₹399) */}
        <div className="liquid-glass-card p-6 border-2 border-indigo-500 flex flex-col justify-between shadow-xl relative overflow-hidden bg-gradient-to-b from-white to-indigo-50/40">
          <div className="absolute top-0 right-0 bg-gradient-to-l from-indigo-600 to-blue-600 text-white text-[9px] font-extrabold px-3 py-0.5 rounded-bl-xl uppercase tracking-wider">
            ⭐ BEST VALUE • SAVE 60%
          </div>
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <span className="doc-tag text-[10px] px-2 py-0.5 bg-indigo-100 text-indigo-800 border-indigo-200 font-bold">ENTERPRISE GRADE</span>
              <span className="text-[10px] text-indigo-700 font-extrabold flex items-center gap-1 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
                <Cpu className="w-3 h-3 text-indigo-600" /> Advanced Reasoning
              </span>
            </div>
            <h4 className="font-extrabold text-slate-900 text-lg">Pro Power Pack</h4>
            <div className="text-2xl font-black text-indigo-700 my-2">
              ₹399 <span className="text-xs font-normal text-slate-500">/ 30 Audits</span>
            </div>
            <p className="text-xs text-indigo-600 font-bold mb-4">Only ₹13.3 per audit • Maximum Savings</p>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> <strong>+30 Comprehensive Audits</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> <strong>Zero-Cloud Retention Document Shredding</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> <strong>Attorney Counter-Drafting with Negotiation Rationale</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> <strong>Official Legal Risk Scorecard PDF Export</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> <strong>Audit History with Expiration Reminders</strong></li>
              <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" /> Deep Legal Clause Reasoning & Flagging</li>
            </ul>
          </div>
          <button
            onClick={() => onSelectPlan({ name: 'Pro Power Pack (30 Uses)', price: 399, uses: 30, engine: 'Pro AI' })}
            className="w-full mt-6 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Unlock 30 Audits • ₹399</span>
          </button>
        </div>

      </div>

      {/* WHY PAY? CONVERSION ASSURANCE BANNER */}
      <div className="mt-8 p-4 rounded-2xl bg-gradient-to-r from-sky-50 via-blue-50 to-indigo-50 border border-blue-200 text-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-blue-600 text-white flex-shrink-0">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h5 className="font-extrabold text-slate-900 text-sm">Why Users Upgrade to LegalEase Pro</h5>
            <p className="text-slate-600 text-xs">
              Detecting unfair clauses is only half the battle. Pro gives you <strong>exact copy-paste attorney replacement clauses</strong>, <strong>statutory defense citations</strong>, and <strong>100% private on-premise document scanning</strong>.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="px-3 py-1.5 bg-white text-emerald-700 font-extrabold rounded-xl border border-emerald-200 shadow-xs flex items-center gap-1">
            <Lock className="w-3.5 h-3.5" /> Zero-Retention Guarantee
          </span>
        </div>
      </div>

    </section>
  );
}
