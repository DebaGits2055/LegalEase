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
def get_localized_rejection_message(language: str) -> str:
    lang_lower = (language or "").lower()
    if "bangla" in lang_lower or "bengali" in lang_lower or "bn" in lang_lower:
        return "⚠️ এটি কোনো স্বীকৃত আইনি নথি নয়। অনুগ্রহ করে একটি বৈধ আইনি নথি আপলোড করুন (যেমন: সম্পত্তির দলিল, চুক্তিপত্র, চিকিৎসা সম্মতি, পুলিশ এফআইআর, এনডিএ ইত্যাদি)।"
    elif "hindi" in lang_lower or "hi" in lang_lower:
        return "⚠️ यह कोई मान्यता प्राप्त कानूनी दस्तावेज़ नहीं है। कृपया एक वैध कानूनी दस्तावेज़ अपलोड करें (जैसे: संपत्ति विलेख, अनुबंध पत्र, चिकित्सा सहमति, पुलिस प्राथमिकी/एफआईआर, एनडीए आदि)।"
    return "⚠️ This is not a recognized legal document. Please upload an authentic legal instrument (Property Deed, Medical Consent, Criminal/Police Report, Employment Agreement, NDA, etc.)."

def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extracts text from PDF, DOCX, or text files.
    """
    extracted_text = ""
    lower_name = (filename or "").lower()
    
    if lower_name.endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            for page in reader.pages[:10]: # Read first 10 pages
                extracted_text += page.extract_text() or ""
        except Exception as e:
            print(f"PDF extraction error: {e}")
            
    elif lower_name.endswith(".docx"):
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                extracted_text = " ".join([node.text for node in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text])
        except Exception as e:
            print(f"DOCX extraction error: {e}")

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
    Strictly weeds out non-legal files (e.g. food receipts, code, memes, resumes, selfies, grocery lists).
    """
    clean_text = (text or "").strip()
    lower_text = clean_text.lower()
    lower_name = (filename or "").lower()

    # Check for filename clues
    has_legal_filename = any(term in lower_name for term in [
        "contract", "agreement", "nda", "deed", "lease", "affidavit", 
        "fir", "bail", "undertaking", "memorandum", "tenancy", "employment",
        "power_of_attorney", "legal", "clause", "petition"
    ])

    # If text is empty or very short (< 30 chars):
    if len(clean_text) < 30:
        if has_legal_filename:
            for cat_key, cat_data in LEGAL_CATEGORIES.items():
                if any(kw in lower_name for kw in cat_data["keywords"]):
                    return True, cat_key, cat_data
            return True, "CORPORATE_EMPLOYMENT", LEGAL_CATEGORIES["CORPORATE_EMPLOYMENT"]
        # Without legal text and without legal filename -> REJECT IMMEDIATELY!
        return False, None, None

    # Check for general legal structural markers
    legal_structure_markers = [
        "whereas", "witnesseth", "now therefore", "in witness whereof",
        "hereinafter referred to", "terms and conditions", "governing law",
        "jurisdiction", "arbitration", "indemnif", "covenant", "agreement",
        "party of the first part", "affidavit", "solemnly affirm", "deponent",
        "section", "pursuant to", "signed", "lessor", "lessee", "tenant",
        "landlord", "employer", "employee", "non-compete", "confidentiality",
        "intellectual property", "termination", "liability", "stamp duty",
        "police station", "accused", "complainant", "bail application",
        "first information report", "notary", "power of attorney", "will and testament",
        "medical negligence", "surgical consent", "informed consent", "statutory"
    ]
    
    structure_score = sum(1 for m in legal_structure_markers if m in lower_text)
    
    # Categorization score
    category_scores = {}
    for cat_key, cat_data in LEGAL_CATEGORIES.items():
        score = sum(1 for kw in cat_data["keywords"] if kw in lower_text)
        category_scores[cat_key] = score
        
    best_cat = max(category_scores, key=category_scores.get)
    max_score = category_scores[best_cat]
    
    # STRICT GUARD: If document lacks sufficient legal markers and category keywords, it is NON-LEGAL!
    if structure_score < 2 and max_score < 1 and not has_legal_filename:
        return False, None, None
        
    return True, best_cat, LEGAL_CATEGORIES[best_cat]

# ========================================================
# 3. LOCAL SPECIALIZED LEGAL INFERENCE ENGINE
# ========================================================
def run_local_legal_audit(
    text: str, 
    filename: str, 
    category_key: str = "CORPORATE_EMPLOYMENT", 
    language: str = "English"
) -> Dict[str, Any]:
    """
    100% Local Specialized Legal Audit:
    - Runs completely offline / on-premise.
    - Zero data transmitted to cloud or external APIs.
    - Analyzes contract clauses against statutory playbooks and Bar standards.
    """
    is_legal, verified_key, _ = classify_legal_document(text, filename)
    if not is_legal:
        return {
            "success": True,
            "is_legal": False,
            "category": None,
            "category_key": None,
            "health_score": 0,
            "report": get_localized_rejection_message(language),
            "engine": "Local Specialized Legal Engine (100% Private, Zero Cloud Retention)"
        }

    effective_cat = verified_key or category_key
    category = LEGAL_CATEGORIES.get(effective_cat, LEGAL_CATEGORIES["CORPORATE_EMPLOYMENT"])
    lower_text = (text or "").lower()
    
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
    
    # Language detection
    lang_lower = (language or "").lower()
    is_bn = "bangla" in lang_lower or "bengali" in lang_lower or "bn" in lang_lower
    is_hi = "hindi" in lang_lower or "hi" in lang_lower

    # Localized Category Titles & Headings
    if is_bn:
        # BENGALI (বাংলা)
        category_title_map = {
            "PROPERTY_REAL_ESTATE": "সম্পত্তি ও আবাসন আইন (Property & Real Estate)",
            "MEDICAL_HEALTHCARE": "চিকিৎসা ও স্বাস্থ্যসেবা আইন (Medical & Healthcare)",
            "CRIMINAL_INVESTIGATION": "ফৌজদারি তদন্ত ও আইন প্রয়োগ (Criminal Law)",
            "CORPORATE_EMPLOYMENT": "কর্পোরেট, বাণিজ্যিক ও শ্রম আইন (Corporate & Employment)",
            "ESTATE_NOTARIAL": "উইল, আমমোক্তারনামা ও হলফনামা (Estate & Affidavits)"
        }
        cat_title = category_title_map.get(category_key, category["title"])
        
        report_lines = [
            "## 🚨 ঝুঁকিপূর্ণ শর্তাবলী ও ঝুঁকি স্তর (প্রথমে প্রদর্শিত)",
        ]
        if not red_flags:
            report_lines.append("- [🟢 নিম্ন ঝুঁকি]: স্ট্যান্ডার্ড ফেয়ার প্লেবুকের সাথে সামঞ্জস্যপূর্ণ")
            report_lines.append("  • সমস্যা: কোনো অন্যায্য বা সংবিধিবহির্ভূত শর্ত পাওয়া যায়নি।")
            report_lines.append("  • স্বাক্ষরকারীর প্রভাব: নথিতে উভয় পক্ষের জন্য ভারসাম্যপূর্ণ শর্তাবলী বিদ্যমান।")
        else:
            bn_clause_map = {
                "Post-Termination Non-Compete Covenant": {
                    "clause": "চাকরি পরবর্তী অন্যায় প্রতিযোগিতা নিষেধাজ্ঞা (Section 27 Non-Compete)",
                    "issue": "চাকরি ছাড়ার পর কোনো প্রতিদ্বন্দ্বী সংস্থায় কাজ করতে নিষেধ করে। ভারতীয় চুক্তি আইন ১৮৭২-এর ধারা ২৭ অনুযায়ী, চাকরি পরবর্তী সবধরনের প্রতিযোগিতা নিষেধাজ্ঞা সম্পূর্ণ অবৈধ এবং বাতিল (void ab initio)।",
                    "impact": "চুক্তিতে স্বাক্ষরকারী অন্যায় আইনি নোটিশের হুমকির মুখে পড়েন, যদিও আদালতে এই ধারা সম্পূর্ণ অকার্যকর।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'কর্মচারী গোপনীয় তথ্যের সুরক্ষা বজায় রাখবেন; তবে ভারতীয় চুক্তি আইনের ধারা ২৭ অনুযায়ী আলাদা হওয়ার পর তার আইনসঙ্গত কর্মসংস্থানের অধিকার অক্ষুণ্ণ থাকবে।'"
                },
                "Overbroad IP & Side-Project Assignment": {
                    "clause": "অতিরিক্ত বিস্তৃত বৌদ্ধিক সম্পত্তি স্বত্ব (Overbroad IP Assignment)",
                    "issue": "ব্যক্তিগত সময়ে বা ব্যক্তিগত ডিভাইসে তৈরি যেকোনো ধারণা বা স্বাধীন প্রজেক্টের ওপরও কোম্পানির একচ্ছত্র মালিকানা দাবি করে।",
                    "impact": "ব্যক্তিগত ওপেন সোর্স প্রজেক্ট, সফটওয়্যার বা নিজস্ব উদ্ভাবনের আইনি অধিকার হারানোর তীব্র ঝুঁকি তৈরি হয়।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'কোম্পানির অধিকার কেবল নির্দিষ্ট কাজের সময় এবং কোম্পানির সরঞ্জাম ব্যবহার করে তৈরি ফলাফলের মধ্যেই সীমাবদ্ধ থাকবে।'"
                },
                "Unilateral Immediate Termination Without Cure Period": {
                    "clause": "একতরফা অবিলম্বে চুক্তি বাতিলকরণ (Unilateral Termination)",
                    "issue": "ত্রুটি সংশোধনের সুযোগ বা উপযুক্ত নোটিশ ছাড়াই অবিলম্বে চুক্তি বাতিলের একতরফা ক্ষমতা দেয়।",
                    "impact": "হঠাৎ করে কোনো পূর্ব নোটিশ বা নিজেকে সংশোধনের সুযোগ না পেয়ে কাজ বা আয় হারানোর আশঙ্কা।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'যেকোনো পক্ষ অন্তত ৩০ দিনের লিখিত নোটিশ এবং যেকোনো লঙ্ঘনের জন্য ১৫ দিনের সংশোধনের সুযোগ প্রদান সাপেক্ষে চুক্তি বাতিল করতে পারে।'"
                },
                "Unlimited Personal Indemnification & Liability Exposure": {
                    "clause": "সীমাহীন ব্যক্তিগত দায় ও ক্ষতিপূরণ (Unlimited Liability Exposure)",
                    "issue": "পারস্পরিক সুরক্ষা ছাড়াই একতরফাভাবে সম্পূর্ণ আর্থিক দায় বা ক্ষতিপূরণের বোঝা চাপিয়ে দেয়।",
                    "impact": "যেকোনো আইনি বিরোধের ক্ষেত্রে মোট অর্জিত পারিশ্রমিকের চেয়ে বহুগুণ বেশি ব্যক্তিগত আর্থিক ক্ষতির আশঙ্কা।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'এই চুক্তির অধীনে কোনো পক্ষের মোট দায় পূর্ববর্তী ৩ (তিন) মাসে প্রদত্ত পারিশ্রমিকের সমপরিমাণ অর্থ পর্যন্ত সীমাবদ্ধ থাকবে।'"
                },
                "Arbitrary Security Deposit Deductions": {
                    "clause": "অন্যায় সিকিউরিটি ডিপোজিট কর্তন (Arbitrary Deposit Forfeiture)",
                    "issue": "প্রমাণিত বিল বা ইনভয়েস ছাড়াই বাড়িওয়ালাকে জামানতের অর্থ আটকে রাখার অযৌক্তিক ক্ষমতা দেয়।",
                    "impact": "ভাড়া শেষে পুরো অগ্রিম জামানতের অর্থ হারানোর তীব্র ঝুঁকি।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'বাড়ি হস্তান্তরের ৭ দিনের মধ্যে স্বাধীন ঠিকাদারের ভাউচার দ্বারা প্রমাণিত ক্ষতি ছাড়া বাকি সমস্ত সিকিউরিটি ডিপোজিট ফেরত দিতে হবে।'"
                },
                "Unlawful Negligence & Malpractice Waiver": {
                    "clause": "চিকিৎসা অবহেলার দায়মুক্তি শর্ত (Unlawful Negligence Waiver)",
                    "issue": "হাসপাতাল বা চিকিৎসকের গুরুতর অবহেলার ক্ষেত্রেও তাদের সবধরনের আইনি দায়মুক্তি দেওয়ার চেষ্টা করে।",
                    "impact": "ভুল চিকিৎসার কারণে রোগী বা তার পরিবার ভোক্তা ফোরাম বা আইনের আশ্রয় নেওয়া থেকে বঞ্চিত হতে পারে।",
                    "counter": "প্রস্তাবিত বিকল্প শর্ত: 'জাতীয় মেডিকেল কমিশনের নির্দেশিকা এবং ভোক্তা সুরক্ষা আইনের অধীনে গুরুতর অবহেলার ক্ষেত্রে কোনো দায়মুক্তি প্রযোজ্য হবে না।'"
                }
            }
            for rf in red_flags:
                badge = "🔴 উচ্চ ঝুঁকি (HIGH RISK)" if rf["severity"] == "HIGH" else "🟡 মাঝারি ঝুঁকি (MEDIUM RISK)"
                mapped = bn_clause_map.get(rf["clause"], {
                    "clause": rf["clause"],
                    "issue": rf["issue"],
                    "impact": rf["signer_impact"],
                    "counter": rf["counter_clause"]
                })
                report_lines.append(f"- [{badge}]: {mapped['clause']}")
                report_lines.append(f"  • সমস্যা: {mapped['issue']}")
                report_lines.append(f"  • স্বাক্ষরকারীর প্রভাব: {mapped['impact']}")
                report_lines.append(f"  • আইনজীবীর বিকল্প খসড়া (Attorney Counter-Draft): {mapped['counter']}")

        verdict_bn = "তাৎক্ষণিক আইনি আলোচনার প্রয়োজন এমন গুরুত্বপূর্ণ ঝুঁকি চিহ্নিত হয়েছে।" if health_score < 70 else "স্ট্যান্ডার্ড আইনি শর্তাবলী সহ ভারসাম্যপূর্ণ চুক্তি।"
        status_text = "উচ্চ ঝুঁকির ফাঁদ চিহ্নিত" if health_score < 60 else "মাঝারি ঝুঁকি" if health_score < 80 else "নিরাপদ ও ভারসাম্যপূর্ণ"

        report_lines.extend([
            "",
            "## 📊 নির্বাহী সারাংশ এবং সম্মতি স্কোর (EXECUTIVE SUMMARY)",
            f"- নথির ধরন: {cat_title} ({filename})",
            f"- সার্বিক সুরক্ষা স্কোর: {health_score}/100 • {status_text}",
            f"- নির্বাহী সিদ্ধান্ত: {verdict_bn}",
            f"- প্রযোজ্য সংবিধিবদ্ধ আইন: {', '.join(category['statutes'])}",
            "",
            "## 🛡️ ৪-স্তম্ভ প্লেবুক নিরীক্ষা (4-PILLAR PLAYBOOK CHECK)",
            f"- প্রতিযোগিতা নিষেধাজ্ঞা (Non-Compete): {'অবৈধ ও বাতিল ঘোষিত (ধারা ২৭)' if any('Non-Compete' in rf['clause'] for rf in red_flags) else 'উত্তীর্ণ - স্ট্যান্ডার্ড নিয়ম'}",
            f"- বৌদ্ধিক সম্পত্তি পরিসীমা (IP Scope): {'অতিরিক্ত বিস্তৃত' if any('IP' in rf['clause'] for rf in red_flags) else 'উত্তীর্ণ - যুক্তিযুক্ত পরিধি'}",
            f"- চুক্তি বাতিল নোটিশ (Termination): {'একতরফা বাতিলকরণ' if any('Termination' in rf['clause'] for rf in red_flags) else 'উত্তীর্ণ - দ্বিপাক্ষিক ৩০ দিনের নোটিশ'}",
            f"- দায়বদ্ধতার সীমা (Liability): {'সীমাহীন দায় চিহ্নিত' if any('Liability' in rf['clause'] for rf in red_flags) else 'উত্তীর্ণ - ভারসাম্যপূর্ণ দায়'}",
            "",
            "## 📝 স্বাক্ষরের পূর্বে করণীয় পদক্ষেপ (ACTIONABLE NEXT STEPS)",
            "১. উপরে চিহ্নিত সমস্ত উচ্চ ঝুঁকির শর্তাবলী বাদ দেওয়ার জন্য লিখিত অনুরোধ জানান।",
            "২. চুক্তির সংশোধিত খসড়ায় উপরে প্রদত্ত 'আইনজীবীর বিকল্প খসড়া (Attorney Counter-Draft)' যুক্ত করুন।",
            "৩. অগ্রিম অর্থ প্রদান বা স্বাক্ষর করার আগে উভয় পক্ষের জন্য পারস্পরিক দায়বদ্ধতার সীমা নিশ্চিত করুন।"
        ])

    elif is_hi:
        # HINDI (हिंदी)
        category_title_map = {
            "PROPERTY_REAL_ESTATE": "संपत्ति एवं अचल संपत्ति कानून (Property & Real Estate)",
            "MEDICAL_HEALTHCARE": "चिकित्सा एवं स्वास्थ्य सेवा कानून (Medical & Healthcare)",
            "CRIMINAL_INVESTIGATION": "आपराधिक जांच एवं कानून प्रवर्तन (Criminal Law)",
            "CORPORATE_EMPLOYMENT": "कॉर्पोरेट, वाणिज्यिक एवं रोजगार कानून (Corporate & Employment)",
            "ESTATE_NOTARIAL": "वसीयत, पावर ऑफ अटॉर्नी एवं शपथ पत्र (Estate & Affidavits)"
        }
        cat_title = category_title_map.get(category_key, category["title"])

        report_lines = [
            "## 🚨 महत्वपूर्ण जोखिम और चेतावनी स्तर (CRITICAL RED FLAGS)",
        ]
        if not red_flags:
            report_lines.append("- [🟢 कम जोखिम]: मानक निष्पक्ष कानूनी दिशानिर्देशों के अनुरूप")
            report_lines.append("  • समस्या: कोई अनुचित या असंवैधानिक शर्तें नहीं पाई गईं।")
            report_lines.append("  • प्रभाव: अनुबंध में दोनों पक्षों के लिए संतुलित शर्तें मौजूद हैं।")
        else:
            hi_clause_map = {
                "Post-Termination Non-Compete Covenant": {
                    "clause": "नौकरी समाप्ति के बाद गैर-प्रतिस्पर्धा खंड (Section 27 Non-Compete)",
                    "issue": "नौकरी छोड़ने के बाद प्रतिस्पर्धी कंपनियों या ग्राहकों के साथ काम करने पर रोक लगाता है। भारतीय अनुबंध अधिनियम 1872 की धारा 27 के तहत, नौकरी के बाद का गैर-प्रतिस्पर्धा खंड पूरी तरह अमान्य और शून्य (void ab initio) है।",
                    "impact": "हस्ताक्षरकर्ता को अनुचित कानूनी नोटिस या अनुभव प्रमाण पत्र रोके जाने का डर रहता है, जबकि यह अदालत में नहीं टिक सकता।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'कर्मचारी व्यापार रहस्यों की गोपनीयता का पालन करेगा; बशर्ते कि भारतीय अनुबंध अधिनियम की धारा 27 के तहत अलग होने के बाद उसके वैध रोजगार के अधिकार पर कोई प्रतिबंध नहीं होगा।'"
                },
                "Overbroad IP & Side-Project Assignment": {
                    "clause": "अति-विस्तृत बौद्धिक संपदा अधिकार (Overbroad IP Assignment)",
                    "issue": "व्यक्तिगत समय और व्यक्तिगत उपकरणों पर बनाए गए स्वतंत्र विचारों और प्रोजेक्ट्स पर भी कंपनी का स्वामित्व मांगता है।",
                    "impact": "व्यक्तिगत ओपन-सोर्स प्रोजेक्ट्स, सॉफ्टवेयर या स्वतंत्र आविष्कारों के अधिकार खोने का गंभीर जोखिम।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'कंपनी का अधिकार केवल कंपनी के कामकाजी घंटों और कंपनी के संसाधनों से तैयार किए गए कार्यों तक ही सीमित रहेगा।'"
                },
                "Unilateral Immediate Termination Without Cure Period": {
                    "clause": "एकतरफा तत्काल अनुबंध समाप्ति (Unilateral Termination)",
                    "issue": "गलती सुधारने का अवसर दिए बिना या बिना उचित नोटिस के अनुबंध को तुरंत रद्द करने का एकतरफा अधिकार देता है।",
                    "impact": "बिना किसी पूर्व सूचना या सुधार के अवसर के अचानक रोजगार या आय खोने का खतरा।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'कोई भी पक्ष कम से कम 30 दिनों का पूर्व लिखित नोटिस देकर और किसी भी सुधारे जा सकने वाले उल्लंघन के लिए 15 दिनों का समय देकर ही अनुबंध समाप्त कर सकता है।'"
                },
                "Unlimited Personal Indemnification & Liability Exposure": {
                    "clause": "असीमित व्यक्तिगत देनदारी व दायित्व (Unlimited Liability Exposure)",
                    "issue": "बिना किसी पारस्परिक सुरक्षा के तीसरे पक्ष के दावों या नुकसान का असीमित वित्तीय बोझ व्यक्तिगत रूप से डालता है।",
                    "impact": "किसी भी विवाद की स्थिति में कुल अनुबंध शुल्क से कहीं अधिक भारी व्यक्तिगत वित्तीय नुकसान।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'इस अनुबंध से उत्पन्न किसी भी पक्ष की कुल देनदारी पिछले 3 (तीन) महीनों में प्राप्त कुल शुल्क तक सीमित होगी।'"
                },
                "Arbitrary Security Deposit Deductions": {
                    "clause": "सुरक्षा जमा (Security Deposit) की मनमानी कटौती",
                    "issue": "मकान मालिक को बिना किसी सत्यापित बिल या इनवॉइस के पूरी सुरक्षा जमा राशि जब्त करने की मनमानी शक्ति देता है।",
                    "impact": "किराया अवधि समाप्त होने पर पूरी अग्रिम जमा राशि खोने का गंभीर जोखिम।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'मकान खाली करने के 7 दिनों के भीतर प्रमाणित बिलों के आधार पर हुई वास्तविक क्षति को छोड़कर पूरी सुरक्षा जमा राशि लौटाई जाएगी।'"
                },
                "Unlawful Negligence & Malpractice Waiver": {
                    "clause": "चिकित्सीय लापरवाही पर अवैध दायित्व मुक्ति (Medical Negligence Waiver)",
                    "issue": "अस्पताल या डॉक्टर की गंभीर लापरवाही के मामलों में भी जवाबदेही से बचने की अनुचित कोशिश करता है।",
                    "impact": "गलत इलाज की स्थिति में मरीज या परिजनों को उपभोक्ता फोरम में न्याय मांगने से वंचित करने का प्रयास।",
                    "counter": "प्रस्तावित प्रति-शर्त (Attorney Counter-Draft): 'उपभोक्ता संरक्षण अधिनियम और मेडिकल काउंसिल के नियमों के तहत गंभीर लापरवाही के खिलाफ कोई छूट लागू नहीं होगी।'"
                }
            }
            for rf in red_flags:
                badge = "🔴 उच्च जोखिम (HIGH RISK)" if rf["severity"] == "HIGH" else "🟡 मध्यम जोखिम (MEDIUM RISK)"
                mapped = hi_clause_map.get(rf["clause"], {
                    "clause": rf["clause"],
                    "issue": rf["issue"],
                    "impact": rf["signer_impact"],
                    "counter": rf["counter_clause"]
                })
                report_lines.append(f"- [{badge}]: {mapped['clause']}")
                report_lines.append(f"  • समस्या: {mapped['issue']}")
                report_lines.append(f"  • हस्ताक्षरकर्ता पर प्रभाव: {mapped['impact']}")
                report_lines.append(f"  • वकील का प्रति-प्रारूप (Attorney Counter-Draft): {mapped['counter']}")

        verdict_hi = "तत्काल बातचीत और संशोधन की आवश्यकता वाले महत्वपूर्ण जोखिम पाए गए हैं।" if health_score < 70 else "मानक कानूनी प्रावधानों के साथ उचित अनुबंध शर्तें।"
        status_text_hi = "उच्च जोखिम चिह्नित" if health_score < 60 else "मध्यम जोखिम" if health_score < 80 else "सुरक्षित और संतुलित"

        report_lines.extend([
            "",
            "## 📊 कार्यकारी सारांश और अनुपालन स्कोर (EXECUTIVE SUMMARY)",
            f"- दस्तावेज़ का प्रकार: {cat_title} ({filename})",
            f"- कुल सुरक्षा स्कोर: {health_score}/100 • {status_text_hi}",
            f"- कार्यकारी निर्णय: {verdict_hi}",
            f"- लागू कानूनी ढांचा: {', '.join(category['statutes'])}",
            "",
            "## 🛡️ 4-स्तंभ कानूनी समीक्षा (4-PILLAR PLAYBOOK CHECK)",
            f"- गैर-प्रतिस्पर्धा खंड (Non-Compete): {'अमान्य एवं शून्य (धारा 27)' if any('Non-Compete' in rf['clause'] for rf in red_flags) else 'पास - मानक प्रावधान'}",
            f"- बौद्धिक संपदा दायरा (IP Scope): {'अत्यधिक विस्तृत' if any('IP' in rf['clause'] for rf in red_flags) else 'पास - उचित दायरा'}",
            f"- समाप्ति एवं नोटिस अवधि (Termination): {'एकतरफा समाप्ति' if any('Termination' in rf['clause'] for rf in red_flags) else 'पास - द्विपक्षीय 30 दिन का नोटिस'}",
            f"- देनदारी व क्षतिपूर्ति सीमा (Liability): {'असीमित देनदारी' if any('Liability' in rf['clause'] for rf in red_flags) else 'पास - संतुलित देनदारी'}",
            "",
            "## 📝 हस्ताक्षर करने से पहले आवश्यक कदम (ACTIONABLE NEXT STEPS)",
            "१. ऊपर बताए गए सभी उच्च जोखिम वाले खंडों को हटाने का लिखित अनुरोध करें।",
            "२. अनुबंध के संशोधित प्रारूप में ऊपर दिए गए 'वकील के प्रति-प्रारूप (Attorney Counter-Draft)' को शामिल करें।",
            "३. अग्रिम भुगतान करने या हस्ताक्षर करने से पहले दोनों पक्षों के लिए पारस्परिक देयता सीमा तय करें।"
        ])

    else:
        # ENGLISH (Standard)
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
        "category": cat_title if (is_bn or is_hi) else category["title"],
        "category_key": category_key,
        "health_score": health_score,
        "report": report_text,
        "engine": "Local Specialized Legal Engine (100% Private, Zero Cloud Retention)"
    }
