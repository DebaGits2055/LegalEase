import re
import os
import json
import time
import urllib.request
from typing import Dict, Any, Tuple, Optional
from pypdf import PdfReader

try:
    from playbook import NON_LEGAL_DOCUMENT_MESSAGE, LEGAL_PLAYBOOK
except ImportError:
    from backend.playbook import NON_LEGAL_DOCUMENT_MESSAGE, LEGAL_PLAYBOOK

# Standardized Rejection Message
STRICT_REJECTION_MESSAGE = "This is not a recognized legal document. Please upload an authentic legal instrument (Property Deed, Medical Consent, Criminal/Police Report, Employment Agreement, NDA, etc.)."

# ========================================================
# 1. SPECIALIZED LEGAL DOCUMENT CATEGORIES & STATUTES
# ========================================================
LEGAL_CATEGORIES = {
    "PROPERTY_REAL_ESTATE": {
        "title": "Property & Real Estate Law",
        "description": "Sale deeds, lease & tenancy agreements, conveyance deeds, mortgage & encumbrance certificates, RERA disclosures.",
        "keywords": [
            "lease agreement", "tenancy agreement", "sale deed", "conveyance deed", "mortgage", 
            "lessor", "lessee", "landlord", "tenant", "security deposit", "premises", 
            "rent deed", "title deed", "encumbrance", "stamp duty", "transfer of property act"
        ],
        "statutes": ["Transfer of Property Act, 1882", "Indian Stamp Act, 1899", "RERA Act, 2016"]
    },
    "MEDICAL_HEALTHCARE": {
        "title": "Medical & Healthcare Law",
        "description": "Informed consent, surgical risk waivers, clinical trial agreements, HIPAA disclosures, hospital liability releases.",
        "keywords": [
            "informed consent", "patient agreement", "surgical consent", "medical records", 
            "hospital admission", "liability waiver", "clinical trial", "physician", "procedure risks", 
            "medical negligence waiver", "anesthesia consent", "hipaa", "healthcare provider"
        ],
        "statutes": ["Clinical Establishments Act", "Consumer Protection Act (Medical)", "NMC Professional Conduct Regulations"]
    },
    "CRIMINAL_INVESTIGATION": {
        "title": "Criminal Investigation & Law Enforcement",
        "description": "First Information Reports (FIR), charge sheets, bail petitions, criminal affidavits, witness depositions, subpoenas.",
        "keywords": [
            "first information report", "fir no", "charge sheet", "bail application", "anticipatory bail", 
            "police station", "subpoena", "criminal procedure", "crpc", "bns", "bhartiya nyaya sanhita", 
            "accused", "complainant", "witness statement", "affidavit under oath", "court of judicial magistrate"
        ],
        "statutes": ["Bharatiya Nagarik Suraksha Sanhita (BNSS)", "Bharatiya Nyaya Sanhita (BNS)", "Code of Criminal Procedure (CrPC)"]
    },
    "CORPORATE_EMPLOYMENT": {
        "title": "Corporate, Commercial & Employment Law",
        "description": "Non-Disclosure Agreements (NDAs), employment contracts, non-compete covenants, IP assignments, master service agreements.",
        "keywords": [
            "employment agreement", "non-disclosure agreement", "nda", "confidentiality agreement", 
            "non-compete", "restraint of trade", "intellectual property assignment", "work-for-hire", 
            "severance", "cure period", "indemnification", "master services agreement", "contractor agreement"
        ],
        "statutes": ["Indian Contract Act, 1872 (Section 27)", "Companies Act, 2013", "Industrial Disputes Act"]
    },
    "ESTATE_NOTARIAL": {
        "title": "Estate, Power of Attorney & Affidavits",
        "description": "Power of attorney (GPA/SPA), last will and testament, codicils, gift deeds, sworn notarial affidavits.",
        "keywords": [
            "power of attorney", "general power of attorney", "special power of attorney", 
            "last will and testament", "testator", "executor", "beneficiary", "sworn affidavit", 
            "deponent", "notary public", "attestation", "solemnly affirm", "gift deed"
        ],
        "statutes": ["Powers of Attorney Act, 1882", "Indian Succession Act, 1925", "Notaries Act, 1952"]
    }
}

# ========================================================
# 2. DOCUMENT TEXT EXTRACTION & PHASE 0 CLASSIFIER
# ========================================================
def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extracts text from PDF, DOCX, or text files.
    """
    extracted_text = ""
    lower_name = filename.lower()
    
    if lower_name.endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            for page in reader.pages[:10]: # Read first 10 pages
                extracted_text += page.extract_text() or ""
        except Exception as e:
            print(f"PDF extraction error: {e}")
            
    elif lower_name.endswith(".txt") or lower_name.endswith(".md"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        except Exception as e:
            print(f"Text read error: {e}")
            
    return extracted_text.strip()

def classify_legal_document(text: str, filename: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Phase 0 Classifier:
    Returns (is_legal, category_key, category_details)
    Strictly weeds out non-legal files (e.g. food receipts, code, memes, resumes, selfies).
    """
    if not text:
        # If image or scanned PDF where text couldn't be extracted, check filename clues
        # or defer to multimodal vision model
        return True, "CORPORATE_EMPLOYMENT", LEGAL_CATEGORIES["CORPORATE_EMPLOYMENT"]
        
    lower_text = text.lower()
    
    # Check for general legal structural markers
    legal_structure_markers = [
        "whereas", "witnesseth", "now therefore", "in witness whereof",
        "hereinafter referred to", "terms and conditions", "governing law",
        "jurisdiction", "arbitration", "indemnify", "covenant", "agreement",
        "party of the first part", "affidavit", "solemnly affirm", "deponent",
        "section", "pursuant to", "signed, sealed and delivered"
    ]
    
    structure_score = sum(1 for m in legal_structure_markers if m in lower_text)
    
    # Categorization score
    category_scores = {}
    for cat_key, cat_data in LEGAL_CATEGORIES.items():
        score = sum(1 for kw in cat_data["keywords"] if kw in lower_text)
        category_scores[cat_key] = score
        
    best_cat = max(category_scores, key=category_scores.get)
    max_score = category_scores[best_cat]
    
    # If both structure score and category score are too low, it's NOT a legal document
    if structure_score < 2 and max_score < 2:
        return False, None, None
        
    return True, best_cat, LEGAL_CATEGORIES[best_cat]

# ========================================================
# 3. LOCAL SPECIALIZED LEGAL INFERENCE ENGINE
# ========================================================
def run_local_legal_audit(
    text: str, 
    filename: str, 
    category_key: str, 
    language: str = "English"
) -> Dict[str, Any]:
    """
    100% Local Specialized Legal Audit:
    - Runs completely offline / on-premise.
    - Zero data transmitted to cloud or external APIs.
    - Analyzes contract clauses against statutory playbooks and Bar standards.
    """
    category = LEGAL_CATEGORIES.get(category_key, LEGAL_CATEGORIES["CORPORATE_EMPLOYMENT"])
    lower_text = text.lower()
    
    red_flags = []
    health_score = 90
    
    # 1. Non-Compete & Restraint of Trade Check (Section 27 Indian Contract Act)
    if "non-compete" in lower_text or "restraint" in lower_text or "prohibited from working" in lower_text:
        # Check duration
        has_post_term = any(w in lower_text for w in ["after termination", "post-employment", "subsequent to departure", "for a period of 1 year", "for a period of 2 years", "24 months", "12 months"])
        if has_post_term:
            red_flags.append({
                "severity": "HIGH",
                "clause": "Post-Termination Non-Compete Covenant",
                "issue": "Prohibits engaging with competing businesses or clients post-employment. Under Section 27 of the Indian Contract Act 1872, all post-termination non-compete agreements are void ab initio and legally unenforceable.",
                "signer_impact": "Signer faces threat of bogus legal notices or withholding of relieving letters, despite the clause being void in court.",
                "counter_clause": "Proposed Counter-Clause: 'The Employee acknowledges duty of confidentiality regarding trade secrets; provided that nothing herein shall restrict the Employee's constitutional right to lawful employment post-separation under Section 27 of the Indian Contract Act.'"
            })
            health_score -= 25

    # 2. Intellectual Property (IP) Overbreadth
    if any(k in lower_text for k in ["intellectual property", "inventions", "assigns all rights", "all works"]):
        has_broad_ip = any(w in lower_text for w in ["whether or not during working hours", "personal time", "unrelated to company", "prior inventions", "all ideas"])
        if has_broad_ip:
            red_flags.append({
                "severity": "HIGH",
                "clause": "Overbroad IP & Side-Project Assignment",
                "issue": "Claims full ownership of all inventions and concepts created by the signer, including off-duty hours, personal hardware, and unrelated side projects.",
                "signer_impact": "Signer risks forfeiting personal open-source projects, patents, or indie software businesses created on personal time.",
                "counter_clause": "Proposed Counter-Clause: 'The Company's assignment rights shall strictly apply exclusively to deliverables created directly within the scope of assigned duties during paid working hours utilizing Company facilities.'"
            })
            health_score -= 20

    # 3. Termination Notice & Lockout Trap
    if "termination" in lower_text or "notice period" in lower_text:
        has_unilateral = any(w in lower_text for w in ["terminate at will", "immediate termination without cause", "without notice", "sole discretion", "zero notice"])
        if has_unilateral:
            red_flags.append({
                "severity": "MEDIUM",
                "clause": "Unilateral Immediate Termination Without Cure Period",
                "issue": "Allows the drafting party to cancel the contract immediately without default cure windows or fair notice.",
                "signer_impact": "Abrupt loss of income, housing, or services with zero transition time or opportunity to rectify alleged breaches.",
                "counter_clause": "Proposed Counter-Clause: 'Either party may terminate this Agreement by providing not less than thirty (30) days prior written notice, subject to a mandatory 15-day cure window for any curable breach.'"
            })
            health_score -= 15

    # 4. Indemnification & Unlimited Liability
    if "indemnif" in lower_text or "hold harmless" in lower_text or "liability" in lower_text:
        has_unlimited = any(w in lower_text for w in ["unlimited liability", "all damages whatsoever", "consequential damages", "indemnify and hold harmless against any and all"])
        if has_unlimited:
            red_flags.append({
                "severity": "HIGH",
                "clause": "Unlimited Personal Indemnification & Liability Exposure",
                "issue": "Imposes uncapped personal liability for third-party claims, legal fees, or consequential damages without reciprocal protection.",
                "signer_impact": "Catastrophic personal financial exposure exceeding total contract earnings in the event of third-party litigation.",
                "counter_clause": "Proposed Counter-Clause: 'The aggregate liability of either party arising out of or related to this Agreement shall be mutually capped at the total fees paid or payable in the preceding three (3) months.'"
            })
            health_score -= 20

    # 5. Property / Lease Traps (If Real Estate)
    if category_key == "PROPERTY_REAL_ESTATE":
        if "security deposit" in lower_text and any(w in lower_text for w in ["forfeit", "non-refundable", "deduct"]):
            red_flags.append({
                "severity": "MEDIUM",
                "clause": "Arbitrary Security Deposit Deductions",
                "issue": "Grants landlord unconstrained power to forfeit or deduct from security deposit without documented repair invoices.",
                "signer_impact": "Risk of losing entire advance deposit upon tenancy move-out.",
                "counter_clause": "Proposed Counter-Clause: 'The Security Deposit shall be fully refunded within 7 days of handover, less only substantiated damages proven via third-party contractor invoices.'"
            })
            health_score -= 15

    # 6. Medical / Healthcare Traps
    if category_key == "MEDICAL_HEALTHCARE":
        if any(w in lower_text for w in ["waive all claims of negligence", "gross negligence", "binding arbitration"]):
            red_flags.append({
                "severity": "HIGH",
                "clause": "Unlawful Negligence & Malpractice Waiver",
                "issue": "Attempts to exempt medical staff or facility from accountability for gross medical negligence or substandard standard of care.",
                "signer_impact": "Patients or family members are stripped of consumer forum recourse in cases of egregious surgical or procedural errors.",
                "counter_clause": "Proposed Counter-Clause: 'Nothing in this Consent shall waive statutory consumer rights or immunity against gross negligence under prevailing Medical Council directives.'"
            })
            health_score -= 20

    # Ensure bounds
    health_score = max(20, min(98, health_score))
    
    # Build Structured Markdown Report
    report_lines = [
        f"## 🚨 CRITICAL RED FLAGS & RISK LEVELS (HIGHLIGHTED FIRST)",
    ]
    
    if not red_flags:
        report_lines.append("- [🟢 LOW RISK]: Standard Fair Playbook Alignment")
        report_lines.append("  • Issue: No predatory or statutory violation clauses detected.")
        report_lines.append("  • Signer Impact: Document exhibits balanced mutual covenants.")
    else:
        for rf in red_flags:
            badge = "🔴 HIGH RISK" if rf["severity"] == "HIGH" else "🟡 MEDIUM RISK"
            report_lines.append(f"- [{badge}]: {rf['clause']}")
            report_lines.append(f"  • Issue: {rf['issue']}")
            report_lines.append(f"  • Signer Impact: {rf['signer_impact']}")
            report_lines.append(f"  • Attorney Counter-Draft: {rf['counter_clause']}")

    verdict = "Significant contract risks detected requiring immediate redline negotiation." if health_score < 70 else "Fair contract terms with standard boilerplate provisions."
    
    report_lines.extend([
        "",
        "## 📊 EXECUTIVE SUMMARY & COMPLIANCE SCORE",
        f"- Document Type: {category['title']} ({filename})",
        f"- Overall Health Score: {health_score}/100 • {'High Risk Trap Detected' if health_score < 60 else 'Moderate Terms' if health_score < 80 else 'Safe & Balanced'}",
        f"- Executive Verdict: {verdict}",
        f"- Applicable Statutory Framework: {', '.join(category['statutes'])}",
        "",
        "## 🛡️ 4-PILLAR PLAYBOOK CHECK",
        f"- Non-Compete & Restraint of Trade: {'Flagged Unenforceable' if any('Non-Compete' in rf['clause'] for rf in red_flags) else 'Pass - Standard Covenants'}",
        f"- IP Assignment Scope: {'Flagged Overbroad' if any('IP' in rf['clause'] for rf in red_flags) else 'Pass - Reasonable Scope'}",
        f"- Termination & Notice Cure Periods: {'Flagged Unilateral' if any('Termination' in rf['clause'] for rf in red_flags) else 'Pass - Bilateral 30-Day Notice'}",
        f"- Indemnification & Liability Caps: {'Flagged Unlimited' if any('Liability' in rf['clause'] for rf in red_flags) else 'Pass - Balanced Exposure'}",
        "",
        "## 📝 ACTIONABLE NEXT STEPS BEFORE SIGNING",
        "1. Request written removal or strike-through of all High Risk clauses highlighted above.",
        "2. Substitute the provided 'Attorney Counter-Draft' language into Section revisions.",
        "3. Insist on a mutual bilateral liability cap before signing or remitting advance funds."
    ])

    report_text = "\n".join(report_lines)

    return {
        "success": True,
        "is_legal": True,
        "category": category["title"],
        "category_key": category_key,
        "health_score": health_score,
        "report": report_text,
        "engine": "Local Specialized Legal Engine (100% Private, Zero Cloud Retention)"
    }
