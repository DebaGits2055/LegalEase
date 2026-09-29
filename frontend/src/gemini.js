import { GoogleGenAI } from '@google/genai';
import mammoth from 'mammoth';

// High-Resilience Gemini API Key Failover Pool (10 API Keys)
const ENCODED_KEYS = [
  'QVEuQWI4Uk42SzZsTkJ1cS1JZ0EzMWNHTEtIZ01rN2JaQ3hNUmkyNGtPVGtBc29FQ3dfX2c=',
  'QVEuQWI4Uk42S2tvMl9HaTFDOXFSNjA2Y0xwUFFKWk15SkhsWkxmUEU5a3hLTTN0b3VNT2c=',
  'QVEuQWI4Uk42TFRSTkRvQ3Y5WlpYTHJrMjhvSzBHbENVaTdHX1hiSjdKTGU0Uk43NFNwMEE=',
  'QVEuQWI4Uk42SXhZcms4UFFtNnRZdl91UHoxaVRvRm43TVQ5WlJOMjRJUG1wV0w0ZkV2c1E=',
  'QVEuQWI4Uk42S1BUNThkamtvSTU4TTRUR2lQZVZMZUQ1dDZYS2RMVEtSQjZxR0szWGxscHc=',
  'QVEuQWI4Uk42SmM3aUVSV01iT2E4VVBJM2l0NUNnbFVBbWhHbW9kVTRNV09fTTZqLXBQY3c=',
  'QVEuQWI4Uk42TGt5WG00WWViemZaeXY5VldyeXduQmZoQkctZWZBelR1RHpVZW1EblRYclE=',
  'QVEuQWI4Uk42THJKQ2tjQ1ptaXA1bjR0aFlpQVFjMGVsdjdTNG5vcWc1c0xNSXU2SWYyeUE=',
  'QVEuQWI4Uk42Smg5Y200T1lBaFdxTVZLSWpabTcyelIwalEzcGNQb0tLRmFLTlROckprVmc=',
  'QVEuQWI4Uk42Skk2QWlUNTJiNE1CUDF4bWtBbTRjcGpPeWJreHlHMG5ZYVB6R3lQQkFzX0E='
];

const decodeKey = (b64) => {
  try {
    if (typeof atob === 'function') {
      return atob(b64);
    }
    return Buffer.from(b64, 'base64').toString('utf-8');
  } catch {
    return b64;
  }
};

export const GEMINI_API_KEY_POOL = ENCODED_KEYS.map(decodeKey);

const getEnvironmentKeyPool = () => {
  const envVal = (typeof import.meta !== 'undefined' && import.meta.env && (import.meta.env.VITE_GEMINI_API_KEYS || import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.GEMINI_API_KEY)) || (typeof process !== 'undefined' && process.env && (process.env.VITE_GEMINI_API_KEYS || process.env.VITE_GEMINI_API_KEY || process.env.GEMINI_API_KEY)) || '';
  if (!envVal) return GEMINI_API_KEY_POOL;
  const customKeys = envVal.split(',').map(k => k.trim()).filter(Boolean);
  return Array.from(new Set([...customKeys, ...GEMINI_API_KEY_POOL]));
};

export const API_KEYS = getEnvironmentKeyPool();


export const NON_LEGAL_DOCUMENT_MESSAGE = "This is not a recognized legal document. Please upload an authentic legal instrument (Property Deed, Medical Consent, Criminal/Police Report, Employment Agreement, NDA, etc.).";

export const getLocalizedRejectionMessage = (language = 'English') => {
  const langLower = (language || '').toLowerCase();
  if (langLower.includes('bangla') || langLower.includes('bengali') || langLower.includes('bn')) {
    return "⚠️ এটি কোনো স্বীকৃত আইনি নথি নয়। অনুগ্রহ করে একটি বৈধ আইনি নথি আপলোড করুন (যেমন: সম্পত্তির দলিল, চুক্তিপত্র, চিকিৎসা সম্মতি, পুলিশ এফআইআর, এনডিএ ইত্যাদি)।";
  } else if (langLower.includes('hindi') || langLower.includes('hi')) {
    return "⚠️ यह कोई मान्यता प्राप्त कानूनी दस्तावेज़ नहीं है। कृपया एक वैध कानूनी दस्तावेज़ अपलोड करें (जैसे: संपत्ति विलेख, अनुबंध पत्र, चिकित्सा सहमति, पुलिस प्राथमिकी/एफआईआर, एनडीए आदि)।";
  }
  return `⚠️ ${NON_LEGAL_DOCUMENT_MESSAGE}`;
};

export const LEGAL_PLAYBOOK = `
You are an Elite Enterprise Legal Counsel & Contract Risk Auditor trained across Bar Association standards and statutory codes.

### MANDATORY PHASE 0: STRICT LEGAL RECOGNITION CHECK
1. Check if the uploaded file is an authentic legal instrument (e.g. employment agreement, NDA, residential lease, commercial contract, service terms, power of attorney, affidavit, police report, medical consent).
2. If NOT a genuine legal document (e.g. food recipe, homework, receipts, landscape, random code, memes, personal selfies), STOP IMMEDIATELY and reply ONLY with:
${NON_LEGAL_DOCUMENT_MESSAGE}

### PHASE 1: CRISP, HIGH-IMPACT PLAYBOOK AUDIT (HIGHLIGHT RED FLAGS FIRST)
If verified, provide a clean, executive, brief audit.
CRITICAL FORMATTING RULES:
- Highlight TOP RED FLAGS FIRST with clear Risk Levels.
- For each flagged clause, provide a practical Attorney Counter-Draft with copyable replacement text.
- Keep explanations brief, punchy, and jargon-free (under 400 words total).
- Do NOT use ascii divider lines (like ===, ---, ### lines), markdown table clutter, or excessive symbols.

Structure your response clearly with these 4 headings:

## 🚨 CRITICAL RED FLAGS & RISK LEVELS (HIGHLIGHTED FIRST)
For each dangerous clause or trap found in the document, list:
- [🔴 HIGH RISK] or [🟡 MEDIUM RISK] or [🟢 LOW RISK]: [Name of Clause]
  • Issue: [1 brief sentence explaining the unfair clause or hidden trap]
  • Signer Impact: [Direct financial, career, or legal penalty to the signer]
  • Attorney Counter-Draft: [Copyable replacement clause protecting the signer]

## 📊 EXECUTIVE SUMMARY & COMPLIANCE SCORE
- Document Type: [e.g. Employment Contract / Residential Lease / NDA]
- Overall Health Score: [e.g. 65/100 • Moderate Risk Detected]
- Executive Verdict: [2 crisp sentences summarizing overall safety]

## 🛡️ 4-PILLAR PLAYBOOK CHECK
- Non-Compete & Restraint of Trade: [Pass / Flagged - 1 brief sentence referencing Section 27 if applicable]
- IP Assignment Scope: [Pass / Flagged - 1 brief sentence]
- Termination & Notice Cure Periods: [Pass / Flagged - 1 brief sentence]
- Indemnification & Liability Caps: [Pass / Flagged - 1 brief sentence]

## 📝 ACTIONABLE NEXT STEPS BEFORE SIGNING
1. [Key item to negotiate or strike out]
2. [Documentary proof or clarification to request in writing]
3. [Safety condition before signing]
`;

export const getMimeType = (file) => {
  if (file.type && file.type !== 'application/octet-stream') {
    return file.type;
  }
  const name = (file.name || '').toLowerCase();
  if (name.endsWith('.pdf')) return 'application/pdf';
  if (name.endsWith('.png')) return 'image/png';
  if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg';
  if (name.endsWith('.webp')) return 'image/webp';
  if (name.endsWith('.docx')) return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  return 'image/jpeg';
};

// Helper: Convert browser File / Blob to base64
export const fileToGenerativePart = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Data = reader.result ? reader.result.split(',')[1] : '';
      resolve({
        inlineData: {
          data: base64Data,
          mimeType: getMimeType(file)
        }
      });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

export const prepareContentPayload = async (file, prompt) => {
  const fileName = (file.name || '').toLowerCase();

  // 1. If DOCX file, extract text via mammoth for 100% reliable Gemini processing
  if (fileName.endsWith('.docx') || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      const docxText = (result?.value || '').trim();
      if (docxText) {
        return [
          {
            text: `DOCUMENT CONTENT (Extracted from ${file.name}):\n\n${docxText}\n\n=========================================\n${prompt}`
          }
        ];
      }
    } catch (docxErr) {
      console.warn('DOCX mammoth extraction fallback:', docxErr);
    }
  }

  // 2. If Plain Text / Markdown / CSV
  if (fileName.endsWith('.txt') || fileName.endsWith('.md') || fileName.endsWith('.csv') || (file.type && file.type.startsWith('text/'))) {
    try {
      const text = await file.text();
      return [
        {
          text: `DOCUMENT CONTENT (from ${file.name}):\n\n${text}\n\n=========================================\n${prompt}`
        }
      ];
    } catch (txtErr) {
      console.warn('Text file read error:', txtErr);
    }
  }

  // 3. For PDF and Image files (PNG, JPG, WEBP)
  const filePart = await fileToGenerativePart(file);
  return [filePart, prompt];
};

const CANDIDATE_MODELS = [
  'gemini-3.8-flash',
  'gemini-3.7-flash',
  'gemini-3.6-flash',
  'gemini-3.5-flash',
  'gemini-3.1-flash-lite',
  'gemini-flash-latest'
];

let activeKeyIndex = 0;
const keyCooldowns = new Map(); // keyIndex -> cooldown timestamp

export const generateWithResilience = async (contents) => {
  const pool = API_KEYS.length > 0 ? API_KEYS : GEMINI_API_KEY_POOL;
  if (!pool || pool.length === 0) {
    throw new Error('Google Gemini API key pool is empty. Please check your configuration.');
  }

  const now = Date.now();
  let lastErr = null;
  const totalKeys = pool.length;

  for (let keyAttempt = 0; keyAttempt < totalKeys; keyAttempt++) {
    const selectedIdx = (activeKeyIndex + keyAttempt) % totalKeys;
    const cooldown = keyCooldowns.get(selectedIdx) || 0;

    // Skip keys currently in cooldown unless it's the last available attempt
    if (now < cooldown && keyAttempt < totalKeys - 1) {
      continue;
    }

    const apiKey = pool[selectedIdx];
    const client = new GoogleGenAI({ apiKey });
    let keyQuotaExceeded = false;

    for (const model of CANDIDATE_MODELS) {
      try {
        const response = await client.models.generateContent({
          model,
          contents
        });

        const text = (response.text || '').trim();
        if (text) {
          activeKeyIndex = selectedIdx; // Remember healthy key
          const readableEngine = `Gemini ${model.replace('gemini-', '').replace('-latest', ' Latest')} (Key #${selectedIdx + 1})`;
          console.log(`[Gemini Engine] Generated successfully with Key #${selectedIdx + 1} (${model})`);
          return {
            text,
            engine: readableEngine
          };
        }
      } catch (err) {
        const msg = (err.message || '').toLowerCase();
        lastErr = err;

        const isQuotaOrLimit =
          msg.includes('429') ||
          msg.includes('quota') ||
          msg.includes('resource_exhausted') ||
          msg.includes('rate limit');

        const isTemporaryBusy =
          msg.includes('503') ||
          msg.includes('high demand') ||
          msg.includes('high traffic') ||
          msg.includes('overloaded');

        if (isQuotaOrLimit) {
          console.warn(`[Gemini Pool] Key #${selectedIdx + 1} quota/limit reached (${err.message.slice(0, 70)}). Activating 10-min cooldown and auto-switching to next key...`);
          keyCooldowns.set(selectedIdx, Date.now() + 10 * 60 * 1000);
          keyQuotaExceeded = true;
          break; // Break model loop, switch to next key immediately
        } else if (isTemporaryBusy) {
          console.warn(`[Gemini Pool] Model ${model} on Key #${selectedIdx + 1} busy (503). Trying next candidate model...`);
          continue;
        } else {
          console.warn(`[Gemini Pool] Model ${model} on Key #${selectedIdx + 1} notice: ${err.message.slice(0, 70)}. Trying next model...`);
          continue;
        }
      }
    }

    if (keyQuotaExceeded) {
      continue;
    }
  }

  let finalMsg = lastErr?.message || 'All Gemini API keys in the failover pool are temporarily unavailable.';
  try {
    if (finalMsg.includes('{')) {
      const jsonMatch = finalMsg.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.error?.message) {
          finalMsg = parsed.error.message;
        }
      }
    }
  } catch (_) {}

  throw new Error(`AI Engine Failover Notice: ${finalMsg}`);
};

export const auditDocumentWithGemini = async (file, language = 'English', isProModel = false) => {
  const pool = API_KEYS.length > 0 ? API_KEYS : GEMINI_API_KEY_POOL;
  if (!pool || pool.length === 0) {
    return {
      success: false,
      error: 'Google Gemini API key pool not configured.'
    };
  }

  try {
    const langLower = (language || '').toLowerCase();
    let langInstruction = `Respond entirely and fluently in ${language}.`;
    if (langLower.includes('bangla') || langLower.includes('bengali') || langLower.includes('bn')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Bengali using authentic Bangla script (সম্পূর্ণ বিশ্লেষণটি খাঁটি বাংলা লিপিতে লিখুন). Do NOT output English words.`;
    } else if (langLower.includes('hindi') || langLower.includes('hi')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Hindi using authentic Devanagari script (संपूर्ण विश्लेषण हिंदी देवनागरी लिपि में लिखें). Do NOT output English words.`;
    }

    const contents = await prepareContentPayload(file, `
    ${LEGAL_PLAYBOOK}
    =========================================
    CRITICAL LANGUAGE INSTRUCTION:
    If and ONLY if the document is verified as an authentic legal document, ${langInstruction}
    If this is NOT a legal document, do NOT translate, do NOT provide any descriptions, and respond ONLY with:
    ${NON_LEGAL_DOCUMENT_MESSAGE}
    `);

    const { text: respText, engine: engineUsed } = await generateWithResilience(contents);
    const respLower = respText.toLowerCase();

    // Strict validation check for non-legal documents
    const rejectionKeywords = [
      'not a legal document',
      'not a legal contract',
      'not a recognized legal document',
      'please upload the correct one',
      'please upload the correect one',
      'স্বীকৃত আইনি নথি নয়',
      'मान्यता प्राप्त कानूनी दस्तावेज़ नहीं'
    ];

    const isRejected = rejectionKeywords.some(kw => respLower.includes(kw)) || (respLower.trim() === NON_LEGAL_DOCUMENT_MESSAGE.toLowerCase());

    if (isRejected) {
      return {
        success: true,
        is_legal: false,
        report: getLocalizedRejectionMessage(language),
        engine: engineUsed || 'Gemini 3.8 Flash'
      };
    }

    return {
      success: true,
      is_legal: true,
      report: respText,
      engine: engineUsed || 'Gemini 3.8 Flash'
    };
  } catch (err) {
    console.error('Gemini Audit Error:', err);
    return {
      success: false,
      error: `Gemini AI Engine processing error: ${err.message}`
    };
  }
};

export const chatWithLegalCounsel = async (userMessage, documentContext = '', language = 'English') => {
  const pool = API_KEYS.length > 0 ? API_KEYS : GEMINI_API_KEY_POOL;
  if (!pool || pool.length === 0) {
    return {
      success: false,
      error: 'Google Gemini API key pool not configured.'
    };
  }

  try {
    const prompt = `
    You are LegalEase AI Counsel — an elite legal risk advisor.
    The user is asking questions about their uploaded agreement.
    
    DOCUMENT AUDIT CONTEXT:
    ${documentContext ? documentContext.substring(0, 5000) : 'No document currently uploaded. Answer general contract law questions.'}

    USER QUESTION:
    ${userMessage}

    CRITICAL INSTRUCTIONS:
    - Respond concisely with high legal accuracy and tactical advice.
    - Provide precise revision wording / redlines where applicable.
    - Fluently reply in ${language}.
    `;

    const { text: replyText } = await generateWithResilience([prompt]);

    return {
      success: true,
      reply: replyText
    };
  } catch (err) {
    console.error('Chat Error:', err);
    return {
      success: false,
      error: `Failed to consult Legal Counsel: ${err.message}`
    };
  }
};
