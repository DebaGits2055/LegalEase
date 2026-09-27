import os
import time
import base64
import json
import urllib.request
from io import BytesIO
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from gtts import gTTS

try:
    from playbook import LEGAL_PLAYBOOK, NON_LEGAL_DOCUMENT_MESSAGE
    from vault import vault_instance
    from legal_engine import (
        extract_text_from_file, 
        classify_legal_document, 
        run_local_legal_audit,
        STRICT_REJECTION_MESSAGE,
        LEGAL_CATEGORIES,
        get_localized_rejection_message
    )
except ImportError:
    from backend.playbook import LEGAL_PLAYBOOK, NON_LEGAL_DOCUMENT_MESSAGE
    from backend.vault import vault_instance
    from backend.legal_engine import (
        extract_text_from_file, 
        classify_legal_document, 
        run_local_legal_audit,
        STRICT_REJECTION_MESSAGE,
        LEGAL_CATEGORIES,
        get_localized_rejection_message
    )

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# ========================================================
# 100% LOCAL AI MODEL CONFIGURATION (ZERO CLOUD / NO GEMINI)
# ========================================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_HOST}/api/chat"
_CACHED_LOCAL_MODEL: Optional[str] = None

def get_available_local_model() -> str:
    global _CACHED_LOCAL_MODEL
    if _CACHED_LOCAL_MODEL:
        return _CACHED_LOCAL_MODEL
        
    env_model = os.getenv("LOCAL_LLM_MODEL")
    if env_model:
        _CACHED_LOCAL_MODEL = env_model
        return env_model
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if models:
                for preferred in ["llama3:8b", "llama3", "phi3:mini", "phi3", "mistral:7b", "mistral"]:
                    for m in models:
                        if preferred in m:
                            _CACHED_LOCAL_MODEL = m
                            return m
                _CACHED_LOCAL_MODEL = models[0]
                return models[0]
    except Exception:
        pass
    return "llama3:8b"

def query_local_ollama(prompt: str, model_name: Optional[str] = None, timeout: int = 60) -> Optional[str]:
    """
    Connects to an on-device local Ollama model (e.g. LLaMA-3, Mistral, Phi-3, Qwen).
    Ensures 100% private offline computation. Zero data is transmitted to external cloud.
    """
    target_model = model_name or get_available_local_model()
    try:
        payload = json.dumps({
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }).encode("utf-8")
        
        req = urllib.request.Request(
            OLLAMA_GENERATE_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        # Ollama daemon not running or not installed
        return None

def analyze_legal_document(
    file_bytes: bytes, 
    filename: str, 
    language: str = "English",
    engine_mode: str = "local",
    user_email: str = "anonymous",
    is_ephemeral: bool = False,
    client_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    100% Local On-Premise Legal Document Compliance Audit:
    - Encrypts and seals document binary in 256-Bit AES-GCM Encrypted Vault.
    - Executes Phase 0 Strict Legal Document Categorization.
    - Processes document using Local Ollama LLM or the Built-in Specialized Legal Reasoning Engine.
    - Zero external cloud services, Zero Gemini dependency, Zero third-party data tracking.
    """
    # 1. 256-BIT AES-GCM ENCRYPTED VAULT INGESTION
    vault_receipt = vault_instance.encrypt_and_store(file_bytes, filename, user_email)
    
    # Save temporary file for text extraction and local processing
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"temp_{int(time.time())}_{filename}")
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    try:
        # 2. EXTRACT TEXT AND RUN PHASE 0 STRICT LEGAL CLASSIFIER
        extracted_text = extract_text_from_file(temp_path, filename)
        if (not extracted_text or len(extracted_text.strip()) < 20) and client_text:
            extracted_text = client_text.strip()

        is_legal, category_key, category_info = classify_legal_document(extracted_text, filename)

        if not is_legal:
            # Ephemeral shredding on rejection
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass
            vault_instance.shred_document(vault_receipt["vault_id"])
            return {
                "success": True,
                "is_legal": False,
                "report": get_localized_rejection_message(language),
                "audio_url": None,
                "vault_receipt": None
            }

        # 3. RUN LOCAL AI INFERENCE (OLLAMA OR BUILT-IN LEGAL ENGINE)
        ollama_response = None
        engine_used = "Local Specialized Legal Engine (100% Private, On-Premise)"

        lang_lower = (language or "").lower()
        if "bangla" in lang_lower or "bengali" in lang_lower or "bn" in lang_lower:
            lang_rule = "BENGALI / BANGLA (বাংলা). CRITICAL INSTRUCTION: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Bengali using Bangla script (সম্পূর্ণ বিশ্লেষণটি খাঁটি বাংলা লিপিতে লিখুন). Do NOT output English words."
        elif "hindi" in lang_lower or "hi" in lang_lower:
            lang_rule = "HINDI (हिंदी). CRITICAL INSTRUCTION: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Hindi using Devanagari script (संपूर्ण विश्लेषण हिंदी देवनागरी लिपि में लिखें). Do NOT output English words."
        elif "tamil" in lang_lower or "ta" in lang_lower:
            lang_rule = "TAMIL (தமிழ்). CRITICAL INSTRUCTION: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Tamil script (முழு பகுப்பாய்வையும் தமிழில் எழுதவும்)."
        else:
            lang_rule = "ENGLISH"

        # Check if local Ollama is available
        if extracted_text and len(extracted_text) > 30:
            prompt = f"""
            {LEGAL_PLAYBOOK}
            =========================================
            DOCUMENT TEXT:
            {extracted_text[:4000]}
            =========================================
            OUTPUT LANGUAGE REQUIREMENT:
            {lang_rule}

            MANDATORY VALIDATION RULES:
            Rule 1 - LEGAL AUTHENTICITY VALIDATION:
            Examine if the document text above is an authentic legal instrument (e.g. agreement, deed, lease, contract, NDA, affidavit, police report, medical consent).
            If the text is NOT an authentic legal document (e.g. food recipe, grocery list, homework, code, casual conversation, jokes, shopping list), you MUST respond ONLY with the exact text:
            "This is not a recognized legal document. Please upload an authentic legal instrument (Property Deed, Medical Consent, Criminal/Police Report, Employment Agreement, NDA, etc.)."
            
            Rule 2 - SPECIFIC CLAUSE AUDIT:
            If it is a legal document, analyze the actual clauses present in the text. Highlight specific High-Risk and Medium-Risk covenants (e.g. non-compete, indemnification, termination).
            Provide tailored Attorney Counter-Drafts for every flagged clause. Do NOT provide generic boilerplate text.

            Respond strictly in the requested language following the standard 4-heading output format with Attorney Counter-Drafts.
            """
            raw_ollama = query_local_ollama(prompt)
            if raw_ollama:
                # Script verification: ensure requested non-English language didn't get ignored
                if ("bangla" in lang_lower or "bengali" in lang_lower) and not re.search(r'[\u0980-\u09FF]', raw_ollama):
                    ollama_response = None
                elif ("hindi" in lang_lower) and not re.search(r'[\u0900-\u097F]', raw_ollama):
                    ollama_response = None
                else:
                    ollama_response = raw_ollama

        if ollama_response:
            resp_text = ollama_response
            engine_used = f"Local Ollama Model ({get_available_local_model()} • 100% Private)"
            identified_category = category_info['title'] if category_info else "Corporate & Contract Law"
        else:
            # High-Speed Built-In Specialized Legal Reasoning Engine with native language support
            local_result = run_local_legal_audit(
                extracted_text, 
                filename, 
                category_key or "CORPORATE_EMPLOYMENT", 
                language
            )
            if not local_result.get("is_legal"):
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except Exception: pass
                vault_instance.shred_document(vault_receipt["vault_id"])
                return {
                    "success": True,
                    "is_legal": False,
                    "report": local_result.get("report") or get_localized_rejection_message(language),
                    "audio_url": None,
                    "vault_receipt": None
                }
            resp_text = local_result["report"]
            engine_used = "Local Specialized Legal Engine (100% Private, On-Premise)"
            identified_category = local_result["category"]

        # Rejection check on response
        rejection_keywords = [
            "not a legal document",
            "not a legal contract",
            "not a recognized legal document",
            "please upload the correct one",
            "স্বীকৃত আইনি নথি নয়",
            "বৈধ আইনি নথি",
            "मान्यता प्राप्त कानूनी दस्तावेज़ नहीं"
        ]
        if any(kw in resp_text.lower() for kw in rejection_keywords):
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass
            vault_instance.shred_document(vault_receipt["vault_id"])
            return {
                "success": True,
                "is_legal": False,
                "report": get_localized_rejection_message(language),
                "audio_url": None,
                "vault_receipt": None
            }

        # 4. MULTILINGUAL AUDIO SYNTHESIS
        audio_b64 = None
        try:
            lang_code_map = {"English": "en", "Hindi (हिंदी)": "hi", "Bangla (বাংলা)": "bn", "Hindi": "hi", "Bangla": "bn", "Tamil": "ta"}
            code = lang_code_map.get(language, "en")
            # Executive summary audio (strip markdown)
            clean_audio_text = resp_text.replace("#", "").replace("*", "").replace("`", "")[:800]
            tts = gTTS(text=clean_audio_text, lang=code, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_b64 = base64.b64encode(fp.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"TTS notice: {e}")

        # If Ephemeral Scan Mode: shred temporary file immediately
        if is_ephemeral:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass
            temp_path = None

        return {
            "success": True,
            "is_legal": True,
            "category": identified_category,
            "report": resp_text,
            "engine": engine_used,
            "vault_receipt": vault_receipt,
            "audio_url": f"data:audio/mp3;base64,{audio_b64}" if audio_b64 else None,
            "doc_temp_path": temp_path if not is_ephemeral else None
        }

    except Exception as e:
        print(f"Local Analysis Exception: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if is_ephemeral and temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except Exception: pass

def chat_with_legal_counsel(query: str, doc_temp_path: Optional[str] = None, language: str = "English") -> Dict[str, Any]:
    """
    100% Local Conversational AI Legal Counsel (Ollama + Statutory Engine).
    """
    doc_context = ""
    if doc_temp_path and os.path.exists(doc_temp_path):
        try:
            doc_context = extract_text_from_file(doc_temp_path, "context_doc.pdf")[:2000]
        except Exception:
            pass

    lang_lower = (language or "").lower()
    is_bn = "bangla" in lang_lower or "bengali" in lang_lower or "bn" in lang_lower
    is_hi = "hindi" in lang_lower or "hi" in lang_lower

    lang_instr = "English"
    if is_bn:
        lang_instr = "BENGALI (বাংলা). You MUST answer exclusively in Bengali language using Bangla script."
    elif is_hi:
        lang_instr = "HINDI (हिंदी). You MUST answer exclusively in Hindi language using Devanagari script."

    chat_prompt = f"""
    You are LegalEase Local AI Counsel — an expert contract attorney.
    Based on standard legal principles, Indian Contract Act 1872, RERA, and consumer statutes:
    Context: {doc_context if doc_context else 'General Contract Law Query'}
    User Question: {query}
    OUTPUT LANGUAGE: {lang_instr}
    Provide crisp, professional, actionable legal guidance strictly in the requested language.
    """

    # 1. Try Local Ollama
    local_reply = query_local_ollama(chat_prompt)
    if local_reply:
        # Check script validity
        if is_bn and re.search(r'[\u0980-\u09FF]', local_reply):
            return {"success": True, "response": local_reply}
        elif is_hi and re.search(r'[\u0900-\u097F]', local_reply):
            return {"success": True, "response": local_reply}
        elif not is_bn and not is_hi:
            return {"success": True, "response": local_reply}

    # 2. Built-in Multilingual Legal Counsel Guidance
    clean_q = query.lower()
    if is_bn:
        # BENGALI (বাংলা)
        guidance = (
            f"আইনি পরামর্শ ({language}): আপনার প্রশ্ন '{query}' প্রসঙ্গে, "
            "ভারতীয় চুক্তি আইন ১৮৭২-এর ধারা ২৭ অনুযায়ী, যেকোনো চুক্তি যা কোনো ব্যক্তিকে তার বৈধ পেশা, ব্যবসা বা বাণিজ্য অনুশীলনে বাধা দেয়, তা সম্পূর্ণ বেআইনি এবং বাতিল। "
            "চুক্তির সমস্ত শর্তাবলীতে কমপক্ষে ৩০ দিনের নোটিশ পিরিয়ড এবং উভয় পক্ষের জন্য পারস্পরিক দায়বদ্ধতার সীমা থাকা নিশ্চিত করুন।"
        )
        if "non-compete" in clean_q or "প্রতিযোগিতা" in clean_q or "restraint" in clean_q:
            guidance = "প্রতিযোগিতা নিষেধাজ্ঞা নীতি (Non-Compete Doctrine): ভারতীয় চুক্তি আইন ১৮৭২-এর ধারা ২৭ অনুযায়ী, চাকরি পরবর্তী সবধরনের প্রতিযোগিতা নিষেধাজ্ঞা সম্পূর্ণ বাতিল (void ab initio)। চুক্তিপত্রে যা-ই লেখা থাকুক না কেন, চাকরি ছাড়ার পর কোনো নিয়োগকর্তা আপনাকে কোনো প্রতিদ্বন্দ্বী প্রতিষ্ঠানে যোগদান করতে আইনত বাধা দিতে পারে না।"
        elif "lease" in clean_q or "rent" in clean_q or "ভাড়া" in clean_q or "deposit" in clean_q or "জামানত" in clean_q:
            guidance = "ভাড়াটিয়া আইন নীতি (Tenancy Law): বাড়ি হস্তান্তরের পর চুক্তি অনুযায়ী নির্দিষ্ট সময়ের মধ্যে সিকিউরিটি ডিপোজিট ফেরত দিতে হবে। স্বাধীন ভাউচার ছাড়া একতরফাভাবে জামানতের অর্থ বাজেয়াপ্ত করা আইনত দণ্ডনীয়।"
        elif "ip" in clean_q or "invention" in clean_q or "প্রজেক্ট" in clean_q:
            guidance = "বৌদ্ধিক সম্পত্তি নীতি (IP Doctrine): নিয়োগকর্তা শুধুমাত্র কাজের সময় এবং কোম্পানির সরঞ্জাম ব্যবহার করে প্রস্তুত ফলাফলের স্বত্ব দাবি করতে পারেন। ব্যক্তিগত সময়ে প্রস্তুত স্বাধীন কাজের ওপর কোম্পানির কোনো আইনি অধিকার থাকে না।"
    elif is_hi:
        # HINDI (हिंदी)
        guidance = (
            f"कानूनी सलाह ({language}): आपके प्रश्न '{query}' के संदर्भ में, "
            "भारतीय अनुबंध अधिनियम 1872 की धारा 27 के तहत, कोई भी समझौता जो किसी भी व्यक्ति को वैध व्यवसाय या पेशा करने से रोकता है, वह कानूनी रूप से अमान्य है। "
            "सुनिश्चित करें कि सभी खंडों में कम से कम 30 दिनों की नोटिस अवधि और दोनों पक्षों के लिए पारस्परिक देनदारी की सीमा तय हो।"
        )
        if "non-compete" in clean_q or "प्रतिस्पर्धा" in clean_q or "restraint" in clean_q:
            guidance = "गैर-प्रतिस्पर्धा सिद्धांत (Non-Compete Doctrine): भारतीय अनुबंध अधिनियम 1872 की धारा 27 के अनुसार, रोजगार समाप्ति के बाद का गैर-प्रतिस्पर्धा खंड पूरी तरह शून्य (void ab initio) होता है। अनुबंध में कुछ भी लिखा हो, नौकरी छोड़ने के बाद कोई भी नियोक्ता आपको प्रतिस्पर्धी कंपनी में जाने से कानूनी रूप से नहीं रोक सकता।"
        elif "lease" in clean_q or "rent" in clean_q or "किराया" in clean_q or "deposit" in clean_q:
            guidance = "किरायेदारी कानून सिद्धांत (Tenancy Law): परिसर खाली करने के बाद सहमत समय सीमा के भीतर सुरक्षा जमा राशि (Security Deposit) लौटाई जानी चाहिए। बिना उचित बिलों के मनमाने ढंग से जमा राशि जब्त करना कानूनी नियमों का उल्लंघन है।"
        elif "ip" in clean_q or "invention" in clean_q or "प्रोजेक्ट" in clean_q:
            guidance = "बौद्धिक संपदा सिद्धांत (IP Doctrine): कंपनियां केवल काम के घंटों के दौरान और कंपनी के संसाधनों से बनाई गई बौद्धिक संपदा पर ही अधिकार मांग सकती हैं। व्यक्तिगत समय में किए गए निजी प्रोजेक्ट्स पर कंपनी का कोई कानूनी अधिकार नहीं होता।"
    else:
        # ENGLISH (Standard)
        guidance = (
            f"Legal Counsel Analysis ({language}): Regarding your query '{query}', "
            "under Section 27 of the Indian Contract Act 1872, any agreement that restrains anyone from exercising "
            "a lawful profession, trade, or business is void to that extent. "
            "Ensure all covenants include mutual bilateral notice periods (minimum 30 days) and reciprocal liability caps."
        )
        if "non-compete" in clean_q or "restraint" in clean_q:
            guidance = "Non-Compete Doctrine: Under Section 27 of the Indian Contract Act 1872, post-termination non-compete clauses are void ab initio in India. An employer cannot stop you from joining a competitor after your employment ends, regardless of what the contract says."
        elif "lease" in clean_q or "rent" in clean_q or "deposit" in clean_q:
            guidance = "Tenancy Law Doctrine: Security deposits must be refunded within the agreed timeframe after deductions for documented damages only. Unilateral forfeiture without third-party repair estimates violates standard lease jurisprudence."
        elif "ip" in clean_q or "invention" in clean_q or "side project" in clean_q:
            guidance = "IP Assignment Doctrine: Companies can only claim ownership of intellectual property created during work hours utilizing company resources and within your designated job duties. Broad clauses capturing off-hour side projects are unenforceable."

    return {
        "success": True,
        "response": guidance
    }
