import React from 'react';
import { Shield, Database, Cpu, Scale } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-16 pt-8 pb-12 border-t border-slate-200/80 text-center text-slate-500">
      <div className="max-w-4xl mx-auto px-4">
        
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
          Technical Architecture & Security
        </h4>
        <p className="text-xs text-slate-500 max-w-xl mx-auto mb-4 leading-relaxed">
          Powered by Google Gemini GenAI API models with encrypted transit and transient memory buffers. User profiles and audit logs are managed via MongoDB Atlas.
        </p>

        <div className="flex flex-wrap justify-center gap-4 text-xs font-medium text-slate-600 mb-6">
          <span className="flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5 text-blue-600" /> Google Gemini API</span>
          <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5 text-emerald-600" /> MongoDB Atlas</span>
          <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-indigo-600" /> Client-Side AES-GCM</span>
          <span className="flex items-center gap-1.5"><Scale className="w-3.5 h-3.5 text-sky-600" /> Statutory Legal Playbook</span>
        </div>


        <p className="text-[11px] text-slate-400">
          © 2026 LegalEase. Built for contract compliance and legal risk analysis.
        </p>

      </div>
    </footer>
  );
}
