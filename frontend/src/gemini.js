import { GoogleGenAI } from '@google/genai';
import mammoth from 'mammoth';

// High-Resilience Gemini API Key Failover Pool (11 Distinct Google Project Keys)
const ENCODED_KEYS = [
  'QVEuQWI4Uk42SlktN1o4eFVkLVNRWVo4UXV3bXJZWXFXYkI3ZXJaM2RNdEpnaDg4T1NZYnc=', // Key 1
  'QVEuQWI4Uk42S2hwbl9IWUlqR1lfTmdlcWNmYzN1SXRCZnFlZzIxcFhFWjh0YU41dUMxZVE=', // Key 2
  'QVEuQWI4Uk42SXpETzJCMzVaYktaOTlXbVc2WGpSQTg2ZENVN1VRNkxzenFxOXJDX2VtaHc=', // Key 3
  'QVEuQWI4Uk42Sk91eGxsTDZ6T1hRTEk3a2dTVjkzem14a3JFdHhEY3V0SnZQWkdQVXJya1E=', // Key 4
  'QVEuQWI4Uk42S1pOWVB3RjYtSFJ3aGxHb1VkNDFqQ2JWdkNEc2o3S204Wjg5ZEI5TXNZdnc=', // Key 5
  'QVEuQWI4Uk42TDE3dHkxamEwSTVNb0NkOS14WGpvT0tFcmZTODd6QmE3YmxFMEtuY3Q1ZVE=', // Key 6
  'QVEuQWI4Uk42SV96MXFvaV9iazhpVEpIbmxjMjIxalU3aVpKeHJvZTdFeWRmeE9iSXU3emc=', // Key 7
  'QVEuQWI4Uk42SS1ZQ05HaHItV1dTcmZvR2ZtRXZ6cHN0OEVub0RqazctX2xYWW9hYXlKanc=', // Key 8
  'QVEuQWI4Uk42SmdCTXZwTG1VSHBGd3ZGb3RHZkw5Vy1NdWJKVXkyQmVtRFRrd0t3VEtOT0E=', // Key 9
  'QVEuQWI4Uk42SV9xZ0hiQTB4b0hreWJ1SEtSa2tuQzVWX2JJQkdJUXpRbEoxODVHZ2IwdFE=', // Key 10
  'QVEuQWI4Uk42TGxNQXBIcTFwblNUd1RsX1pkNkNzWFpsMHM0Sy12a1FhZXVMdWwyc3lvUVE='  // Key 11
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
  } else if (langLower.includes('telugu') || langLower.includes('te')) {
    return "⚠️ ఇది గుర్తించబడిన చట్టపరమైన పత్రం కాదు. దయచేసి ప్రామాణికమైన చట్టపరమైన పత్రాన్ని అప్‌లోడ్ చేయండి (ఉదా: ఆస్తి దస్తావేజు, ఒప్పంద పత్రం, వైద్య సమ్మతి, పోలీస్ ఎఫ్ఐఆర్, ఎన్‌డిఎ మొదలైనవి).";
  } else if (langLower.includes('kannada') || langLower.includes('kn')) {
    return "⚠️ ಇದು ಮಾನ್ಯತೆ ಪಡೆದ ಕಾನೂನು ದಾಖಲೆಯಲ್ಲ. ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಕಾನೂನು ದಾಖಲೆಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (ಉದಾ: ಆಸ್ತಿ ಪತ್ರ, ಒಪ್ಪಂದ, ವೈದ್ಯಕೀಯ ಸಮ್ಮತಿ, ಪೊಲೀಸ್ ಎಫ್‌ಐಆರ್, ಎನ್‌ಡಿಎ ಇತ್ಯಾದಿ).";
  } else if (langLower.includes('marathi') || langLower.includes('mr')) {
    return "⚠️ हे कोणतेही मान्यताप्राप्त कायदेशीर दस्तऐवज नाही. कृपया वैध कायदेशीर दस्तऐवज अपलोड करा (उदा. मालमत्ता दस्तऐवज, करारनामा, वैद्यकीय संमती, पोलीस तक्रार/एफआयआर, एनडीए इत्यादी).";
  } else if (langLower.includes('tamil') || langLower.includes('ta')) {
    return "⚠️ இது அங்கீகரிக்கப்பட்ட சட்ட ஆவணம் அல்ல. தயவுசெய்து உண்மையான சட்ட ஆவணத்தை பதிவேற்றவும் (எ.கா: சொத்து பத்திரம், ஒப்பந்தம், மருத்துவ ஒப்புதல், காவல் அறிக்கை/எஃப்ஐஆர், என்டிஏ போன்றவை).";
  } else if (langLower.includes('gujarati') || langLower.includes('gu')) {
    return "⚠️ આ કોઈ માન્ય કાનૂની દસ્તાવેજ નથી. કૃપા કરીને માન્ય કાનૂની દસ્તાવેજ અપલોડ કરો (જેમ કે: મિલકત દસ્તાવેજ, કરાર પત્ર, તબીબી સંમતિ, પોલીસ એફઆઈઆર, એનડીએ વગેરે).";
  } else if (langLower.includes('malayalam') || langLower.includes('ml')) {
    return "⚠️ ഇത് അംഗീകൃത നിയമപരമായ രേഖയല്ല. ദയവായി സാധുവായ നിയമപരമായ രേഖ അപ്‌ലോഡ് ചെയ്യുക (ഉദാ: വസ്തു ആധാരം, കരാർ, മെഡിക്കൽ സമ്മതം, പോലീസ് എഫ്ഐആർ, എൻഡിഎ മുതലായവ).";
  } else if (langLower.includes('punjabi') || langLower.includes('pa')) {
    return "⚠️ ਇਹ ਕੋਈ ਮਾਨਤਾ ਪ੍ਰਾਪਤ ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਇੱਕ ਪ੍ਰਮਾਣਿਕ ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ ਅਪਲੋਡ ਕਰੋ (ਜਿਵੇਂ ਕਿ: ਜਾਇਦਾਦ ਦੀ ਰਜਿਸਟਰੀ, ਇਕਰਾਰਨਾਮਾ, ਮੈਡੀਕਲ ਸਹਿਮਤੀ, ਪੁਲਿਸ ਐਫਆਈਆਰ, ਐਨਡੀਏ ਆਦਿ)।";
  } else if (langLower.includes('odia') || langLower.includes('or')) {
    return "⚠️ ଏହା କୌଣସି ସ୍ୱୀକୃତିପ୍ରାପ୍ତ ଆଇନଗତ ଦଲିଲ ନୁହେଁ। ଦୟାକରି ଏକ ବୈଧ ଆଇନଗତ ଦଲିଲ ଅପଲୋଡ୍ କରନ୍ତୁ (ଯଥା: ସମ୍ପତ୍ତି ଦଲିଲ, ଚୁକ୍ତିନାମା, ଚିକିତ୍ସା ସମ୍ମତି, ପୋଲିସ୍ ଏଫ୍ଆଇଆର୍, ଏନ୍ଡିଏ ଇତ୍ୟାଦି)।";
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
  'gemini-3.6-flash'
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
          console.warn(`[Gemini Pool] Model ${model} on Key #${selectedIdx + 1} quota/rate limit reached. Cascading to next model...`);
          continue; // Do NOT abandon the key immediately; try next candidate model!
        } else if (isTemporaryBusy) {
          console.warn(`[Gemini Pool] Model ${model} on Key #${selectedIdx + 1} busy (503). Trying next candidate model...`);
          continue;
        } else {
          console.warn(`[Gemini Pool] Model ${model} on Key #${selectedIdx + 1} notice: ${err.message.slice(0, 70)}. Trying next model...`);
          continue;
        }
      }
    }

    // All candidate models failed on this key, set temporary cooldown and try next key
    keyCooldowns.set(selectedIdx, Date.now() + 5 * 60 * 1000);
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
    } else if (langLower.includes('telugu') || langLower.includes('te')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Telugu using authentic Telugu script (పూర్తి చట్టపరమైన సమీక్ష మరియు నిబంధనలను స్పష్టమైన తెలుగు లిపిలో మాత్రమే రాయండి). Do NOT output English words.`;
    } else if (langLower.includes('kannada') || langLower.includes('kn')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Kannada using authentic Kannada script (ಸಂಪೂರ್ಣ ಕಾನೂನು ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ಕರಡುಗಳನ್ನು ಕನ್ನಡ ಲಿಪಿಯಲ್ಲಿ ಮಾತ್ರ ಬರೆಯಿರಿ). Do NOT output English words.`;
    } else if (langLower.includes('marathi') || langLower.includes('mr')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Marathi using authentic Marathi Devanagari script (संपूर्ण कायदेशीर विश्लेषण आणि पर्यायी अटी शुद्ध मराठी देवनागरी लिपीमध्ये लिहा). Do NOT output English words.`;
    } else if (langLower.includes('tamil') || langLower.includes('ta')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Tamil using authentic Tamil script (முழு சட்ட பகுப்பாய்வு மற்றும் மாற்று விதிகளை தூய தமிழ் எழுத்துக்களில் எழுதவும்). Do NOT output English words.`;
    } else if (langLower.includes('gujarati') || langLower.includes('gu')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Gujarati using authentic Gujarati script (સંપૂર્ણ કાનૂની વિશ્લેષણ અને વૈકલ્પિક શરતો શુદ્ધ ગુજરાતી લિપિમાં લખો). Do NOT output English words.`;
    } else if (langLower.includes('malayalam') || langLower.includes('ml')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Malayalam using authentic Malayalam script (മുഴുവൻ നിയമ വിശകലനവും ആധികാരിക മലയാള ലിപിയിൽ എഴുതുക). Do NOT output English words.`;
    } else if (langLower.includes('punjabi') || langLower.includes('pa')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Punjabi using authentic Gurmukhi script (ਸਾਰਾ ਕਾਨੂੰਨੀ ਵਿਸ਼ਲੇਸ਼ਣ ਗੁਰਮੁਖੀ ਲਿਪੀ ਵਿੱਚ ਲਿਖੋ). Do NOT output English words.`;
    } else if (langLower.includes('odia') || langLower.includes('or')) {
      langInstruction = `CRITICAL: You MUST write the ENTIRE analysis, all headings, clause titles, issues, signer impacts, and attorney counter-drafts exclusively in Odia using authentic Odia script (ସମ୍ପୂର୍ଣ୍ଣ ଆଇନଗତ ବିଶ୍ଳେଷଣ ଓଡ଼ିଆ ଲିପିରେ ଲେଖନ୍ତୁ). Do NOT output English words.`;
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

    // Strict validation check for non-legal documents across all supported languages
    const rejectionKeywords = [
      'not a legal document',
      'not a legal contract',
      'not a recognized legal document',
      'please upload the correct one',
      'please upload the correect one',
      'স্বীকৃত আইনি নথি নয়',
      'मान्यता प्राप्त कानूनी दस्तावेज़ नहीं',
      'గుర్తించబడిన చట్టపరమైన పత్రం కాదు',
      'చట్టపరమైన పత్రం కాదు',
      'ಕಾನೂನು ದಾಖಲೆಯಲ್ಲ',
      'कायदेशीर दस्तऐवज नाही',
      'சட்ட ஆவணம் அல்ல',
      'કાનૂની દસ્તાવેજ નથી',
      'നിയമപരമായ രേഖയല്ല',
      'ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ ਨਹੀਂ',
      'ଆଇନଗତ ଦଲିଲ ନୁହେଁ'
    ];

    const isRejected = rejectionKeywords.some(kw => respLower.includes(kw)) || (respLower.trim() === NON_LEGAL_DOCUMENT_MESSAGE.toLowerCase());

    if (isRejected) {
      return {
        success: true,
        is_legal: false,
        report: getLocalizedRejectionMessage(language),
        engine: engineUsed || 'Gemini Flash'
      };
    }

    return {
      success: true,
      is_legal: true,
      report: respText,
      engine: engineUsed || 'Gemini Flash'
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
    const langLower = (language || '').toLowerCase();
    let chatLangInstruction = `Fluently reply in ${language}.`;
    if (langLower.includes('telugu')) {
      chatLangInstruction = `Fluently reply in authentic Telugu (స్పష్టమైన తెలుగు లిపిలో సమాధానం ఇవ్వండి).`;
    } else if (langLower.includes('kannada')) {
      chatLangInstruction = `Fluently reply in authentic Kannada (ಸ್ಪಷ್ಟ ಕನ್ನಡ ಲಿಪಿಯಲ್ಲಿ ಉತ್ತರಿಸಿ).`;
    } else if (langLower.includes('marathi')) {
      chatLangInstruction = `Fluently reply in authentic Marathi (शुद्ध मराठी देवनागरीत उत्तर द्या).`;
    } else if (langLower.includes('tamil')) {
      chatLangInstruction = `Fluently reply in authentic Tamil (தூய தமிழில் பதிலளிக்கவும்).`;
    } else if (langLower.includes('gujarati')) {
      chatLangInstruction = `Fluently reply in authentic Gujarati (શુદ્ધ ગુજરાતીમાં જવાબ આપો).`;
    } else if (langLower.includes('malayalam')) {
      chatLangInstruction = `Fluently reply in authentic Malayalam (മലയാളത്തിൽ മറുപടി നൽകുക).`;
    } else if (langLower.includes('punjabi')) {
      chatLangInstruction = `Fluently reply in authentic Punjabi (ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ).`;
    } else if (langLower.includes('odia')) {
      chatLangInstruction = `Fluently reply in authentic Odia (ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅନ୍ତୁ).`;
    } else if (langLower.includes('bangla') || langLower.includes('bengali')) {
      chatLangInstruction = `Fluently reply in authentic Bengali (খাঁটি বাংলায় উত্তর দিন).`;
    } else if (langLower.includes('hindi')) {
      chatLangInstruction = `Fluently reply in authentic Hindi (शुद्ध हिंदी में उत्तर दें).`;
    }

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
    - ${chatLangInstruction}
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
