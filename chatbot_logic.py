import re, os, json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

MONTH_MAP = {
    # English
    'january': '01', 'jan': '01',
    'february': '02', 'feb': '02',
    'march': '03', 'mar': '03',
    'april': '04', 'apr': '04',
    'may': '05',
    'june': '06', 'jun': '06',
    'july': '07', 'jul': '07',
    'august': '08', 'aug': '08',
    'september': '09', 'sep': '09', 'sept': '09',
    'october': '10', 'oct': '10',
    'november': '11', 'nov': '11',
    'december': '12', 'dec': '12',
    # Kannada
    'ಜನವರಿ': '01', 'ಜನವಾರಿ': '01',
    'ಫೆಬ್ರವರಿ': '02', 'ಫೆಬ್ರುವರಿ': '02',
    'ಮಾರ್ಚ್': '03',
    'ಏಪ್ರಿಲ್': '04',
    'ಮೇ': '05',
    'ಜೂನ್': '06',
    'ಜುಲೈ': '07',
    'ಆಗಸ್ಟ್': '08', 'ಅಗಸ್ಟ್': '08',
    'ಸೆಪ್ಟೆಂಬರ್': '09', 'ಸೆಪ್ಟಂಬರ್': '09',
    'ಅಕ್ಟೋಬರ್': '10', 'ಅಕ್ಟೋಬರ': '10',
    'ನವೆಂಬರ್': '11', 'ನವೆಂಬರ': '11',
    'ಡಿಸೆಂಬರ್': '12', 'ಡಿಸೆಂಬರ': '12'
}

def parse_dob(text):
    """
    Parses spoken or written Date of Birth in English or Kannada and converts it
    into strict ISO YYYY-MM-DD format (required by HTML5 <input type="date">).
    """
    if not text:
        return None
    raw = str(text).strip()
    
    # 1. Already strict YYYY-MM-DD
    m_iso = re.search(r'\b(19\d\d|20[0-2]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b', raw)
    if m_iso:
        return m_iso.group(0)

    # Clean ordinals: 15th -> 15, 1st -> 1, 15ನೇ -> 15
    cleaned = re.sub(r'(\d+)(?:st|nd|rd|th|ನೇ)', r'\1', raw, flags=re.IGNORECASE)

    # 2. Match DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
    m_dmy = re.search(r'\b(0?[1-9]|[12]\d|3[01])[\/\-\.\s](0?[1-9]|1[0-2])[\/\-\.\s](19\d\d|20[0-2]\d)\b', cleaned)
    if m_dmy:
        d = int(m_dmy.group(1))
        m = int(m_dmy.group(2))
        y = m_dmy.group(3)
        return f"{y}-{m:02d}-{d:02d}"

    # 3. Match YYYY-MM-DD with slashes or spaces
    m_ymd = re.search(r'\b(19\d\d|20[0-2]\d)[\/\-\.\s](0?[1-9]|1[0-2])[\/\-\.\s](0?[1-9]|[12]\d|3[01])\b', cleaned)
    if m_ymd:
        y = m_ymd.group(1)
        m = int(m_ymd.group(2))
        d = int(m_ymd.group(3))
        return f"{y}-{m:02d}-{d:02d}"

    # 4. Text month: e.g. "15 August 1998", "15 ಆಗಸ್ಟ್ 1998", "August 15 1998"
    month_names_pattern = "|".join([re.escape(k) for k in MONTH_MAP.keys()])
    
    # Pattern A: Day Month Year (e.g. 15 August 1998 or 15 ಆಗಸ್ಟ್ 1998)
    m_d_m_y = re.search(r'\b(0?[1-9]|[12]\d|3[01])\s*(?:of)?\s*(' + month_names_pattern + r')\s*,?\s*(19\d\d|20[0-2]\d)\b', cleaned, flags=re.IGNORECASE)
    if m_d_m_y:
        d = int(m_d_m_y.group(1))
        mon_str = m_d_m_y.group(2).lower()
        y = m_d_m_y.group(3)
        m_num = MONTH_MAP.get(mon_str)
        if m_num:
            return f"{y}-{m_num}-{d:02d}"

    # Pattern B: Month Day Year (e.g. August 15 1998)
    m_m_d_y = re.search(r'\b(' + month_names_pattern + r')\s*(0?[1-9]|[12]\d|3[01])\s*,?\s*(19\d\d|20[0-2]\d)\b', cleaned, flags=re.IGNORECASE)
    if m_m_d_y:
        mon_str = m_m_d_y.group(1).lower()
        d = int(m_m_d_y.group(2))
        y = m_m_d_y.group(3)
        m_num = MONTH_MAP.get(mon_str)
        if m_num:
            return f"{y}-{m_num}-{d:02d}"

    # Pattern C: Year Month Day (e.g. 1998 ಆಗಸ್ಟ್ 15)
    m_y_m_d = re.search(r'\b(19\d\d|20[0-2]\d)\s*(' + month_names_pattern + r')\s*(0?[1-9]|[12]\d|3[01])\b', cleaned, flags=re.IGNORECASE)
    if m_y_m_d:
        y = m_y_m_d.group(1)
        mon_str = m_y_m_d.group(2).lower()
        d = int(m_y_m_d.group(3))
        m_num = MONTH_MAP.get(mon_str)
        if m_num:
            return f"{y}-{m_num}-{d:02d}"

    return None

def extract_phone_or_aadhaar(text):
    """
    Extracts a 10-digit Indian mobile number or 12-digit Aadhaar number from
    spoken or written text in English or Kannada, handling digits with spaces (e.g. '9080 400 291'),
    Kannada numerals (೦-೯), and spoken word digits ('nine, zero, eight...').
    """
    if not text:
        return None, None
    raw = str(text)

    # 1. Convert Kannada script numerals ೦-೯ to English digits 0-9
    kn_digits = {'೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4', '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9'}
    for kn_char, en_digit in kn_digits.items():
        raw = raw.replace(kn_char, en_digit)

    # 2. Convert spoken word digits to digits
    word_to_digit = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'o': '0', 'oh': '0',
        'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
        'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
    }
    words = raw.lower().split()
    converted_words = []
    for w in words:
        w_clean = re.sub(r'[^a-zA-Zಀ-೿]', '', w)
        if w_clean in word_to_digit:
            converted_words.append(word_to_digit[w_clean])
        else:
            converted_words.append(w)
    converted_str = " ".join(converted_words)

    # 3. Collapse whitespace and punctuation between digits (e.g. '9080 400 291' -> '9080400291')
    collapsed = re.sub(r'(?<=\d)[\s,\.\-]+(?=\d)', '', converted_str)

    # 4. Check for 12-digit Aadhaar number
    m_aadhaar = re.search(r'\b(\d{12})\b', collapsed)
    if m_aadhaar:
        return 'aadhaar', m_aadhaar.group(1)

    # 5. Check for 10-digit Indian Mobile number (starts with 6,7,8,9)
    m_phone = re.search(r'\b([6-9]\d{9})\b', collapsed)
    if m_phone:
        return 'phone', m_phone.group(1)

    # 6. Any standard 10-digit number
    m_10 = re.search(r'\b(\d{10})\b', collapsed)
    if m_10:
        return 'phone', m_10.group(1)

    return None, None

def extract_account_number(text):
    """
    Extracts bank account number (e.g. ACC80001, ACC80000..ACC89999 or 5-12 digit account)
    from spoken or written English/Kannada text, handling spaces, punctuation,
    'a c c', 'acc', 'account', spoken word digits ('eight zero zero zero one').
    """
    if not text:
        return None
    raw = str(text)

    # 1. Convert Kannada script numerals ೦-೯ to English digits 0-9
    kn_digits = {'೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4', '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9'}
    for kn_char, en_digit in kn_digits.items():
        raw = raw.replace(kn_char, en_digit)

    # 2. Convert spoken word digits to digits
    word_to_digit = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'o': '0', 'oh': '0',
        'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
        'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
    }
    words = raw.lower().split()
    converted_words = []
    for w in words:
        w_clean = re.sub(r'[^a-zA-Z0-9ಀ-೿]', '', w)
        if w_clean in word_to_digit:
            converted_words.append(word_to_digit[w_clean])
        else:
            converted_words.append(w)
    converted_str = ' '.join(converted_words)

    # 3. Handle 'a c c', 'a.c.c', 'a c c.', 'acc', 'account', 'acc no', 'account number', 'ಖಾತೆ', 'ಖಾತೆ ಸಂಖ್ಯೆ'
    normalized = re.sub(r'\b(?:a[\s\.\,]*c[\s\.\,]*c|acc|account|acc\s*no\.?|account\s*number|acct|acct\s*no\.?|ಖಾತೆ\s*(?:ಸಂಖ್ಯೆ)?)\s*#?\s*', 'ACC', converted_str, flags=re.IGNORECASE)
    
    def collapse_acc_digits(m):
        digits = re.sub(r'[\s,\.\-]+', '', m.group(1))
        return 'ACC' + digits

    normalized = re.sub(r'ACC\s*([0-9\s,\.\-]+)', collapse_acc_digits, normalized, flags=re.IGNORECASE)

    # 4. Match ACC followed by 4-12 digits
    m_acc = re.search(r'\b(ACC\d{4,12})\b', normalized, re.IGNORECASE)
    if m_acc:
        return m_acc.group(1).upper()

    # 5. Match standalone 5-digit account number starting with 8 (e.g. 80000, 80001, 80002)
    m_5digit = re.search(r'\b(8\d{4})\b', normalized)
    if m_5digit:
        return f"ACC{m_5digit.group(1)}"

    return None

def extract_spoken_name(text):
    """
    Extracts a spoken or written full name from English or Kannada queries:
    - 'type my name Pawan Kumar my mobile number 9380 400291' -> 'Pawan Kumar'
    - 'in registration page fill my name is Pawan Kumar' -> 'Pawan Kumar'
    - 'full name Pawan Kumar' -> 'Pawan Kumar'
    - 'my name is Pawan Kumar' -> 'Pawan Kumar'
    - 'my name Pawan Kumar' -> 'Pawan Kumar'
    - 'fill my name as Pawan Kumar' -> 'Pawan Kumar'
    - 'name is Pawan Kumar' -> 'Pawan Kumar'
    - 'ನನ್ನ ಹೆಸರು ಪವನ್ ಕುಮಾರ್' -> 'ಪವನ್ ಕುಮಾರ್'
    - 'ಪೂರ್ಣ ಹೆಸರು ಪವನ್ ಕುಮಾರ್' -> 'ಪವನ್ ಕುಮಾರ್'
    """
    if not text:
        return None
    raw = str(text).strip()

    split_words = r'(?:and\s+)?(?:my\s+)?(?:mobile|phone|contact|aadhaar|num|number|password|pin|ಮೊಬೈಲ್|ಆಧಾರ್|ಪಾಸ್‌ವರ್ಡ್|ಪಿನ್|ಸಂಖ್ಯೆ)'
    split_pattern = r'\s+(?:' + split_words + r')(?:\s+|$|\d)|\s*\d'

    # 1. Prefix pattern for explicit name declaration
    prefix = r'(?:\b(?:in\s+registration(?:\s+(?:page|form|tab|section))?\s+)?(?:type|fill|put|enter|write|set)?\s*(?:in\s+registration(?:\s+(?:page|form|tab|section))?\s+)?(?:my\s+)?(?:full\s+)?(?:name|ಹೆಸರು|ಪೂರ್ಣ\s*ಹೆಸರು)\s*(?:is|as|:|\s)?\s*)'
    m = re.search(prefix + r'([A-Za-z\u0C80-\u0CFF\s]+)', raw, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        split_match = re.split(split_pattern, candidate, flags=re.IGNORECASE)
        name = split_match[0].strip()
        name = re.sub(r'^(?:is|as)\s+', '', name, flags=re.IGNORECASE).strip()
        blacklisted = {'is', 'as', 'my', 'the', 'a', 'in', 'page', 'tab', 'form', 'section', 'registration', 'register', 'login', 'kyc', 'aadhaar', 'password', 'pin', 'pass', 'ಪಾಸ್‌ವರ್ಡ್', 'ಪಿನ್'}
        if name.lower() not in blacklisted and len(name) >= 2:
            return name

    # 2. Check if text begins directly with 'name <Name>' or 'full name <Name>'
    m_direct = re.search(r'^(?:my\s+)?(?:full\s+)?(?:name|ಹೆಸರು)\s+(?:is\s+)?([A-Za-z\u0C80-\u0CFF\s]+)', raw, re.IGNORECASE)
    if m_direct:
        candidate = m_direct.group(1).strip()
        split_match = re.split(split_pattern, candidate, flags=re.IGNORECASE)
        name = split_match[0].strip()
        name = re.sub(r'^(?:is|as)\s+', '', name, flags=re.IGNORECASE).strip()
        blacklisted = {'is', 'as', 'my', 'the', 'a', 'in', 'page', 'tab', 'form', 'section', 'registration', 'register', 'login', 'kyc', 'aadhaar', 'password', 'pin', 'pass', 'ಪಾಸ್‌ವರ್ಡ್', 'ಪಿನ್'}
        if name.lower() not in blacklisted and len(name) >= 2:
            return name

    return None

def extract_password(text, bot_asked_pwd=False):
    """
    Extracts spoken or written passwords/PINs from diverse English and Kannada expressions:
    - '123456 as pass' -> '123456'
    - '123456 as password' -> '123456'
    - '123456 is pass' -> '123456'
    - '123456 is my password' -> '123456'
    - 'take 123456 as pass' -> '123456'
    - 'set 123456 as pass' -> '123456'
    - 'password 123456' -> '123456'
    - 'pass 123456' -> '123456'
    - 'pin 123456' -> '123456'
    - '123456 pass' -> '123456'
    - '123456 password' -> '123456'
    - '1 2 3 4 5 6 as pass' -> '123456'
    - '12 34 56 as pass' -> '123456'
    - 'ಪಾಸ್‌ವರ್ಡ್ 123456' -> '123456'
    - '123456 ಪಾಸ್‌ವರ್ಡ್' -> '123456'
    - '123456 ಅಂತ ಪಾಸ್‌ವರ್ಡ್' -> '123456'
    """
    if not text:
        return None
    raw = str(text).strip()

    # 1. Keyword first: e.g. 'password 123456', 'pass is 123456', 'pin: 123456'
    m_kw_first = re.search(r'\b(?:password|pass|pin|ಪಾಸ್‌ವರ್ಡ್|ಪಿನ್)\b(?:\s+is|\s+as|\s*:)?\s*([A-Za-z0-9@#$%^&*!_+=-]+(?:\s+[A-Za-z0-9@#$%^&*!_+=-]+)*)', raw, re.IGNORECASE)
    if m_kw_first:
        val = m_kw_first.group(1).strip()
        val = re.sub(r'^(?:is|as)\s+', '', val, flags=re.IGNORECASE).strip()
        if re.match(r'^[\d\s]+$', val):
            val = re.sub(r'\s+', '', val)
        if len(val) >= 4:
            return val

    # 2. Value first: e.g. '123456 as pass', '123456 as password', '123456 is my password', 'take 123456 as pass', '123456 pass'
    m_val_first = re.search(r'(?:(?:take|set|put|enter|use|keep|give|make)\s+)?([A-Za-z0-9@#$%^&*!_+=-]+(?:\s+[A-Za-z0-9@#$%^&*!_+=-]+)*?)\s+(?:as|is|my|the|to|ಎಂದು|ಅಂತ)?\s*(?:my\s+)?\b(?:password|pass|pin|ಪಾಸ್‌ವರ್ಡ್|ಪಿನ್)\b', raw, re.IGNORECASE)
    if m_val_first:
        val = m_val_first.group(1).strip()
def extract_email(text, user_name=""):
    """
    Extracts, normalizes, and cleans an email address from typed or spoken text in English or Kannada.
    Handles standard email e.g. user@gmail.com, as well as complex spoken/phonetic patterns:
    - 'p a v a n k 5214@gmail.com' -> pavank5214@gmail.com
    - 'my email is pavan 1 2 3 at the rate gmail dot com' -> pavan123@gmail.com
    - 'chaithanya rajkumar at gmail com' -> chaithanyarajkumar@gmail.com
    - 'pavan @ gmail . com' -> pavan@gmail.com
    - 'pavan dot kumar at outlook dot com' -> pavan.kumar@outlook.com
    - 'pavan gmail com' -> pavan@gmail.com
    - 'ಪವನ್ 123 ಅಟ್ ಜಿಮೇಲ್ ಡಾಟ್ ಕಾಮ್' -> pavan123@gmail.com
    - 'siriaibank at gmail dot com' -> siriaibank@gmail.com
    Also uses Gemini AI to cleanly resolve conversational/noisy spoken inputs.
    """
    if not text:
        return None
    raw = str(text).strip()

    # 1. Rule-based phonetic & spoken normalization
    s = raw

    # Remove conversational prefixes
    s = re.sub(r'^(?:my\s+)?(?:email|mail|e-mail)(?:\s+address|\s+id)?\s*(?:is|as|:)?\s*', '', s, flags=re.I)
    s = re.sub(r'^(?:take|set|put|enter|fill|use)\s+(?:my\s+)?(?:email|mail|e-mail)\s*(?:as|is|:)?\s*', '', s, flags=re.I)
    s = re.sub(r'^(?:ನನ್ನ\s+)?(?:ಇಮೇಲ್|ಮೇಲ್)(?:\s*ವಿಳಾಸ)?\s*(?:ಆಗಿದೆ|ಇದೆ|:)?\s*', '', s, flags=re.I)

    # Kannada transliterations
    kn_map = {
        'ಅಟ್ ದ ರೇಟ್ ಆಫ್': ' @ ', 'ಅಟ್ ದ ರೇಟ್': ' @ ', 'ಅಟ್ ದಿ ರೇಟ್': ' @ ', 'ಅಟ್': ' @ ', 'ಆಟ್': ' @ ',
        'ಡಾಟ್': ' . ', 'ಚುಕ್ಕೆ': ' . ', 'ಜಿಮೇಲ್': 'gmail', 'ಯಾಹೂ': 'yahoo', 'ಔಟ್‌ಲುಕ್': 'outlook',
        'ಹಾಟ್‌ಮೇಲ್': 'hotmail', 'ಕಾಮ್': 'com', 'ಇನ್': 'in', 'ಅಂಡರ್‌ಸ್ಕೋರ್': '_', 'ಡ್ಯಾಶ್': '-', 'ಹೈಫನ್': '-'
    }
    for k, v in sorted(kn_map.items(), key=lambda x: len(x[0]), reverse=True):
        s = s.replace(k, v)

    # Kannada name common transliterations
    kn_name_map = {
        'ಪವನ್': 'pavan', 'ಕುಮಾರ್': 'kumar', 'ಚೈತನ್ಯ': 'chaithanya', 'ರಾಜ್‌ಕುಮಾರ್': 'rajkumar',
        'ರಾಜಕುಮಾರ್': 'rajkumar', 'ರಮೇಶ್': 'ramesh', 'ಸುರೇಶ್': 'suresh', 'ಮಹೇಶ್': 'mahesh',
        'ಗಣೇಶ್': 'ganesh', 'ಆನಂದ್': 'anand', 'ಪ್ರಕಾಶ್': 'prakash', 'ಮಂಜುನಾಥ್': 'manjunath',
        'ಕಿರಣ್': 'kiran', 'ಪ್ರಶಾಂತ್': 'prashanth', 'ಸಂತೋಷ್': 'santhosh', 'ವಿಜಯ್': 'vijay',
        'ರಾಜು': 'raju', 'ರವಿ': 'ravi', 'ರಾಹುಲ್': 'rahul', 'ಅರುಣ್': 'arun', 'ಅನಿಲ್': 'anil'
    }
    for k, v in kn_name_map.items():
        s = s.replace(k, v)

    # Word-to-digit conversion
    word_to_digit = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
        'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
    }
    for w, d in word_to_digit.items():
        s = re.sub(r'\b' + re.escape(w) + r'\b', d, s, flags=re.I)

    # English spoken patterns
    s = re.sub(r'\b(?:at\s+the\s+rate\s+of|at\s+the\s+rate|at\s+rate|at\s+sign|at\s+the|at)\b', ' @ ', s, flags=re.I)
    s = re.sub(r'\b(?:dot|point|period)\b', ' . ', s, flags=re.I)
    s = re.sub(r'\b(?:underscore)\b', '_', s, flags=re.I)
    s = re.sub(r'\b(?:hyphen|dash)\b', '-', s, flags=re.I)

    # If no @ yet, but has known domain name
    if '@' not in s:
        s = re.sub(r'\b(?:gmail|yahoo|outlook|hotmail|icloud|protonmail|rediffmail)\b', r'@ \g<0>', s, flags=re.I)

    # Collapse multiple @ signs
    s = re.sub(r'@+', '@', s)

    if '@' in s:
        parts = s.split('@', 1)
        # Username part: strip all whitespace & non-email characters (collapses spoken spaced letters)
        user_part = re.sub(r'\s+', '', parts[0].lower())
        user_part = re.sub(r'[^a-zA-Z0-9._+-]', '', user_part)
        if (not user_part or user_part.isdigit()) and user_name:
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', user_name.lower())
            user_part = f"{clean_name}{user_part}" if clean_name else user_part

        # Domain part: normalize dots & strip whitespace
        domain_part = parts[1].lower()
        domain_part = re.sub(r'\s*\.\s*', '.', domain_part)
        domain_part = re.sub(r'\s+', '', domain_part)
        domain_part = re.sub(r'[^a-zA-Z0-9.-]', '', domain_part)

        known_domains = {'gmail', 'yahoo', 'outlook', 'hotmail', 'icloud', 'protonmail', 'rediffmail'}
        for dom in known_domains:
            if domain_part == dom:
                domain_part = f"{dom}.com"
            elif domain_part.startswith(dom) and not domain_part.startswith(f"{dom}."):
                rest = domain_part[len(dom):]
                if rest in ['com', 'in', 'org', 'co', 'net']:
                    domain_part = f"{dom}.{rest}"
                else:
                    domain_part = f"{dom}.com"

        if '.' not in domain_part:
            domain_part += '.com'

        if user_part and domain_part:
            clean_email = f"{user_part}@{domain_part}"
            if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', clean_email):
                return clean_email

    # Direct standard email match fallback
    m_std = re.search(r'\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b', raw)
    if m_std:
        return m_std.group(1).lower()

    # 3. Intelligent AI Resolution via Gemini (if available) for complex or natural language utterances
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    if api_key and len(raw) >= 3 and not any(w in raw.lower() for w in ['balance', 'transfer', 'cancel', 'no', 'logout', 'login']):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""Extract or infer the exact email address from the user's spoken or typed text.
Text: "{raw}"
User Full Name (if known): "{user_name}"

Rules:
- If the user spoke words like 'at', 'dot', 'gmail', 'at the rate', etc., convert to a valid email (e.g. 'user@gmail.com').
- If the user gave a handle or username for email, format it as a clean email ending in @gmail.com.
- Return ONLY the clean lowercase email address (e.g. 'pavan@gmail.com') or 'NONE' if no email is mentioned.
- Absolutely NO other text, NO quotes, NO markdown.
"""
            resp = model.generate_content(prompt, request_options={"timeout": 5})
            out = resp.text.strip().lower()
            m_ai = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', out)
            if m_ai:
                return m_ai.group(0).lower()
        except Exception:
            pass

    return None

def get_next_registration_prompt(reg_flow, effective_lang, acknowledged_msg=""):
    reg_flow = reg_flow or {}
    name = reg_flow.get('name')
    email = reg_flow.get('email')
    phone = reg_flow.get('phone')
    aadhaar = reg_flow.get('aadhaar')
    photo = reg_flow.get('photo')
    id_proof = reg_flow.get('id_proof')
    password = reg_flow.get('password')

    prefix = (acknowledged_msg + " ") if acknowledged_msg else ""

    if not name:
        if effective_lang == "Kannada":
            return prefix + "ಪ್ರಾರಂಭಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ.", 'name'
        else:
            return prefix + "Please tell me your full name to start.", 'name'

    if not email:
        if effective_lang == "Kannada":
            return prefix + "ಮುಂದಿನ ಹಂತ, ಅಧಿಸೂಚನೆಗಳಿಗಾಗಿ ನಿಮ್ಮ ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ಹೇಳಿ.", 'email'
        else:
            return prefix + "Next, please tell me your email address for account notifications and updates.", 'email'

    if not phone:
        if effective_lang == "Kannada":
            return prefix + "ಮುಂದಿನ ಹಂತ, ದಯವಿಟ್ಟು ನಿಮ್ಮ 10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ಹೇಳಿ.", 'phone'
        else:
            return prefix + "Next, please tell me your 10-digit mobile number.", 'phone'

    if not aadhaar:
        if effective_lang == "Kannada":
            return prefix + "ಮುಂದಿನ ಹಂತ, ದಯವಿಟ್ಟು ನಿಮ್ಮ 12 ಅಂಕಿಗಳ ಆಧಾರ್ ಸಂಖ್ಯೆಯನ್ನು ಹೇಳಿ.", 'aadhaar'
        else:
            return prefix + "Next, please tell me your 12-digit Aadhaar number.", 'aadhaar'

    # If password is provided (or if all details are already filled), proceed directly to final confirmation!
    if password and name and email and phone and aadhaar:
        spoken_phone = format_text_for_speech(phone, effective_lang)
        spoken_aadhaar = format_text_for_speech(aadhaar, effective_lang)
        if effective_lang == "Kannada":
            return prefix + f"ಎಲ್ಲಾ ವಿವರಗಳು ಮತ್ತು ದಾಖಲೆಗಳು ಸಿದ್ಧವಾಗಿವೆ! ಹೆಸರು: {name}, ಇಮೇಲ್: {email}, ಮೊಬೈಲ್: {spoken_phone}, ಆಧಾರ್: {spoken_aadhaar}. ನೋಂದಣಿ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸಬೇಕೇ? 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ.", 'confirm'
        else:
            return prefix + f"All details and verification documents are ready! Name: {name}, Email: {email}, Mobile: {spoken_phone}, Aadhaar: {spoken_aadhaar}. Ready to submit your application? Say 'Yes' or 'Submit' to proceed.", 'confirm'

    if not photo:
        if effective_lang == "Kannada":
            return prefix + "ಈಗ ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಲು ಕ್ಯಾಮೆರಾ ತೆರೆಯುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಕ್ಯಾಮೆರಾ ನೋಡಿ 'ಕ್ಲಿಕ್ ಮಾಡಿ' ಎಂದು ಹೇಳಿ!", 'photo_camera'
        else:
            return prefix + "Now opening the camera to take your profile picture. Please look at the camera and say 'Click' when ready!", 'photo_camera'

    if not id_proof:
        if effective_lang == "Kannada":
            return prefix + "ಪ್ರೊಫೈಲ್ ಫೋಟೋ ಸೇರಿಸಲಾಗಿದೆ! ಈಗ ನಿಮ್ಮ ಗುರುತಿನ ಚೀಟಿ (ಆಧಾರ್ ಅಥವಾ ಪ್ಯಾನ್ ಕಾರ್ಡ್) ಕ್ಯಾಮೆರಾ ಮುಂದೆ ಹಿಡಿದು 'ಕ್ಲಿಕ್ ಮಾಡಿ' ಎಂದು ಹೇಳಿ.", 'idproof_camera'
        else:
            return prefix + "Profile photo saved! Now please hold your ID card (Aadhaar or PAN) in front of the camera and say 'Click' to scan it.", 'idproof_camera'

    if not password:
        if effective_lang == "Kannada":
            return prefix + "ಗುರುತಿನ ದಾಖಲೆ ಉಳಿಸಲಾಗಿದೆ! ಕೊನೆಯ ಹಂತ, ದಯವಿಟ್ಟು ನಿಮ್ಮ ಖಾತೆಗೆ ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಪಿನ್ ರಚಿಸಿ ಹೇಳಿ.", 'password'
        else:
            return prefix + "ID document saved! Final step, please create a password or PIN for your account.", 'password'

    # All fields and documents collected -> Ready for Zero-Click Submission!
    spoken_phone = format_text_for_speech(phone, effective_lang)
    spoken_aadhaar = format_text_for_speech(aadhaar, effective_lang)
    if effective_lang == "Kannada":
        return prefix + f"ಎಲ್ಲಾ ವಿವರಗಳು ಮತ್ತು ದಾಖಲೆಗಳು ಸಿದ್ಧವಾಗಿವೆ! ಹೆಸರು: {name}, ಇಮೇಲ್: {email}, ಮೊಬೈಲ್: {spoken_phone}, ಆಧಾರ್: {spoken_aadhaar}. ನೋಂದಣಿ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸಬೇಕೇ? 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ.", 'confirm'
    else:
        return prefix + f"All details and verification documents are ready! Name: {name}, Email: {email}, Mobile: {spoken_phone}, Aadhaar: {spoken_aadhaar}. Ready to submit your application? Say 'Yes' or 'Submit' to proceed.", 'confirm'


def get_next_kyc_prompt(kyc_flow, effective_lang, acknowledged_msg=""):
    """
    Determines the next missing field in the step-by-step KYC wizard:
    1. Full Name ('name')
    2. Date of Birth ('dob')
    3. Aadhaar Number ('aadhaar' - 12 digits)
    4. Step 1 Complete -> Prompt to generate OTP ('generate_otp')
    5. Step 2 Complete -> Prompt to verify OTP ('verify_otp')
    Returns (reply_message, next_field_key).
    """
    kyc_flow = kyc_flow or {}
    name = kyc_flow.get('name')
    dob = kyc_flow.get('dob')
    aadhaar = kyc_flow.get('aadhaar')
    step = kyc_flow.get('step', 1)

    prefix = (acknowledged_msg + " ") if acknowledged_msg else ""

    if step == 2:
        if effective_lang == "Kannada":
            return prefix + "ನಿಮ್ಮ ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗೆ ಆಧಾರ್ ಒಟಿಪಿ ಕಳುಹಿಸಲಾಗಿದೆ ಮತ್ತು ನಮೂದಿಸಲಾಗಿದೆ. ಒಟಿಪಿ ಪರಿಶೀಲಿಸಲು ಸಿದ್ಧವೇ? 'ಪರಿಶೀಲಿಸಿ' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ.", 'verify_otp'
        else:
            return prefix + "Aadhaar OTP has been sent to your registered mobile number and entered. Ready to verify OTP? Say 'Verify OTP' or 'Submit' to proceed.", 'verify_otp'

    if not name:
        if effective_lang == "Kannada":
            return prefix + "ಕೆವೈಸಿ ಪ್ರಾರಂಭಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ.", 'name'
        else:
            return prefix + "Please tell me your full name to start KYC.", 'name'

    if not dob:
        if effective_lang == "Kannada":
            return prefix + "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹುಟ್ಟಿದ ದಿನಾಂಕವನ್ನು ಹೇಳಿ (ಉದಾಹರಣೆಗೆ 15-05-1995).", 'dob'
        else:
            return prefix + "Please provide your Date of Birth (e.g., 15th May 1995) to proceed.", 'dob'

    if not aadhaar:
        if effective_lang == "Kannada":
            return prefix + "ದಯವಿಟ್ಟು ನಿಮ್ಮ 12 ಅಂಕಿಯ ಆಧಾರ್ ಸಂಖ್ಯೆಯನ್ನು ಹೇಳಿ.", 'aadhaar'
        else:
            return prefix + "Please provide your 12-digit Aadhaar number to proceed.", 'aadhaar'

    # All 3 Step 1 fields are filled
    spoken_aadhaar = format_text_for_speech(aadhaar, effective_lang)
    if effective_lang == "Kannada":
        summary = f"ಎಲ್ಲಾ ಕೆವೈಸಿ ವಿವರಗಳು ಸಿದ್ಧವಾಗಿವೆ! ಹೆಸರು: {name}, ಹುಟ್ಟಿದ ದಿನಾಂಕ: {dob}, ಆಧಾರ್: {spoken_aadhaar}."
        return prefix + f"{summary} ಒಟಿಪಿ ರಚಿಸಲು ಸಿದ್ಧವೇ? ಮುಂದುವರಿಯಲು 'ಒಟಿಪಿ ರಚಿಸಿ' ಅಥವಾ 'ಹೌದು' ಎಂದು ಹೇಳಿ.", 'generate_otp'
    else:
        summary = f"All KYC details are ready! Name: {name}, DOB: {dob}, Aadhaar: {spoken_aadhaar}."
        return prefix + f"{summary} Ready to generate OTP? Say 'Generate OTP' or 'Yes' to proceed.", 'generate_otp'


TRANSLATIONS = {
    'English': {
        'greeting': 'Hello! I am your SIRI BANK AI Voice Assistant. How can I help you today? You can ask for balance, transfer money, request an ATM card, or register a new account.',
        'balance_inquiry': 'Your current account balance for account {} is {} rupees.',
        'request_card_success': 'Your request for a new ATM Debit Card has been submitted.',
        'request_aadhaar_success': 'Your request to link Aadhaar has been submitted.',
        'usage_guidance': "SIRI BANK Voice Guide: You can speak naturally in English or Kannada. Say 'check balance', 'send 500 to 9876543210', 'open ATM services', or 'register new account'.",
        'not_understood': 'I did not catch that. You can say "check balance", "transfer money", "register account", or "open KYC".',
        'please_wait': 'Processing your request...',
        'fill_pay_phone_success': 'I have prepared a transfer of ₹{} to phone number {}. Ready to submit? Say "Yes" or "Submit" to proceed.',
        'fill_pay_acc_success': 'I have prepared a transfer of ₹{} to account number {}. Ready to submit? Say "Yes" or "Submit" to proceed.',
        'fill_kyc_success': 'I have filled your KYC details: Name {}, DOB {}, Aadhaar number {}. Ready to submit and simulate OTP? Say "Yes" or "Submit" to proceed.',
        'fill_name_success': 'I have filled your name as {}. Please provide your Date of Birth and Aadhaar number to proceed.',
        'fill_register_success': 'I have filled your registration details: Name {}, Phone {}, Aadhaar {}. Ready to submit? Say "Yes" or "Submit" to proceed.',
        'confirm_submit_success': 'Submitting your details now.',
        'cancel_submit_success': 'Submission cancelled. How else can I help you?',
        'verify_otp_success': 'Simulating and verifying your KYC OTP now.',
        'nav_success': 'Navigating to the {} page.',
        'read_screen_prompt': 'Reading screen content for you.'
    },
    'Kannada': {
        'greeting': 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ SIRI BANK AI ಧ್ವನಿ ಸಹಾಯಕ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ? ಬ್ಯಾಲೆನ್ಸ್ ಪರಿಶೀಲನೆ, ಹಣ ವರ್ಗಾವಣೆ, ಎಟಿಎಂ ಕಾರ್ಡ್ ಅಥವಾ ಹೊಸ ಖಾತೆ ನೋಂದಣಿಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.',
        'balance_inquiry': 'ಖಾತೆ {} ಗಾಗಿ ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಬ್ಯಾಲೆನ್ಸ್ ₹{}.',
        'request_card_success': 'ಹೊಸ ಎಟಿಎಂ ಕಾರ್ಡ್ ವಿನಂತಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ.',
        'request_aadhaar_success': 'ಆಧಾರ್ ಲಿಂಕ್ ಮಾಡುವ ವಿನಂತಿಯನ್ನು ಸಲ್ಲಿಸಲಾಗಿದೆ.',
        'usage_guidance': "ಸಿರಿ ಬ್ಯಾಂಕ್ ಧ್ವನಿ ಮಾರ್ಗದರ್ಶಿ: ನೀವು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಬಹುದು. 'ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು', '500 ರೂಪಾಯಿ ಕಳುಹಿಸಿ', ಅಥವಾ 'ಹೊಸ ಖಾತೆ ತೆರೆಯಿರಿ' ಎಂದು ಹೇಳಿ.",
        'not_understood': 'ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ನೀವು "ಬ್ಯಾಲೆನ್ಸ್ ಪರಿಶೀಲಿಸಿ", "ಹಣ ಕಳುಹಿಸಿ", ಅಥವಾ "ಹೊಸ ಖಾತೆ ತೆರೆಯಿರಿ" ಎಂದು ಹೇಳಬಹುದು.',
        'please_wait': 'ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ...',
        'fill_pay_phone_success': 'ನಾನು ಮೊಬೈಲ್ ಸಂಖ್ಯೆ {} ಗೆ ₹{} ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು "ಹೌದು" ಅಥವಾ "ಸಲ್ಲಿಸಿ" ಎಂದು ಹೇಳಿ.',
        'fill_pay_acc_success': 'ನಾನು ಖಾತೆ ಸಂಖ್ಯೆ {} ಗೆ ₹{} ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು "ಹೌದು" ಅಥವಾ "ಸಲ್ಲಿಸಿ" ಎಂದು ಹೇಳಿ.',
        'fill_kyc_success': 'ನಾನು ನಿಮ್ಮ ಕೆವೈಸಿ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿದ್ದೇನೆ: ಹೆಸರು {}, ಜನ್ಮ ದಿನಾಂಕ {}, ಆಧಾರ್ {}. ಒಟಿಪಿ ಸಿಮ್ಯುಲೇಟ್ ಮಾಡಲು "ಹೌದು" ಅಥವಾ "ಸಲ್ಲಿಸಿ" ಎಂದು ಹೇಳಿ.',
        'fill_name_success': 'ನಾನು ನಿಮ್ಮ ಹೆಸರನ್ನು {} ಎಂದು ಭರ್ತಿ ಮಾಡಿದ್ದೇನೆ. ಮುಂದುವರಿಯಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜನ್ಮ ದಿನಾಂಕ ಮತ್ತು ಆಧಾರ್ ಸಂಖ್ಯೆಯನ್ನು ಹೇಳಿ.',
        'fill_register_success': 'ನಾನು ನಿಮ್ಮ ನೋಂದಣಿ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿದ್ದೇನೆ: ಹೆಸರು {}, ಫೋನ್ {}, ಆಧಾರ್ {}. ಸಲ್ಲಿಸಲು "ಹೌದು" ಅಥವಾ "ಸಲ್ಲಿಸಿ" ಎಂದು ಹೇಳಿ.',
        'confirm_submit_success': 'ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ.',
        'cancel_submit_success': 'ವಿನಂತಿಯನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ.',
        'verify_otp_success': 'ನಿಮ್ಮ ಕೆವೈಸಿ ಒಟಿಪಿಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ.',
        'nav_success': '{} ವಿಭಾಗಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ.',
        'read_screen_prompt': 'ಪರದೆಯ ಮಾಹಿತಿಯನ್ನು ಓದಲಾಗುತ್ತಿದೆ.'
    }
}

def get_translation(lang, key):
    if lang not in TRANSLATIONS:
        lang = 'Kannada'
    return TRANSLATIONS[lang].get(key, TRANSLATIONS['Kannada'].get(key, ''))

def detect_user_language(text):
    if not text:
        return 'Kannada'
    # 0. Check explicit language switch keywords first
    if 'ಇಂಗ್ಲೀಷ್' in text or 'ಇಂಗ್ಲಿಷ್' in text or re.search(r'\benglish\b', text, re.IGNORECASE):
        return 'English'
    if 'ಕನ್ನಡ' in text or re.search(r'\b(kannada|kannadadalli)\b', text, re.IGNORECASE):
        return 'Kannada'

    # 1. Check for Kannada Unicode script (0x0C80 to 0x0CFF)
    if re.search(r'[ಀ-೿]', text):
        return 'Kannada'
    
    # 2. Check for common Kannada transliterated words (Latin script)
    kannada_translit = [
        r'\bnamaskar[a-z]*\b', r'\bnamaste\b', r'\beshtu\b', r'\bhana\b', r'\bkodi\b',
        r'\byaru\b', r'\bnanna\b', r'\bkhate\b', r'\benu\b', r'\bhege\b', r'\bmadali\b',
        r'\bkannada\b', r'\bhelu\b', r'\billi\b', r'\belli\b', r'\bkodbeku\b',
        r'\bkalisbeku\b', r'\bbeku\b', r'\bhosa\b', r'\bthago\b', r'\bhogi\b',
        r'\bmatte\b', r'\billa\b', r'\bide\b', r'\bidhe\b', r'\bdayavittu\b'
    ]
    lower = text.lower()
    for pat in kannada_translit:
        if re.search(pat, lower):
            return 'Kannada'
            
    # 3. Check for obvious English keywords
    english_words = [
        r'\bwhat\b', r'\bhow\b', r'\bcan\b', r'\bis\b', r'\bmy\b', r'\bbalance\b',
        r'\btransfer\b', r'\bsend\b', r'\bmoney\b', r'\bregister\b', r'\bhelp\b',
        r'\bhi\b', r'\bhello\b', r'\bcard\b', r'\bhistory\b', r'\bloan\b',
        r'\bprofile\b', r'\bopen\b', r'\bshow\b', r'\bplease\b', r'\baccount\b',
        r'\benglish\b', r'\bthank\b', r'\bthanks\b', r'\bcheck\b', r'\bview\b'
    ]
    for pat in english_words:
        if re.search(pat, lower):
            return 'English'
            
    return None

def format_text_for_speech(text, lang="Kannada"):
    """
    Transforms text so that TTS voice engines pronounce it with maximum clarity and naturalness:
    - Account numbers (ACC80001, 80001, etc.), phone numbers, Aadhaar, OTPs are read DIGIT BY DIGIT (1, 2, 3...)
    - Currency amounts (₹15,000, 500 rupees, etc.) are read in natural words (thousands, hundreds, rupees)
    """
    if not text:
        return ""

    clean = re.sub(r'<[^>]*>', ' ', str(text))
    is_kn = (lang == "Kannada")

    # 1. Format Account Numbers: e.g. ACC80001 or Account ACC80001 -> spaced digits
    def format_acc(m):
        prefix = m.group(1) or ""
        digits = m.group(2)
        spaced_digits = ", ".join(list(digits))
        if is_kn:
            prefix_kn = "ಎ ಸಿ ಸಿ, " if "ACC" in prefix.upper() else (prefix + " ")
            return f"{prefix_kn}{spaced_digits}"
        else:
            prefix_en = "A C C, " if "ACC" in prefix.upper() else (prefix + " ")
            return f"{prefix_en}{spaced_digits}"

    clean = re.sub(r'\b(ACC|acc)\s*(\d{4,8})\b', format_acc, clean)
    clean = re.sub(r'\b(account\s+(?:number\s+|no\.?\s*)?|ಖಾತೆ\s+(?:ಸಂಖ್ಯೆ\s+)?|ಖಾತೆ\s+)(\d{4,8})\b', format_acc, clean, flags=re.IGNORECASE)

    # 2. Format 10-digit Phone Numbers to digit-by-digit
    def format_phone(m):
        digits = m.group(1)
        return f"{', '.join(digits[:5])}, {', '.join(digits[5:])}"
    clean = re.sub(r'\b([6-9]\d{9})\b', format_phone, clean)

    # 3. Format 12-digit Aadhaar Numbers to digit-by-digit
    def format_aadhaar(m):
        digits = m.group(1)
        return f"{', '.join(digits[:4])}, {', '.join(digits[4:8])}, {', '.join(digits[8:])}"
    clean = re.sub(r'\b(\d{12})\b', format_aadhaar, clean)

    # 4. Format Currency Amounts (thousands, hundreds, rupees)
    def format_amount(m):
        amt_str = m.group(1).replace(',', '')
        try:
            val = float(amt_str)
            int_part = int(val)
            dec_part = int(round((val - int_part) * 100))
            if is_kn:
                if int_part >= 100000:
                    lakhs = int_part // 100000
                    rem = int_part % 100000
                    words = f"{lakhs} ಲಕ್ಷ"
                    if rem >= 1000:
                        words += f" {rem // 1000} ಸಾವಿರ"
                    if rem % 1000 > 0:
                        words += f" {rem % 1000}"
                    words += " ರೂಪಾಯಿ"
                elif int_part >= 1000:
                    thousands = int_part // 1000
                    hundreds = int_part % 1000
                    words = f"{thousands} ಸಾವಿರ"
                    if hundreds > 0:
                        words += f"ದ {hundreds}"
                    words += " ರೂಪಾಯಿ"
                elif int_part >= 100:
                    hundreds = int_part // 100
                    rem = int_part % 100
                    words = f"{hundreds} ನೂರು"
                    if rem > 0:
                        words += f" {rem}"
                    words += " ರೂಪಾಯಿ"
                else:
                    words = f"{int_part} ರೂಪಾಯಿ"
                if dec_part > 0:
                    words += f" {dec_part} ಪೈಸೆ"
                return words
            else:
                if int_part >= 100000:
                    lakhs = int_part // 100000
                    rem = int_part % 100000
                    words = f"{lakhs} lakh"
                    if rem >= 1000:
                        words += f" {rem // 1000} thousand"
                    if rem % 1000 > 0:
                        words += f" {rem % 1000}"
                    words += " rupees"
                elif int_part >= 1000:
                    thousands = int_part // 1000
                    hundreds = int_part % 1000
                    words = f"{thousands} thousand"
                    if hundreds > 0:
                        words += f" {hundreds}"
                    words += " rupees"
                elif int_part >= 100:
                    hundreds = int_part // 100
                    rem = int_part % 100
                    words = f"{hundreds} hundred"
                    if rem > 0:
                        words += f" {rem}"
                    words += " rupees"
                else:
                    words = f"{int_part} rupees"
                if dec_part > 0:
                    words += f" and {dec_part} paise"
                return words
        except Exception:
            return m.group(0)

    clean = re.sub(r'(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*(?:\.\d{1,2})?)', format_amount, clean, flags=re.IGNORECASE)
    # 5. Ensure isolated '0' in digit sequences is pronounced as 'zero' or 'ಸೊನ್ನೆ'
    zero_word = 'ಸೊನ್ನೆ' if is_kn else 'zero'
    clean = re.sub(r'(?<=[,\s(])0(?=[,\s)]|$)', zero_word, clean)
    clean = re.sub(r'\b0\b', zero_word, clean)
    return clean.strip()

def call_gemini_conversational_ai(text, user_state, language="Kannada", conversation_history=None):
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json", "max_output_tokens": 600}
        )

        is_logged_in = bool(user_state.get('account_number') or (user_state.get('user_name') and not user_state.get('is_visitor')))
        user_name = user_state.get('user_name', 'Customer')
        account_num = user_state.get('account_number', 'ACC80001')
        balance = user_state.get('balance', '0.00')
        current_page = user_state.get('current_page', '')
        current_tab = user_state.get('current_tab', '')
        if is_logged_in and (current_tab in ['login', 'register'] or not current_tab):
            current_tab = 'kyc' if 'kyc' in current_page else ('pay' if 'pay' in current_page else ('atm' if 'atm' in current_page else ('history' if 'history' in current_page else 'dashboard')))

        auto_lang = detect_user_language(text)
        if auto_lang:
            effective_lang = auto_lang
        else:
            has_kannada_script = bool(re.search(r'[ಀ-೿]', text))
            effective_lang = "Kannada" if (language == "Kannada" or has_kannada_script) else "English"

        history_context = ""
        if conversation_history and isinstance(conversation_history, list):
            history_lines = []
            for item in conversation_history[-6:]:
                role = "Customer" if item.get('role') == 'user' else "SIRI AI"
                content = item.get('content', '')
                if content:
                    history_lines.append(f"{role}: {content}")
            if history_lines:
                history_context = "\nRECENT CONVERSATION MEMORY (Use this to remember past context, names, previous questions):\n" + "\n".join(history_lines) + "\n"

        logged_in_rule = ""
        if is_logged_in:
            logged_in_rule = f"- CRITICAL: The user is currently LOGGED IN as {user_name}. Under NO circumstances ask them to log in, provide their password, or provide mobile number to sign in."

        kyc_status = user_state.get('kyc_status')
        kyc_rejection_reason = user_state.get('kyc_rejection_reason')

        system_prompt = f"""
You are SIRI BANK's single, intelligent, empathetic AI Voice & Banking Assistant with continuous memory across all banking services.
You natively speak and understand ONLY two languages: Kannada (ಕನ್ನಡ) and English.
NEVER, UNDER ANY CIRCUMSTANCES, USE HINDI OR DEVNAGARI SCRIPT. NO HINDI WORDS ALLOWED.

Target Language: {effective_lang}
User Logged-in Status: {'Logged In as ' + user_name if is_logged_in else 'Visitor / Unauthenticated'}
Current Page: {current_page or ('/home' if is_logged_in else '/login')}
Active Form Tab: {current_tab or ('dashboard' if is_logged_in else 'login')}
User Account Context: Account Number: {account_num}, Balance: ₹{balance}, KYC Status: {kyc_status or 'None'}, Administrator Rejection Reason: {kyc_rejection_reason or 'None'}
{history_context}
Current User Spoken or Typed Message: "{text}"

YOUR MISSION & CONVERSATIONAL RULES:
{logged_in_rule}
- REJECTION REASON INTEGRITY: If the user asks why their KYC was rejected or what the admin said, you MUST state the exact administrator rejection reason: "{kyc_rejection_reason}". Do NOT make up any reason.
- SIRI BANK PRODUCT & SERVICE FACTS:
  * Fixed Deposit (FD): Triple Delight FD offers 7.85% p.a. standard rate, 8.35% p.a. (+0.50%) for Senior Citizens. Zero penalty on premature withdrawals for medical emergencies.
  * Kisan Agri Loans: Subsidized 4.00% p.a. interest rate for Karnataka farmers, zero paperwork, direct DBT subsidy linkage, and flexible harvest repayments.
  * RuPay Platinum Debit Card: ₹0 fee (Free for Year 1), 2x reward points on UPI payments, free domestic airport lounge access, 1-click voice freeze.
  * Account Opening: 100% paperless e-KYC in 2 minutes, ₹0 minimum balance, guided voice registration.
  * Smart Home Loans: 8.25% p.a., zero processing fees for women co-applicants.

1. AUTOMATIC LANGUAGE ADAPTATION & STRICT MONOLINGUAL RESPONSE:
   - CRITICAL: NEVER MIX LANGUAGES IN THE SAME RESPONSE!
   - If Target Language is English: Respond 100% in pure, fluent English. Do NOT include any Kannada script or words.
   - If Target Language is Kannada: Respond 100% in authentic, pure Kannada script (ಕನ್ನಡ). Do NOT include English translation words in parentheses.
   - ZERO HINDI! Absolutely never use Hindi words or Devanagari script.

2. NATURAL VOICE PRONUNCIATION (CRITICAL FOR ACCESSIBILITY):
   - For Account Numbers, Phone Numbers, Aadhaar Numbers, Customer IDs, and OTPs: ALWAYS spell out the digit 0 as 'zero' in English (or 'ಸೊನ್ನೆ' in Kannada) separated by commas. NEVER write or pronounce digit '0' as letter 'o'!
   - For Currency Amounts (e.g. ₹15,000 or ₹42,023): ALWAYS express amounts in natural words using thousands, hundreds, and rupees.

3. CONVERSATION MEMORY:
   - Maintain context from recent dialogue history.

4. USER CONFIRMATION & AUTOMATIC FORM SUBMISSION:
   - When pre-filling forms, summarize values and ask: "Ready to submit? Say 'Yes' or 'Submit' to proceed."
   - When user confirms ("yes", "submit", "login", etc.): set `intent: "CONFIRM_SUBMIT"`, `action: "SUBMIT_FORM"`.

RETURN ONLY A VALID JSON OBJECT IN THIS FORMAT:
{{
  "intent": "GENERAL_CHAT" | "BALANCE_INQUIRY" | "VOICE_FILL_PAY_PHONE" | "VOICE_FILL_PAY_ACC" | "VOICE_FILL_KYC" | "REGISTER_ASSIST" | "NAVIGATE" | "READ_SCREEN" | "ATM_CARD_REQUEST" | "LOGOUT" | "SWITCH_AUTH_MODE" | "CONFIRM_SUBMIT" | "VOICE_FILL_LOGIN" | "KYC_VERIFY_OTP",
  "reply": "<natural conversational speech strictly in {effective_lang} script>",
  "action": "FILL_FORM" | "FILL_REGISTER" | "SUBMIT_FORM" | "READ_SCREEN" | "SPEAK_BALANCE" | "NAVIGATE" | "CREATE_REQUEST_ATM" | "LOGOUT" | "SWITCH_AUTH_MODE" | "VERIFY_KYC_OTP" | null,
  "target_form": "register" | "login" | "pay-phone" | "pay-acc" | "kyc" | "kyc-otp" | null,
  "fields": {{
    "name": "<name if mentioned, else null>",
    "email": "<valid email address e.g. user@gmail.com if mentioned or spoken, else null>",
    "phone": "<10-digit phone if mentioned, else null>",
    "aadhaar": "<12-digit aadhaar if mentioned, else null>",
    "password": "<password/PIN if mentioned, else null>",
    "identifier": "<login phone or aadhaar if mentioned, else null>",
    "dob": "<YYYY-MM-DD if mentioned, else null>",
    "amount": "<numeric amount if mentioned, else null>",
    "account": "<account number if mentioned, else null>"
  }},
  "redirect": "/home" | "/pay" | "/atm-services" | "/aadhaar-kyc" | "/request-history" | "/profile" | "/login" | "/register" | null
}}
"""
        response = model.generate_content(system_prompt, request_options={"timeout": 15})
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)

        # Robust JSON extraction
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            candidate_json = json_match.group(0)
            candidate_json = re.sub(r',\s*([\}\]])', r'\1', candidate_json)
            try:
                parsed_json = json.loads(candidate_json)
                if 'fields' in parsed_json and isinstance(parsed_json['fields'], dict):
                    parsed_json['fields'] = {k: v for k, v in parsed_json['fields'].items() if v is not None}
                return parsed_json
            except Exception:
                pass

        try:
            parsed_json = json.loads(raw_text)
            if 'fields' in parsed_json and isinstance(parsed_json['fields'], dict):
                parsed_json['fields'] = {k: v for k, v in parsed_json['fields'].items() if v is not None}
            return parsed_json
        except Exception:
            clean_reply = re.sub(r'[{}\[\]"]', '', raw_text).strip()
            if clean_reply and len(clean_reply) > 10:
                return {'intent': 'GENERAL_CHAT', 'reply': clean_reply, 'action': None}
            return None
    except Exception as e:
        print("Gemini Conversational API Notice (falling back to localized engine):", e)
        return None

def process_chat_intent(text, user_state, language="Kannada", conversation_history=None):
    text_clean = (text or '').strip()
    text_lower = text_clean.lower()
    auto_lang = detect_user_language(text_clean)
    if auto_lang:
        effective_lang = auto_lang
    else:
        has_kannada_script = bool(re.search(r'[ಀ-೿]', text_clean))
        effective_lang = "Kannada" if (language == "Kannada" or has_kannada_script) else "English"

    is_visitor = not bool(user_state.get('account_number') or (user_state.get('user_name') and not user_state.get('is_visitor')))
    current_page = user_state.get('current_page', '')
    current_tab = user_state.get('current_tab', '')
    last_bot_msg = (user_state.get('last_bot_message') or '').strip().lower()
    if not last_bot_msg and conversation_history:
        for turn in reversed(conversation_history):
            if isinstance(turn, dict) and (turn.get('role') == 'assistant' or turn.get('sender') in ['assistant', 'bot']):
                last_bot_msg = (turn.get('content') or turn.get('text') or '').strip().lower()
                break
    bot_asked_phone = bool(re.search(r'\b(?:10-digit|tell\s+me|provide|enter)?\s*(?:your\s+)?(?:mobile|phone|contact|ಮೊಬೈಲ್|ಫೋನ್)\b', last_bot_msg) and not any(w in last_bot_msg for w in ['noted your mobile', 'entered your mobile', 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಲಾಗಿದೆ', 'aadhaar', 'password', 'pin']))
    bot_asked_name = bool(re.search(r'\b(?:tell\s+me|what\s+is|provide|enter|ದಯವಿಟ್ಟು)?\s*(?:your\s+)?(?:full\s+name|name\s+to\s+start|name\s+to\s+proceed|ಪೂರ್ಣ\s*ಹೆಸರು|ಹೆಸರು\s*ಹೇಳಿ)\b', last_bot_msg) and not any(w in last_bot_msg for w in ['noted your name', 'entered your name', 'ಹೆಸರು ನಮೂದಿಸಲಾಗಿದೆ', 'mobile', 'phone', 'aadhaar', 'password', 'pin']))
    bot_asked_pwd = bool(any(w in last_bot_msg for w in ['provide your password', 'enter your password', 'tell me your password', 'password to sign in', 'password to log in', 'create a password', '4-digit password', '4-digit pin', 'ಪಾಸ್‌ವರ್ಡ್', 'ಪಿನ್']))
    bot_asked_confirmation = bool(re.search(r"\b(ready\s+to\s+log\s*in|ready\s+to\s+submit|ready\s+to\s+proceed|say\s+['\"]?yes['\"]?|say\s+['\"]?login['\"]?|say\s+['\"]?submit['\"]?|is\s+that\s+correct|ಸಿದ್ಧವೇ|ಹೌದು\s+ಅಥವಾ\s+ಲಾಗಿನ್|ಹೌದು\s+ಅಥವಾ\s+ಸಲ್ಲಿಸಿ)\b", last_bot_msg))

    reg_flow = user_state.get('reg_flow', {}).copy() if isinstance(user_state.get('reg_flow'), dict) else {}
    kyc_flow = user_state.get('kyc_flow', {}).copy() if isinstance(user_state.get('kyc_flow'), dict) else {}

    # Explicit Language Switch Request
    if re.search(r'\b(kannada|ಕನ್ನಡ|kannadadalli)\b', text_lower) or re.search(r'(ಕನ್ನಡದಲ್ಲಿ\s*ಮಾತನಾಡಿ|ಕನ್ನಡಕ್ಕೆ\s*ಬದಲಾಯಿಸಿ|ಕನ್ನಡ\s*ಮಾತನಾಡಿ|ಕನ್ನಡ\s*ಭಾಷೆ)', text_clean):
        return {
            'intent': 'LANGUAGE_SWITCH',
            'reply': 'ಖಂಡಿತ! ನಾನು ಇನ್ನು ಮುಂದೆ ನಿಮ್ಮೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲೇ ಮಾತನಾಡುತ್ತೇನೆ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?',
            'action': None,
            'switch_language': 'Kannada'
        }
    elif 'ಇಂಗ್ಲೀಷ್' in text_clean or re.search(r'ಇಂಗ್ಲೀಷ್‌ನಲ್ಲಿ\s*ಮಾತನಾಡಿ|ಇಂಗ್ಲೀಷ್‌ಗೆ\s*ಬದಲಾಯಿಸಿ', text_clean):
        return {
            'intent': 'LANGUAGE_SWITCH',
            'reply': "Okay, I've switched our conversation to English. How may I assist you today?",
            'action': None,
            'switch_language': 'English'
        }
    elif re.search(r'\b(english|ಇಂಗ್ಲಿಷ್)\b', text_lower) or 'ಇಂಗ್ಲಿಷ್' in text_clean or re.search(r'(ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ\s*ಮಾತನಾಡಿ|ಇಂಗ್ಲಿಷ್‌ಗೆ\s*ಬದಲಾಯಿಸಿ|speak\s+in\s+english|switch\s+to\s+english)', text_clean, re.IGNORECASE):
        return {
            'intent': 'LANGUAGE_SWITCH',
            'reply': "Okay, I've switched to English. How can I help you today?",
            'action': None,
            'switch_language': 'English'
        }

    # High-Priority Intercept: Explicit Registration Reset / Cancel / Start Over
    is_reset_reg = bool(
        re.search(r'\b(?:start\s+over|start\s+fresh|reset|clear|restart)\s*(?:registration|register|form|details)?\b', text_lower) or
        re.search(r'\b(?:reset\s+registration|clear\s+registration|restart\s+registration|cancel\s+registration)\b', text_lower) or
        re.search(r'(ನೋಂದಣಿ\s*ರದ್ದು|ನೋಂದಣಿ\s*ಮರುಹೊಂದಿಸಿ|ಹೊಸದಾಗಿ\s*ಪ್ರಾರಂಭಿಸಿ|ವಿವರಗಳನ್ನು\s*ಅಳಿಸಿ)', text_clean)
    ) and (is_visitor or current_tab == 'register') and not re.search(r'\b(?:transfer|balance|loan|pay)\b', text_lower)
    if is_reset_reg:
        reply_msg = "ನೋಂದಣಿ ವಿವರಗಳನ್ನು ಮರುಹೊಂದಿಸಲಾಗಿದೆ. ಹೊಸದಾಗಿ ಪ್ರಾರಂಭಿಸೋಣ! ಪ್ರಾರಂಭಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ." if effective_lang == "Kannada" else "Registration has been reset. Let's start fresh! Please tell me your full name to start."
        return {
            'intent': 'RESET_REGISTRATION',
            'reply': reply_msg,
            'action': 'FILL_REGISTER',
            'mode': 'register',
            'target_form': 'register',
            'fields': {'name': '', 'email': '', 'phone': '', 'aadhaar': '', 'password': ''},
            'reg_flow': {},
            'switch_language': effective_lang
        }

    # High-Priority Intercept: Live Camera Opening / Capture Photo by Voice
    is_cam_open_intent = bool(
        re.search(r'\b(?:open|start|show|turn\s*on)\s*(?:the\s+)?(?:camera|webcam|photo\s*capture|selfie)\b', text_lower) or
        re.search(r'\b(?:take|click|capture)\s*(?:a\s+)?(?:photo|picture|image|selfie|id|id\s*card)\b', text_lower) or
        re.search(r'(ಕ್ಯಾಮೆರಾ\s*ತೆರೆ|ಕ್ಯಾಮೆರಾ\s*ಆನ್\s*ಮಾಡಿ|ಫೋಟೋ\s*ತೆಗೆ|ಫೋಟೋ\s*ತೆಗೆಯಿರಿ|ಸೆಲ್ಫಿ\s*ತೆಗೆ|ಕ್ಲಿಕ್\s*ಮಾಡಿ)', text_clean)
    )
    if is_cam_open_intent:
        is_id_cam = bool(re.search(r'\b(?:id|card|proof|document|ಗುರುತಿನ\s*ಚೀಟಿ|ದಾಖಲೆ)\b', text_lower))
        target_cam = 'idproof' if is_id_cam else 'photo'
        reply_msg = ("ಗುರುತಿನ ಚೀಟಿ ಸ್ಕ್ಯಾನ್ ಮಾಡಲು ಕ್ಯಾಮೆರಾ ತೆರೆಯಲಾಗಿದೆ. ಕಾರ್ಡ್ ತೋರಿಸಿ 'ಕ್ಲಿಕ್ ಮಾಡಿ' ಎಂದು ಹೇಳಿ." if target_cam == 'idproof' else "ಕ್ಯಾಮೆರಾ ತೆರೆಯಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಕ್ಯಾಮೆರಾ ನೋಡಿ ಸಿದ್ಧರಾದಾಗ 'ಕ್ಲಿಕ್ ಮಾಡಿ' ಎಂದು ಹೇಳಿ ಅಥವಾ ಬಟನ್ ಒತ್ತಿರಿ.") if effective_lang == "Kannada" else (
            "Opening camera to scan your ID card. Hold your card and say 'Click' when ready!" if target_cam == 'idproof' else "Opening camera. Please look at the camera and say 'Click' or press the button when ready!"
        )
        return {
            'intent': 'OPEN_CAMERA',
            'reply': reply_msg,
            'action': 'OPEN_CAMERA',
            'camera_target': target_cam,
            'mode': 'register',
            'target_form': 'register',
            'switch_language': effective_lang
        }

    # High-Priority Intercept: Direct Navigation to Register or Login
    is_explicit_nav_reg = bool(
        is_visitor and (
            re.search(r'\b(?:open|go\s*to|navigate\s*to|show|i\s*want\s*to|how\s*to|please)?\s*(?:the\s+|an?\s+)?(?:register|registration|signup|sign\s*up|new\s*account|open\s*(?:new\s*)?account|create\s*(?:new\s*)?account)\b', text_lower) or 
            re.search(r'(ನೋಂದಣಿ|ಹೊಸ\s*ಖಾತೆ|ಖಾತೆ\s*ತೆರೆಯಿರಿ|ಖಾತೆ\s*ತೆರೆ|ಸೈನ್\s*ಅಪ್)', text_clean)
        )
    ) and not re.search(r'\b(?:login|log\s*in|sign\s*in|signin|balance|pay|transfer|atm|card|debit|credit|kyc)\b', text_lower)

    is_explicit_nav_login = bool(
        re.search(r'\b(?:open|go\s*to|navigate\s*to|show|i\s*want\s*to|please)?\s*(?:the\s+)?(?:login|log\s+in|sign\s+in|signin)\b', text_lower) or 
        re.search(r'(ಲಾಗಿನ್|ಪ್ರವೇಶ|ಸೈನ್\s*ಇನ್)', text_clean)
    ) and not re.search(r'\b(?:register|registration|signup|sign\s*up|balance|pay|transfer)\b', text_lower)
    if is_explicit_nav_reg:
        if all(reg_flow.get(k) for k in ['name', 'email', 'phone', 'aadhaar', 'password']):
            reg_flow = {}
        reply_msg, next_field = get_next_registration_prompt(
            reg_flow,
            effective_lang,
            acknowledged_msg="ಖಂಡಿತ! ಹೊಸ ಖಾತೆ ನೋಂದಣಿ ಫಾರ್ಮ್ ತೆರೆಯಲಾಗಿದೆ. ಹಂತ ಹಂತವಾಗಿ ನೋಂದಣಿ ಮಾಡೋಣ." if effective_lang == "Kannada" else "Opening the Registration form. Let's register your account step by step."
        )
        return {
            'intent': 'SWITCH_AUTH_MODE',
            'reply': reply_msg,
            'action': 'SWITCH_AUTH_MODE',
            'mode': 'register',
            'target_form': 'register',
            'reg_flow': reg_flow,
            'switch_language': effective_lang
        }

    if is_explicit_nav_login:
        if not is_visitor:
            user_name = user_state.get('user_name', 'Customer')
            reply_msg = f"ನೀವು ಈಗಾಗಲೇ {user_name} ಆಗಿ ಲಾಗಿನ್ ಆಗಿದ್ದೀರಿ." if effective_lang == "Kannada" else f"You are already logged in as {user_name}."
            return {'intent': 'ALREADY_LOGGED_IN', 'reply': reply_msg, 'action': None, 'switch_language': effective_lang}
        reply_msg = "ಖಂಡಿತ! ಲಾಗಿನ್ ಫಾರ್ಮ್ ತೆರೆಯಲಾಗಿದೆ. ಪ್ರವೇಶಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಆಧಾರ್ ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ಹೇಳಿ." if effective_lang == "Kannada" else "Opening the Login form. Please provide your mobile number or Aadhaar and password to sign in."
        return {'intent': 'SWITCH_AUTH_MODE', 'reply': reply_msg, 'action': 'SWITCH_AUTH_MODE', 'mode': 'login', 'target_form': 'login', 'switch_language': effective_lang}

    # ── Step-by-Step Registration Context Handler ──
    is_reg_context = bool(
        is_visitor and (
            current_tab == 'register' or
            bool(reg_flow.get('name') or reg_flow.get('email') or reg_flow.get('phone') or reg_flow.get('aadhaar')) or
            bot_asked_name or
            any(w in last_bot_msg for w in [
                'registration form', 'register your account', 'register your account step by step',
                'tell me your full name to start', 'tell me your email address', 'tell me your 10-digit mobile number',
                'tell me your 12-digit aadhaar number', 'create a password or pin for your account',
                'ready to submit registration', 'ನೋಂದಣಿ ಫಾರ್ಮ್', 'ಹಂತ ಹಂತವಾಗಿ ನೋಂದಣಿ', 'ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ',
                'ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ಹೇಳಿ', '10 ಅಂಕಿಗಳ ಮೊಬೈಲ್', '12 ಅಂಕಿಗಳ ಆಧಾರ್', 'ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಪಿನ್ ರಚಿಸಿ', 'ನೋಂದಣಿಯನ್ನು ಸಲ್ಲಿಸಬೇಕೇ'
            ])
        ) and not re.search(r'\b(open\s*login|switch\s*to\s*login|sign\s*in|ಲಾಗಿನ್\s*ಮಾಡಿ|ಲಾಗಿನ್\s*ತೆರೆಯಿರಿ)\b', text_lower)
    )

    if is_reg_context and text_clean and not re.search(r'\b(open\s*login|switch\s*to\s*login|login|log\s*in|sign\s*in|balance|pay|transfer|atm|kyc|logout|history|home|profile|cancel|stop|no|ಬೇಡ|ರದ್ದು)\b', text_lower):
        # Word-to-digit mapping for spoken single digits
        word_digit_map = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
            'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
        }
        # Convert spoken word-digits to actual digits
        converted_text = text_clean
        for word, digit in word_digit_map.items():
            converted_text = re.sub(r'\b' + re.escape(word) + r'\b', digit, converted_text, flags=re.IGNORECASE)

        # Strip spaces/dashes from digits for phone/aadhaar spoken with gaps (e.g. "8637 644 98518")
        digits_only = re.sub(r'[\s\-,]+', '', converted_text)
        is_all_digits = digits_only.isdigit() and len(digits_only) > 0

        # 1. Direct submission check if everything was already filled
        is_confirm_submit = bool(
            reg_flow.get('name') and reg_flow.get('phone') and reg_flow.get('aadhaar') and reg_flow.get('password') and
            re.search(r'\b(?:yes|submit|confirm|proceed|ok|send|apply|ಹೌದು|ಸಲ್ಲಿಸಿ|ಸರಿ|ಮುಂದುವರಿಸಿ|ಅರ್ಜಿ\s*ಸಲ್ಲಿಸಿ)\b', text_lower)
        )
        if is_confirm_submit:
            reply_msg = "ಖಂಡಿತ! ನಿಮ್ಮ ನೋಂದಣಿ ಅರ್ಜಿಯನ್ನು ಬ್ಯಾಂಕ್ ಮ್ಯಾನೇಜರ್ ಪರಿಶೀಲನೆಗೆ ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ." if effective_lang == "Kannada" else "Submitting your registration application for bank manager approval."
            return {
                'intent': 'CONFIRM_SUBMIT',
                'reply': reply_msg,
                'action': 'SUBMIT_FORM',
                'mode': 'register',
                'target_form': 'register',
                'fields': {k: reg_flow[k] for k in ['name', 'email', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                'reg_flow': reg_flow,
                'switch_language': effective_lang
            }

        email_match_reg = extract_email(converted_text, user_name=reg_flow.get('name', ''))
        phone_match_reg = re.search(r'^([6-9]\d{9})$', digits_only) if is_all_digits else None
        aadhaar_match_reg = re.search(r'^(\d{12})$', digits_only) if is_all_digits else None
        is_password_input = bool(
            not reg_flow.get('password') and reg_flow.get('name') and reg_flow.get('phone') and reg_flow.get('aadhaar') and
            (re.search(r'^\d{4,6}$', digits_only) or any(w in last_bot_msg for w in ['password', 'pin', '4-digit', 'create a password', 'ಪಾಸ್‌ವರ್ಡ್', 'ಪಿನ್']))
        )

        captured = False

        # 1. Step: Name (When name is not yet provided)
        if not reg_flow.get('name'):
            spoken_name = extract_spoken_name(text_clean)
            if not spoken_name and len(text_clean) >= 2 and not is_all_digits and not re.search(r'\b(open|register|login|help|balance|transfer|pay|no|cancel)\b', text_lower):
                # Clean name: remove common greetings
                cleaned_name = re.sub(r'^(?:hi|hello|hey|namaskar[a-z]*|ನಮಸ್ಕಾರ|ನನ್ನ\s*ಹೆಸರು|my\s*name\s*is|name\s*is|name)\s*', '', text_clean, flags=re.I).strip()
                if len(cleaned_name) >= 2 and re.match(r'^[A-Za-z\u0C80-\u0CFF\s.]+$', cleaned_name):
                    spoken_name = cleaned_name.title()
            if spoken_name:
                reg_flow['name'] = spoken_name
                captured = True

        # 2. Step: Email (When name is filled, but email is not yet provided)
        elif not reg_flow.get('email'):
            cand_email = extract_email(converted_text, user_name=reg_flow.get('name', ''))
            if not cand_email:
                # Handle username/handle fallback: convert simple username to @gmail.com
                cleaned_handle = re.sub(r'[^a-zA-Z0-9._+-]', '', text_clean.lower())
                if len(cleaned_handle) >= 3 and not is_all_digits and not any(w in cleaned_handle for w in ['skip', 'no', 'cancel', 'stop']):
                    cand_email = f"{cleaned_handle}@gmail.com"
            if cand_email:
                reg_flow['email'] = cand_email
                captured = True
            else:
                err = "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ಹೇಳಿ (ಉದಾಹರಣೆಗೆ user@gmail.com ಅಥವಾ pavan at gmail dot com)." if effective_lang == "Kannada" else "Please tell me your email address for notifications (e.g. user@gmail.com or pavan at gmail dot com)."
                return {
                    'intent': 'REGISTER_ASSIST', 'reply': err, 'action': 'FILL_REGISTER',
                    'mode': 'register', 'target_form': 'register',
                    'fields': {k: reg_flow[k] for k in ['name', 'email', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                    'reg_flow': reg_flow, 'switch_language': effective_lang
                }

        # 3. Step: Phone (When name and email are filled, but phone is not yet provided)
        elif not reg_flow.get('phone'):
            if phone_match_reg:
                reg_flow['phone'] = phone_match_reg.group(1)
                captured = True
            elif is_all_digits:
                digit_count = len(digits_only)
                if digit_count < 10:
                    err = f"ನೀವು {digit_count} ಅಂಕಿಗಳನ್ನು ನೀಡಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ 10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಹೇಳಿ." if effective_lang == "Kannada" else f"That number seems to be {digit_count} digits long. Please tell me your full 10-digit mobile number."
                else:
                    err = "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಿಖರವಾಗಿ 10 ಅಂಕಿಗಳಿರಬೇಕು ಮತ್ತು 6-9 ರಿಂದ ಪ್ರಾರಂಭವಾಗಬೇಕು." if effective_lang == "Kannada" else "Mobile number must be exactly 10 digits and start with 6-9. Please try again."
                return {
                    'intent': 'REGISTER_ASSIST', 'reply': err, 'action': 'FILL_REGISTER',
                    'mode': 'register', 'target_form': 'register',
                    'fields': {k: reg_flow[k] for k in ['name', 'email', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                    'reg_flow': reg_flow, 'switch_language': effective_lang
                }

        # 4. Step: Aadhaar (When name, email, phone are filled, but aadhaar is not yet provided)
        elif not reg_flow.get('aadhaar'):
            if aadhaar_match_reg:
                reg_flow['aadhaar'] = aadhaar_match_reg.group(1)
                captured = True
            elif is_all_digits:
                digit_count = len(digits_only)
                err = f"ನೀವು {digit_count} ಅಂಕಿಗಳನ್ನು ನೀಡಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ 12 ಅಂಕಿಗಳ ಆಧಾರ್ ಸಂಖ್ಯೆ ಹೇಳಿ." if effective_lang == "Kannada" else f"That number is {digit_count} digits. Please tell me your full 12-digit Aadhaar number."
                return {
                    'intent': 'REGISTER_ASSIST', 'reply': err, 'action': 'FILL_REGISTER',
                    'mode': 'register', 'target_form': 'register',
                    'fields': {k: reg_flow[k] for k in ['name', 'email', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                    'reg_flow': reg_flow, 'switch_language': effective_lang
                }

        # 5. Step: Password / PIN (When documents and identity fields are filled)
        elif not reg_flow.get('password'):
            if is_password_input or (is_all_digits and 4 <= len(digits_only) <= 25) or (len(text_clean) >= 4 and not re.search(r'\b(balance|transfer|cancel|stop|logout)\b', text_lower)):
                pwd_cand = extract_password(text_clean, bot_asked_pwd=True) or (digits_only if is_all_digits else text_clean)
                reg_flow['password'] = pwd_cand
                captured = True

        if captured:
            reply_msg, next_field = get_next_registration_prompt(reg_flow, effective_lang)
            act = 'OPEN_CAMERA' if next_field in ['photo_camera', 'idproof_camera'] else 'FILL_REGISTER'
            cam_target = 'photo' if next_field == 'photo_camera' else ('idproof' if next_field == 'idproof_camera' else None)
            return {
                'intent': 'REGISTER_ASSIST',
                'reply': reply_msg,
                'action': act,
                'camera_target': cam_target,
                'mode': 'register',
                'target_form': 'register',
                'fields': {k: reg_flow[k] for k in ['name', 'email', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                'reg_flow': reg_flow,
                'switch_language': effective_lang
            }

    # ── Step-by-Step Login Context Handler ──
    # When visitor is in login flow, capture bare field inputs (phone/aadhaar/customer ID, password)
    is_login_context = bool(
        is_visitor and not is_reg_context and (
            current_tab == 'login' or
            any(w in last_bot_msg for w in [
                'opening the login form', 'login form', 'sign in', 'log in', 'ಲಾಗಿನ್ ಫಾರ್ಮ್', 'ಪ್ರವೇಶಿಸಲು',
                'noted your mobile number as', 'noted your login identifier', 'provide your password to sign in',
                'password to sign in', 'password to log in', 'mobile number or aadhaar and password to sign in'
            ])
        ) and not re.search(r'\b(open\s*register|new\s*account|open\s*account|ನೋಂದಣಿ|ಹೊಸ\s*ಖಾತೆ)\b', text_lower)
    )

    if is_login_context and text_clean and not re.search(r'\b(register|registration|signup|sign\s*up|new\s*account|open\s*account|balance|atm|logout|history|cancel|stop|no|ಬೇಡ|ರದ್ದು)\b', text_lower):
        # Word-to-digit mapping for spoken single digits
        word_digit_map = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
            'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
        }
        converted_text = text_clean
        for word, digit in word_digit_map.items():
            converted_text = re.sub(r'\b' + re.escape(word) + r'\b', digit, converted_text, flags=re.IGNORECASE)

        digits_only = re.sub(r'[\s\-,]+', '', converted_text)
        is_all_digits = digits_only.isdigit() and len(digits_only) > 0

        # Identifier resolution: check user_state or search conversation history
        ident = user_state.get('login_identifier') or ''
        if not ident and conversation_history:
            for turn in reversed(conversation_history):
                txt = turn.get('content', '')
                if turn.get('role') == 'user':
                    c = re.sub(r'[\s\-,]+', '', txt)
                    for word, digit in word_digit_map.items():
                        c = re.sub(r'\b' + re.escape(word) + r'\b', digit, c, flags=re.IGNORECASE)
                    c = re.sub(r'[\s\-,]+', '', c)
                    if re.match(r'^[6-9]\d{9}$', c) or re.match(r'^\d{12}$', c) or re.match(r'^CUST\d+$', c, re.I):
                        ident = c
                        break
                elif turn.get('role') == 'assistant':
                    m = re.search(r'\b([6-9]\d{9})\b', re.sub(r'[\s\-,]+', '', txt))
                    if m:
                        ident = m.group(1)
                        break

        # Check if user input is password
        is_pwd_input = bool(
            any(w in last_bot_msg for w in ['provide your password to sign in', 'password to sign in', 'password to log in', 'ಪಾಸ್‌ವರ್ಡ್ ಹೇಳಿ', 'ಪ್ರವೇಶಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್']) or
            (ident and (is_all_digits and 4 <= len(digits_only) <= 25)) or
            re.search(r'\b(?:password|pass|pin|ಪಾಸ್‌ವರ್ಡ್|ಪಿನ್)\b', text_lower)
        )

        phone_match_login = re.search(r'^([6-9]\d{9})$', digits_only) if is_all_digits else None
        aadhaar_match_login = re.search(r'^(\d{12})$', digits_only) if is_all_digits else None
        cust_match_login = re.search(r'^(CUST\d+)$', text_clean, re.I)

        if is_pwd_input and not (not ident and (phone_match_login or aadhaar_match_login or cust_match_login)):
            pwd_cand = extract_password(text_clean, bot_asked_pwd=True) or (digits_only if is_all_digits else text_clean)
            reply_msg = (
                "ಪಾಸ್‌ವರ್ಡ್ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಲಾಗುತ್ತಿದೆ..."
                if effective_lang == "Kannada" else
                "Password received. Signing you into your account now..."
            )
            return {
                'intent': 'VOICE_FILL_LOGIN',
                'reply': reply_msg,
                'action': 'SUBMIT_FORM',
                'target_form': 'login',
                'mode': 'login',
                'fields': {'identifier': ident, 'password': pwd_cand} if ident else {'password': pwd_cand},
                'switch_language': effective_lang
            }

        # Check for Identifier input (Phone / Aadhaar / Customer ID)
        if phone_match_login or aadhaar_match_login or cust_match_login:
            val = phone_match_login.group(1) if phone_match_login else (aadhaar_match_login.group(1) if aadhaar_match_login else cust_match_login.group(1).upper())
            spoken_val = format_text_for_speech(val, effective_lang)
            reply_msg = (
                f"ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಲಾಗಿನ್ ಐಡಿಯನ್ನು {spoken_val} ಎಂದು ನಮೂದಿಸಲಾಗಿದೆ. ಪ್ರವೇಶಿಸಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ಹೇಳಿ."
                if effective_lang == "Kannada" else
                f"I have noted your mobile number as {spoken_val}. Please provide your password to sign in."
            )
            return {
                'intent': 'VOICE_FILL_LOGIN',
                'reply': reply_msg,
                'action': 'FILL_FORM',
                'target_form': 'login',
                'mode': 'login',
                'fields': {'identifier': val},
                'switch_language': effective_lang
            }

        elif is_all_digits and len(digits_only) < 10 and not ident:
            digit_count = len(digits_only)
            err = f"ನೀವು {digit_count} ಅಂಕಿಗಳನ್ನು ನೀಡಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ 10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಆಧಾರ್ ಸಂಖ್ಯೆ ಹೇಳಿ." if effective_lang == "Kannada" else f"That number seems to be {digit_count} digits long. Please tell me your full 10-digit mobile number or Aadhaar to sign in."
            return {
                'intent': 'VOICE_FILL_LOGIN',
                'reply': err,
                'action': 'SWITCH_AUTH_MODE',
                'mode': 'login',
                'target_form': 'login',
                'switch_language': effective_lang
            }


    # High-Priority Intercept: Direct Confirmation when Bot Asked to Proceed / Confirm
    is_affirmative = bool(re.search(r'\b(yes|yeah|yup|sure|proceed|submit|confirm|correct|right|do\s+it|ok|okay|ಹೌದು|ಸರಿ|ಖಂಡಿತ|ಮುಂದುವರಿಯಿರಿ|ಸಲ್ಲಿಸಿ)\b', text_lower))
    if bot_asked_confirmation and is_affirmative:
        # A. Registration Confirmation
        if any(w in last_bot_msg for w in ['submit registration', 'ready to submit registration', 'ನೋಂದಣಿಯನ್ನು ಸಲ್ಲಿಸಬೇಕೇ', 'registration details are ready', 'ನೋಂದಣಿ ವಿವರಗಳು ಸಿದ್ಧ']):
            reply_msg = "ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಖಾತೆ ನೋಂದಣಿಯನ್ನು ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ." if effective_lang == "Kannada" else "Thank you! Submitting your account registration for approval now."
            return {
                'intent': 'CONFIRM_SUBMIT',
                'reply': reply_msg,
                'action': 'SUBMIT_REGISTER',
                'target_form': 'register',
                'mode': 'register',
                'fields': {k: reg_flow[k] for k in ['name', 'phone', 'aadhaar', 'password'] if k in reg_flow},
                'reg_flow': reg_flow,
                'switch_language': effective_lang
            }

        # B. Login Confirmation
        if any(w in last_bot_msg for w in ['ready to log in', 'ready to sign in', 'ಖಾತೆಗೆ ಲಾಗಿನ್']):
            reply_msg = "ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಲಾಗುತ್ತಿದೆ..." if effective_lang == "Kannada" else "Thank you! Logging into your account now..."
            return {
                'intent': 'CONFIRM_SUBMIT',
                'reply': reply_msg,
                'action': 'SUBMIT_FORM',
                'target_form': 'login',
                'mode': 'login',
                'switch_language': effective_lang
            }

        # C. KYC Confirmation (Logged in users only)
        user_name = user_state.get('user_name') or 'Customer'
        if any(w in last_bot_msg for w in ['logged in as', 'is that correct', 'feel my name', 'fill my name', 'ಹೆಸರು', 'ನಿಮ್ಮ ಹೆಸರು']):
            reply_msg = get_translation(effective_lang, 'fill_name_success').format(user_name)
            return {
                'intent': 'VOICE_FILL_KYC',
                'reply': reply_msg,
                'action': 'FILL_FORM',
                'target_form': 'kyc',
                'fields': {'name': user_name},
                'redirect': '/aadhaar-kyc',
                'switch_language': effective_lang
            }

        if not is_visitor and any(w in last_bot_msg for w in ['re-kyc', 're kyc', 'retry kyc', 'ಮತ್ತೆ ಕೆವೈಸಿ', 'ಮರು-ಕೆವೈಸಿ', 'rejected because', 'ತಿರಸ್ಕರಿಸಲ್ಪಟ್ಟಿದೆ', 'kyc verification']):
            kyc_flow = {'step': 1}
            reason = (user_state.get('kyc_rejection_reason') or 'Verification rejected by administrator').strip().rstrip('.')
            if user_name and user_name != 'Visitor':
                kyc_flow['name'] = user_name
                ack = (f"ನಿಮ್ಮ ಹಿಂದಿನ ಆಧಾರ್ ಕೆವೈಸಿ ತಿರಸ್ಕರಿಸಲ್ಪಟ್ಟಿದೆ (ಕಾರಣ: {reason}). ನಿಮ್ಮ ಮರು-ಕೆವೈಸಿ ಪ್ರಾರಂಭಿಸಲಾಗುತ್ತಿದೆ. ನಿಮ್ಮ ಹೆಸರು {user_name} ಎಂದು ನಮೂದಿಸಲಾಗಿದೆ."
                       if effective_lang == "Kannada" else
                       f"Your previous Aadhaar KYC was rejected because: {reason}. Starting fresh re-KYC for {user_name}. I have entered your name as {user_name}.")
            else:
                ack = ("ನಿಮ್ಮ ಕೆವೈಸಿ ಪರಿಶೀಲನೆಯನ್ನು ಮರುಹೊಂದಿಸಲಾಗುತ್ತಿದೆ."
                       if effective_lang == "Kannada" else
                       "Resetting KYC verification.")
            reply_msg, next_field = get_next_kyc_prompt(kyc_flow, effective_lang, acknowledged_msg=ack)
            return {
                'intent': 'KYC_RETRY',
                'reply': reply_msg,
                'action': 'RESET_KYC',
                'redirect': '/aadhaar-kyc?retry=true',
                'mode': 'kyc',
                'target_form': 'kyc',
                'fields': {'name': kyc_flow.get('name')},
                'kyc_flow': kyc_flow,
                'switch_language': effective_lang
            }

    # Step-by-Step KYC Context
    is_kyc_context = bool(
        current_tab == 'kyc' or
        current_page == '/aadhaar-kyc' or
        bool(kyc_flow)
    )

    # 1. Step 2 OTP Generation Confirmation (from step 1 completed or explicit command)
    is_generate_otp_confirm = bool(
        re.search(r'\b(?:generate|create|send|get|request)\s*(?:an?\s*)?(?:aadhaar\s*)?otp\b', text_lower) or
        (is_kyc_context and (
            (bool(kyc_flow.get('name')) and bool(kyc_flow.get('dob')) and bool(kyc_flow.get('aadhaar'))) or
            'ready to generate otp' in last_bot_msg or
            'ಒಟಿಪಿ ರಚಿಸಲು ಸಿದ್ಧವೇ' in last_bot_msg
        ) and re.search(r'\b(yes|submit|confirm|proceed|generate|sure|ಹೌದು|ಸಲ್ಲಿಸಿ|ರಚಿಸಿ|ಮುಂದುವರಿಸಿ)\b', text_lower)) or
        re.search(r'(ಒಟಿಪಿ\s*ರಚಿಸಿ|ಒಟಿಪಿ\s*ಕಳುಹಿಸಿ|ಒಟಿಪಿ\s*ಜನರೇಟ್)', text_clean)
    ) and not re.search(r'\b(verify|check|ಪರಿಶೀಲಿಸಿ)\b', text_lower)

    if is_generate_otp_confirm and (is_kyc_context or current_page == '/aadhaar-kyc') and not is_visitor:
        mock_otp = "123456"
        kyc_flow['step'] = 2
        kyc_flow['otp'] = mock_otp
        reply_msg = (
            "ನಿಮ್ಮ ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗೆ ಆಧಾರ್ ಒಟಿಪಿ ಕಳುಹಿಸಲಾಗಿದೆ ಮತ್ತು ನಮೂದಿಸಲಾಗಿದೆ. ಒಟಿಪಿ ಪರಿಶೀಲಿಸಲು ಸಿದ್ಧವೇ? 'ಪರಿಶೀಲಿಸಿ' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ."
            if effective_lang == "Kannada" else
            "Aadhaar OTP has been sent to your registered mobile number and entered. Ready to verify OTP? Say 'Verify OTP' or 'Submit' to proceed."
        )
        return {
            'intent': 'KYC_GENERATE_OTP',
            'reply': reply_msg,
            'action': 'GENERATE_KYC_OTP',
            'target_form': 'kyc',
            'fields': {'otp': mock_otp},
            'kyc_flow': kyc_flow,
            'switch_language': effective_lang
        }

    # 2. Step 3 OTP Verification Confirmation (from step 2 completed or explicit command)
    is_verify_otp_confirm = bool(
        re.search(r'\b(?:verify|validate|submit|check|enter)\s*(?:an?\s*)?(?:aadhaar\s*)?otp\b', text_lower) or
        (is_kyc_context and (
            kyc_flow.get('step') == 2 or
            'ready to verify otp' in last_bot_msg or
            'ಒಟಿಪಿ ಪರಿಶೀಲಿಸಲು ಸಿದ್ಧವೇ' in last_bot_msg
        ) and re.search(r'\b(yes|submit|confirm|proceed|verify|sure|123456|ಹೌದು|ಸಲ್ಲಿಸಿ|ಪರಿಶೀಲಿಸಿ|ಮುಂದುವರಿಸಿ)\b', text_lower)) or
        re.search(r'(ಒಟಿಪಿ\s*ಪರಿಶೀಲಿಸಿ|ಒಟಿಪಿ\s*ಸಲ್ಲಿಸಿ)', text_clean)
    )

    if is_verify_otp_confirm and (is_kyc_context or current_page == '/aadhaar-kyc') and not is_visitor:
        kyc_flow['step'] = 3
        reply_msg = (
            "ಒಟಿಪಿ ಯಶಸ್ವಿಯಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ! ಈಗ ಮುಖದ ಲೈವ್‌ನೆಸ್ ಸ್ಕ್ಯಾನ್ ಆರಂಭವಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಕ್ಯಾಮೆರಾ ಕಡೆಗೆ ನೇರವಾಗಿ ನೋಡಿ."
            if effective_lang == "Kannada" else
            "OTP verified successfully! Now starting face liveness scan. Please look directly at the camera."
        )
        return {
            'intent': 'KYC_VERIFY_OTP',
            'reply': reply_msg,
            'action': 'VERIFY_KYC_OTP',
            'target_form': 'kyc',
            'kyc_flow': kyc_flow,
            'switch_language': effective_lang
        }

    # 3. Step-by-Step KYC Details Entry (Name, DOB, Aadhaar)
    if is_kyc_context and not is_visitor and not re.search(r'\b(balance|transfer|pay|send|loan|atm|statement|logout|ಬ್ಯಾಲೆನ್ಸ್|ವರ್ಗಾವಣೆ)\b', text_lower):
        dob_val = parse_dob(text_clean)
        num_type, num_val = extract_phone_or_aadhaar(text_clean)
        aadhaar_val = num_val if num_type == 'aadhaar' else None
        if not aadhaar_val:
            # Check if 12 consecutive digits exist after stripping non-digits
            only_digits = re.sub(r'[^\d]', '', text_clean)
            if len(only_digits) == 12:
                aadhaar_val = only_digits

        kyc_name_val = None
        if not dob_val and not aadhaar_val:
            kyc_name_val = extract_spoken_name(text_clean)
            # Only attempt name fallback if name has NOT been provided yet and bot specifically asked for full name
            if not kyc_name_val and not kyc_flow.get('name') and ('tell me your full name' in last_bot_msg or 'full name to start' in last_bot_msg or 'ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ' in last_bot_msg):
                cand_name = re.sub(r'[^a-zA-Zಀ-೿\s]', '', text_clean).strip()
                words = cand_name.split()
                invalid_words = {'password', 'pin', 'pass', 'balance', 'transfer', 'send', 'pay', 'money', 'cancel', 'no', 'stop', 'wait', 'yes', 'submit', 'logout', 'login', 'register', 'help', 'atm', 'card', 'kyc', 'otp', 'aadhaar', 'aadhar', 'number', 'num', 'account', 'dob', 'date', 'birth', 'phone', 'mobile', 'ಹೆಸರು', 'ಆಧಾರ್', 'ಸಂಖ್ಯೆ'}
                if 1 <= len(words) <= 4 and not any(w.lower() in invalid_words for w in words):
                    kyc_name_val = cand_name

        if kyc_name_val or dob_val or aadhaar_val:
            ack_parts = []
            if kyc_name_val:
                kyc_flow['name'] = kyc_name_val
                ack_parts.append(f"ನಿಮ್ಮ ಹೆಸರು {kyc_name_val}" if effective_lang == "Kannada" else f"your name as {kyc_name_val}")
            if dob_val:
                kyc_flow['dob'] = dob_val
                ack_parts.append(f"ನಿಮ್ಮ ಹುಟ್ಟಿದ ದಿನಾಂಕ {dob_val}" if effective_lang == "Kannada" else f"your Date of Birth as {dob_val}")
            if aadhaar_val:
                kyc_flow['aadhaar'] = aadhaar_val
                spoken_aadhaar = format_text_for_speech(aadhaar_val, effective_lang)
                ack_parts.append(f"ಆಧಾರ್ ಸಂಖ್ಯೆ {spoken_aadhaar}" if effective_lang == "Kannada" else f"Aadhaar number as {spoken_aadhaar}")

            ack_msg = ("ನಾನು " + ", ".join(ack_parts) + " ನಮೂದಿಸಿದ್ದೇನೆ." if effective_lang == "Kannada" else "I have entered " + ", ".join(ack_parts) + ".")
            reply_msg, next_field = get_next_kyc_prompt(kyc_flow, effective_lang, acknowledged_msg=ack_msg)
            
            return {
                'intent': 'VOICE_FILL_KYC',
                'reply': reply_msg,
                'action': 'FILL_FORM',
                'target_form': 'kyc',
                'fields': {k: kyc_flow[k] for k in ['name', 'dob', 'aadhaar'] if k in kyc_flow},
                'kyc_flow': kyc_flow,
                'switch_language': effective_lang
            }

    # High-Priority Intercept: User Confirmation ("yes", "ಹೌದು", "submit", "ಸಲ್ಲಿಸಿ", etc.)
    is_affirmative = bool(re.search(r'\b(yes|yeah|yup|sure|proceed|submit|confirm|correct|right|do\s+it|ok|okay|ಹೌದು|ಸರಿ|ಖಂಡಿತ|ಮುಂದುವರಿಯಿರಿ|ಸಲ್ಲಿಸಿ)\b', text_lower))
    if is_affirmative:
        user_name = user_state.get('user_name') or 'Customer'
        if any(w in last_bot_msg for w in ['logged in as', 'is that correct', 'feel my name', 'fill my name', 'ಹೆಸರು', 'ನಿಮ್ಮ ಹೆಸರು']):
            reply_msg = get_translation(effective_lang, 'fill_name_success').format(user_name)
            return {
                'intent': 'VOICE_FILL_KYC',
                'reply': reply_msg,
                'action': 'FILL_FORM',
                'target_form': 'kyc',
                'fields': {'name': user_name},
                'redirect': '/aadhaar-kyc',
                'switch_language': effective_lang
            }
        
        # If bot asked about re-KYC or explained rejection
        if any(w in last_bot_msg for w in ['re-kyc', 're kyc', 'retry kyc', 'ಮತ್ತೆ ಕೆವೈಸಿ', 'ಮರು-ಕೆವೈಸಿ', 'rejected because', 'ತಿರಸ್ಕರಿಸಲ್ಪಟ್ಟಿದೆ']):
            kyc_flow = {'step': 1}
            if user_name and user_name != 'Visitor':
                kyc_flow['name'] = user_name
                ack = (f"ಉತ್ತಮ! ನಿಮ್ಮ ಮರು-ಕೆವೈಸಿ ಹಂತ ಹಂತವಾಗಿ ಮುಂದುವರಿಸೋಣ. ನಿಮ್ಮ ಹೆಸರು {user_name} ಎಂದು ನಮೂದಿಸಲಾಗಿದೆ."
                       if effective_lang == "Kannada" else
                       f"Great! Let's proceed with your re-KYC step by step. I have entered your name as {user_name}.")
            else:
                ack = ("ಉತ್ತಮ! ನಿಮ್ಮ ಮರು-ಕೆವೈಸಿ ಹಂತ ಹಂತವಾಗಿ ಮುಂದುವರಿಸೋಣ."
                       if effective_lang == "Kannada" else
                       "Great! Let's proceed with your re-KYC step by step.")
            reply_msg, next_field = get_next_kyc_prompt(kyc_flow, effective_lang, acknowledged_msg=ack)
            return {
                'intent': 'KYC_RETRY',
                'reply': reply_msg,
                'action': 'FILL_FORM',
                'target_form': 'kyc',
                'fields': {'name': kyc_flow.get('name')},
                'kyc_flow': kyc_flow,
                'redirect': '/aadhaar-kyc?retry=true',
                'switch_language': effective_lang
            }
        
        if any(w in last_bot_msg for w in ['ready to submit kyc', 'submit kyc', 'ಸಲ್ಲಿಸಲು ಸಿದ್ಧವೇ', 'ಕೆವೈಸಿ ಸಲ್ಲಿಸಬೇಕೇ', 'face scan completed']):
            reply_msg = get_translation(effective_lang, 'confirm_submit_success')
            return {
                'intent': 'CONFIRM_SUBMIT',
                'reply': reply_msg,
                'action': 'SUBMIT_FORM',
                'target_form': 'kyc',
                'redirect': '/aadhaar-kyc',
                'switch_language': effective_lang
            }

        if any(w in last_bot_msg for w in ['simulate kyc', 'ಸಿಮ್ಯುಲೇಟ್']):
            kyc_name = user_state.get('user_name') or 'Customer'
            aadhaar_val = user_state.get('aadhaar_number') or "123456789001"
            reply_msg = (
                "ನಿಮ್ಮ ಆಧಾರ್ ಕೆವೈಸಿ ಒಟಿಪಿಯನ್ನು ಸಿಮ್ಯುಲೇಟ್ ಮಾಡಿ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ..."
                if effective_lang == "Kannada" else
                "Simulating and verifying your KYC OTP now..."
            )
            return {
                'intent': 'KYC_SIMULATE_ALL',
                'reply': reply_msg,
                'action': 'SIMULATE_KYC_AUTO',
                'target_form': 'kyc',
                'fields': {'name': kyc_name, 'aadhaar': aadhaar_val, 'dob': '1995-05-15'},
                'redirect': '/aadhaar-kyc',
                'switch_language': effective_lang
            }

        # Visitor Confirmation (Login vs Registration)
        if is_visitor:
            if current_tab == 'register' or any(w in last_bot_msg for w in ['registration', 'register', 'ನೋಂದಣಿ']):
                reply_msg = "ನಿಮ್ಮ ನೋಂದಣಿಯನ್ನು ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ..." if effective_lang == "Kannada" else "Submitting your registration for approval now."
                return {
                    'intent': 'CONFIRM_SUBMIT',
                    'reply': reply_msg,
                    'action': 'SUBMIT_FORM',
                    'target_form': 'register',
                    'switch_language': effective_lang
                }
            else:
                reply_msg = "ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಲಾಗುತ್ತಿದೆ..." if effective_lang == "Kannada" else "Logging you in now..."
                return {
                    'intent': 'CONFIRM_SUBMIT',
                    'reply': reply_msg,
                    'action': 'SUBMIT_FORM',
                    'target_form': 'login',
                    'switch_language': effective_lang
                }

        # General confirmation (e.g. transfer, payment, etc.)
        target_form = None
        if any(w in last_bot_msg for w in ['account', 'acc', 'ಖಾತೆ', 'bank transfer', 'ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ']):
            target_form = 'pay-acc'
        elif any(w in last_bot_msg for w in ['phone', 'mobile', 'ಮೊಬೈಲ್']):
            target_form = 'pay-phone'

        reply_msg = get_translation(effective_lang, 'confirm_submit_success')
        return {
            'intent': 'CONFIRM_SUBMIT',
            'reply': reply_msg,
            'action': 'SUBMIT_FORM',
            'target_form': target_form,
            'switch_language': effective_lang
        }

    # 1. Resilient Rule-Based High-Speed Banking Engine (sub-millisecond local execution)

    # Cancellation
    if re.search(r"(no|cancel|stop|wait|dont|don't|ಬೇಡ|ರದ್ದು|ರದ್ದುಮಾಡಿ|ನಿಲ್ಲಿಸು|ಬೇಡ ಸಿರಿ)", text_lower):
        reply_msg = get_translation(effective_lang, 'cancel_submit_success')
        return {
            'intent': 'CANCEL_SUBMIT',
            'reply': reply_msg,
            'action': 'CANCEL_SUBMIT',
            'switch_language': effective_lang
        }



    # Balance Inquiry
    is_bal_inquiry = bool(
        (re.search(r'\b(balance|money\s*left|account\s*balance|check\s*balance|ಬ್ಯಾಲೆನ್ಸ್|ಖಾತೆಯಲ್ಲಿ ಹಣ|ಹಣ ಎಷ್ಟಿದೆ)\b', text_lower) or
         (re.search(r'\b(money|funds|amount|ಹಣ)\b', text_lower) and re.search(r'\b(how\s*much|what\s*is|check|show|view|tell\s*me|available|ಎಷ್ಟು|ಪರಿಶೀಲಿಸಿ|ತಿಳಿಸಿ|ತೋರಿಸಿ)\b', text_lower))) and
        not re.search(r'\b(transfer|pay|send|give|deposit|bill|ವರ್ಗಾವಣೆ|ಪಾವತಿ|ಕಳುಹಿಸಿ|ಕಳಿಸು|ಕೊಡು)\b', text_lower)
    )
    if is_bal_inquiry:
        acc_num = user_state.get('account_number', 'ACC80001')
        balance = user_state.get('balance', '15000.00')
        acc_spoken = format_text_for_speech(acc_num, effective_lang)
        amt_match = re.match(r'(\d+)(?:\.(\d+))?', str(balance))
        amt_int = int(amt_match.group(1)) if amt_match else 0
        amt_dec = int(amt_match.group(2)[:2]) if amt_match and amt_match.group(2) else 0

        if effective_lang == 'Kannada':
            bal_words = f"{amt_int} ರೂಪಾಯಿ"
            if amt_dec > 0: bal_words += f" {amt_dec} ಪೈಸೆ"
            reply_text = f"ಖಾತೆ {acc_spoken} ಗಾಗಿ ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಬ್ಯಾಲೆನ್ಸ್ {bal_words}."
        else:
            bal_words = f"{amt_int} rupees"
            if amt_dec > 0: bal_words += f" and {amt_dec} paise"
            reply_text = f"Your current account balance for account {acc_spoken} is {bal_words}."

        return {
            'intent': 'BALANCE_INQUIRY',
            'reply': reply_text,
            'action': 'SPEAK_BALANCE',
            'switch_language': effective_lang
        }

    # Visitor transfer intercept
    if is_visitor and re.search(r'\b(pay|transfer|send\s*money|money\s*transfer|ವರ್ಗಾವಣೆ|ಪಾವತಿ)\b', text_lower):
        reply_msg = "ಹಣ ವರ್ಗಾವಣೆ ಮಾಡಲು ದಯವಿಟ್ಟು ಮೊದಲು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಿ." if effective_lang == "Kannada" else "Please log in to your account first to make payments or transfers."
        return {
            'intent': 'SWITCH_AUTH_MODE',
            'reply': reply_msg,
            'action': 'SWITCH_AUTH_MODE',
            'mode': 'login',
            'target_form': 'login',
            'switch_language': effective_lang
        }

    # Money Transfer to Phone & Bank Account (authenticated users only)
    # Check for 10-digit mobile number in text (handling spaces, dashes, etc.)
    num_type, num_val = extract_phone_or_aadhaar(text_clean)
    raw_phone_val = num_val if num_type == 'phone' else None

    # Detect Account Number
    raw_acc_val = extract_account_number(text_clean)

    # If user provided a Bank Account number
    if not is_visitor and raw_acc_val:
        acc_val = raw_acc_val
        spoken_acc = format_text_for_speech(acc_val, effective_lang)
        amt_val = None
        # Extract amount by removing account digits & identifiers from remaining text
        text_without_acc = re.sub(r'(?:acc(?:ount)?\s*#?\s*|ಖಾತೆ\s*ಸಂಖ್ಯೆ\s*)?[0-9\s,\.\-]+', ' ', text_clean, flags=re.I)
        amt_match = re.search(r'\b(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\b', text_without_acc, re.IGNORECASE)
        if amt_match:
            amt_val = amt_match.group(1)

        if amt_val:
            reply = (
                f"ನಾನು ಖಾತೆ {spoken_acc} ಗೆ ₹{amt_val} ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ."
                if effective_lang == "Kannada" else
                f"I have prepared a transfer of ₹{amt_val} to account {spoken_acc}. Ready to submit? Say 'Yes' or 'Submit' to proceed."
            )
            return {
                'intent': 'VOICE_FILL_PAY_ACC',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-acc',
                'fields': {'account': acc_val, 'amount': amt_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }
        else:
            reply = (
                f"ಸ್ವೀಕರಿಸುವವರ ಖಾತೆ ಸಂಖ್ಯೆ {spoken_acc} ಎಂದು ನಮೂದಿಸಲಾಗಿದೆ. ನೀವು ಎಷ್ಟು ಮೊತ್ತವನ್ನು ವರ್ಗಾಯಿಸಲು ಬಯಸುತ್ತೀರಿ?"
                if effective_lang == "Kannada" else
                f"I have entered recipient account {spoken_acc}. How much amount would you like to transfer?"
            )
            return {
                'intent': 'VOICE_FILL_PAY_ACC',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-acc',
                'fields': {'account': acc_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }

    # If user provided a Mobile Number
    if not is_visitor and raw_phone_val:
        phone_val = raw_phone_val
        spoken_phone = format_text_for_speech(phone_val, effective_lang)
        # Check for amount by removing phone digits from text
        text_without_phone = re.sub(r'[6-9](?:[\s,\-]*\d){9}', '', text_clean)
        amt_match = re.search(r'\b(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\b', text_without_phone, re.IGNORECASE)
        amt_val = amt_match.group(1) if amt_match else None

        if amt_val:
            reply = (
                f"ನಾನು ಮೊಬೈಲ್ ಸಂಖ್ಯೆ {spoken_phone} ಗೆ ₹{amt_val} ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ."
                if effective_lang == "Kannada" else
                f"I have prepared a transfer of ₹{amt_val} to mobile number {spoken_phone}. Ready to submit? Say 'Yes' or 'Submit' to proceed."
            )
            return {
                'intent': 'VOICE_FILL_PAY_PHONE',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-phone',
                'fields': {'phone': phone_val, 'amount': amt_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }
        else:
            reply = (
                f"ಸ್ವೀಕರಿಸುವವರ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ {spoken_phone} ಎಂದು ನಮೂದಿಸಲಾಗಿದೆ. ನೀವು ಎಷ್ಟು ಮೊತ್ತವನ್ನು ವರ್ಗಾಯಿಸಲು ಬಯಸುತ್ತೀರಿ?"
                if effective_lang == "Kannada" else
                f"I have entered recipient mobile {spoken_phone}. How much amount would you like to transfer?"
            )
            return {
                'intent': 'VOICE_FILL_PAY_PHONE',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-phone',
                'fields': {'phone': phone_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }

    # If only amount is given in payment context
    amount_match = re.search(r'\b(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|rupees?|ರೂಪಾಯಿ)?\b', text_clean, re.IGNORECASE)
    if not is_visitor and amount_match and (current_page == '/pay' or current_tab == 'pay' or any(w in last_bot_msg for w in ['account', 'amount', 'transfer', 'mobile', 'phone', 'ವರ್ಗಾವಣೆ', 'ಖಾತೆ', 'ಮೊತ್ತ', 'ಮೊಬೈಲ್'])):
        amt_val = amount_match.group(1)
        cleaned_last = last_bot_msg
        word_digit_map = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ಸೊನ್ನೆ': '0', 'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4',
            'ಐದು': '5', 'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9'
        }
        for w, d in word_digit_map.items():
            cleaned_last = re.sub(r'\b' + re.escape(w) + r'\b', d, cleaned_last, flags=re.I)
        cleaned_last_compact = re.sub(r'[\s,\-]+', '', cleaned_last)

        prev_acc_match = re.search(r'ACC(\d{5,12})', cleaned_last_compact, re.IGNORECASE)
        prev_phone_match = re.search(r'([6-9]\d{9})', cleaned_last_compact)

        if prev_acc_match:
            acc_val = f"ACC{prev_acc_match.group(1)}"
            spoken_acc = format_text_for_speech(acc_val, effective_lang)
            reply = (
                f"ನಾನು ಖಾತೆ {spoken_acc} ಗೆ ₹{amt_val} ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ."
                if effective_lang == "Kannada" else
                f"I have prepared a transfer of ₹{amt_val} to account {spoken_acc}. Ready to submit? Say 'Yes' or 'Submit' to proceed."
            )
            return {
                'intent': 'VOICE_FILL_PAY_ACC',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-acc',
                'fields': {'account': acc_val, 'amount': amt_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }
        elif prev_phone_match:
            phone_val = prev_phone_match.group(1)
            spoken_phone = format_text_for_speech(phone_val, effective_lang)
            reply = (
                f"ನಾನು ಮೊಬೈಲ್ ಸಂಖ್ಯೆ {spoken_phone} ಗೆ ₹{amt_val} ವರ್ಗಾವಣೆ ವಿವರಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿದ್ದೇನೆ. ಸಲ್ಲಿಸಲು 'ಹೌದು' ಅಥವಾ 'ಸಲ್ಲಿಸಿ' ಎಂದು ಹೇಳಿ."
                if effective_lang == "Kannada" else
                f"I have prepared a transfer of ₹{amt_val} to mobile number {spoken_phone}. Ready to submit? Say 'Yes' or 'Submit' to proceed."
            )
            return {
                'intent': 'VOICE_FILL_PAY_PHONE',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-phone',
                'fields': {'phone': phone_val, 'amount': amt_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }
        else:
            reply = (
                f"₹{amt_val} ವರ್ಗಾಯಿಸಲು ಸಿದ್ಧವಾಗಿದೆ. ದಯವಿಟ್ಟು ಸ್ವೀಕರಿಸುವವರ ಬ್ಯಾಂಕ್ ಖಾತೆ ಸಂಖ್ಯೆ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ತಿಳಿಸಿ."
                if effective_lang == "Kannada" else
                f"Transferring ₹{amt_val}. Please tell me the recipient's bank account number or mobile number."
            )
            return {
                'intent': 'VOICE_FILL_PAY_ACC',
                'reply': reply,
                'action': 'FILL_FORM',
                'target_form': 'pay-acc',
                'fields': {'amount': amt_val},
                'redirect': '/pay',
                'switch_language': effective_lang
            }

    # Logout / Sign Out
    if re.search(r'\b(logout|log\s*out|sign\s*out|signout|ನಿರ್ಗಮಿಸಿ|ಹೊರಬನ್ನಿ|ಲಾಗ್\s*ಔಟ್)\b', text_lower):
        reply_msg = "ಖಂಡಿತ! ನಿಮ್ಮ ಖಾತೆಯಿಂದ ಲಾಗ್‌ಔಟ್ ಮಾಡಲಾಗುತ್ತಿದೆ." if effective_lang == "Kannada" else "Logging you out now. Have a great day!"
        return {
            'intent': 'LOGOUT',
            'reply': reply_msg,
            'action': 'LOGOUT',
            'redirect': '/',
            'switch_language': effective_lang
        }

    # Clear / Delete Full Chat
    if re.search(r'\b(delete\s*chat|clear\s*chat|delete\s*full\s*chat|clear\s*full\s*chat|delete\s*history|clear\s*history|reset\s*chat|delete\s*all\s*messages|ಚಾಟ್\s*ಅಳಿಸಿ|ಸಂಭಾಷಣೆ\s*ಅಳಿಸಿ|ಹಿಸ್ಟರಿ\s*ಅಳಿಸಿ)\b', text_lower):
        reply_msg = "ಖಂಡಿತ! ನಿಮ್ಮ ಸಂಪೂರ್ಣ ಚಾಟ್ ಇತಿಹಾಸವನ್ನು ಅಳಿಸಲಾಗಿದೆ." if effective_lang == "Kannada" else "Done! Your full chat history has been deleted."
        return {
            'intent': 'CLEAR_CHAT',
            'reply': reply_msg,
            'action': 'CLEAR_CHAT',
            'switch_language': effective_lang
        }

    # ── SIRI BANK FEATURED PRODUCT & OFFER INQUIRIES ──
    # 1. Kisan Agri Loans
    if re.search(r'\b(kisan|agri|agriculture|farmer|farming|crop|4%|4\s*percent|ಕೃಷಿ|ರೈತ|ಕಿಸಾನ್|ಬೆಳೆ|ಸಾಲದ\s*ವಿವರ)\b', text_lower):
        reply_msg = (
            "ಸಿರಿ ಬ್ಯಾಂಕ್‌ನ ಕಿಸಾನ್ ವಾಯ್ಸ್ ಕೃಷಿ ಸಾಲವು ಕರ್ನಾಟಕದ ರೈತರಿಗೆ ಕೇವಲ 4% ರಿಯಾಯಿತಿ ಬಡ್ಡಿದರದಲ್ಲಿ ಲಭ್ಯವಿದೆ. ಇದಕ್ಕೆ ಯಾವುದೇ ಕಾಗದಪತ್ರಗಳ ಅಗತ್ಯವಿಲ್ಲ ಹಾಗೂ ನೇರ ಡಿಬಿಟಿ ಸಹಾಯಧನ ಸೌಲಭ್ಯವಿದೆ."
            if effective_lang == "Kannada" else
            "SIRI Bank's Kisan Voice Agri-Credit offers subsidized loans at 4.00% p.a. for Karnataka farmers with zero paperwork, direct DBT subsidy linkage, and flexible harvest-based repayments."
        )
        return {
            'intent': 'KISAN_AGRI_LOAN_INFO',
            'reply': reply_msg,
            'action': None,
            'switch_language': effective_lang
        }

    # 2. Fixed Deposit (FD) Rates
    if re.search(r'\b(fd|fixed\s*deposit|deposit\s*rates?|interest\s*rates?|7\.85|8\.35|ಎಫ್‌ಡಿ|ಫಿಕ್ಸ್ಡ್\s*ಡೆಪಾಸಿಟ್|ಬಡ್ಡಿದರ|ಠೇವಣಿ)\b', text_lower):
        reply_msg = (
            "ಸಿರಿ ಬ್ಯಾಂಕ್‌ನ ಟ್ರಿಪಲ್ ಡಿಲೈಟ್ ಫಿಕ್ಸ್ಡ್ ಡೆಪಾಸಿಟ್ (FD) ವಾರ್ಷಿಕ 7.85% ಚಕ್ರಬಡ್ಡಿ ನೀಡುತ್ತದೆ, ಮತ್ತು ಹಿರಿಯ ನಾಗರಿಕರಿಗೆ ಹೆಚ್ಚುವರಿ 0.50% ಅಂದರೆ 8.35% ಬಡ್ಡಿದರ ಲಭ್ಯವಿದೆ. ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಅವಧಿಗೆ ಮುನ್ನ ಹಿಂಪಡೆಯಲು ಯಾವುದೇ ದಂಡವಿರುವುದಿಲ್ಲ."
            if effective_lang == "Kannada" else
            "SIRI Bank's Triple Delight Fixed Deposit (FD) offers an attractive 7.85% p.a. interest rate with quarterly compounding, and an extra 0.50% (8.35% p.a.) for Senior Citizens with zero premature penalty for emergencies."
        )
        return {
            'intent': 'FD_RATES_INFO',
            'reply': reply_msg,
            'action': None,
            'switch_language': effective_lang
        }

    # 3. RuPay Platinum Debit Card Offers
    if re.search(r'\b(rupay|debit\s*card\s*offers?|card\s*offers?|platinum\s*card|ರೂಪೇ|ಡೆಬಿಟ್\s*ಕಾರ್ಡ್\s*ಆಫರ್|ಕಾರ್ಡ್\s*ಆಫರ್)\b', text_lower):
        reply_msg = (
            "ಸಿರಿ ರೂಪೇ ಪ್ಲಾಟಿನಮ್ ಕಾರ್ಡ್ ಮೊದಲ ವರ್ಷ ಸಂಪೂರ್ಣ ಉಚಿತ! ಯುಪಿಐ ಪಾವತಿಗಳಲ್ಲಿ 2x ರಿವಾರ್ಡ್ ಪಾಯಿಂಟ್‌ಗಳು, ದೇಶೀಯ ವಿಮಾನ ನಿಲ್ದಾಣ ಲಾಂಜ್ ಪ್ರವೇಶ, ಮತ್ತು ಧ್ವನಿ ಮೂಲಕ ತಕ್ಷಣ ಕಾರ್ಡ್ ಫ್ರೀಜ್ ಮಾಡುವ ಅತ್ಯುನ್ನತ ಭದ್ರತೆ ಹೊಂದಿದೆ."
            if effective_lang == "Kannada" else
            "The SIRI Contactless RuPay Platinum Debit Card has ₹0 annual fee for the first year, 2x reward points on UPI payments, free domestic airport lounge access, and instant voice-guided card freeze protection."
        )
        return {
            'intent': 'RUPAY_CARD_OFFERS_INFO',
            'reply': reply_msg,
            'action': None,
            'switch_language': effective_lang
        }

    # 4. How to Open an Account
    if re.search(r'\b(how\s*do\s*i\s*open\s*(?:an?\s*)?account|how\s*to\s*open\s*(?:an?\s*)?account|how\s*to\s*register|how\s*do\s*i\s*register|open\s*(?:an?\s*)?account\s*procedure|ಹೊಸ\s*ಖಾತೆ\s*ಹೇಗೆ|ಖಾತೆ\s*ಹೇಗೆ\s*ತೆರೆಯುವುದು|ನೋಂದಣಿ\s*ಹೇಗೆ)\b', text_lower):
        reply_msg = (
            "ಸಿರಿ ಬ್ಯಾಂಕ್‌ನಲ್ಲಿ ಖಾತೆ ತೆರೆಯುವುದು ಸಂಪೂರ್ಣ ಕಾಗದರಹಿತ ಮತ್ತು ಶೂನ್ಯ ಬ್ಯಾಲೆನ್ಸ್ ಆಗಿದೆ! ಹೋಮ್‌ಪೇಜ್‌ನಲ್ಲಿ 'ಹೊಸ ಖಾತೆ' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ, ಅಥವಾ ನನಗೆ ನಿಮ್ಮ ಹೆಸರು, ಮೊಬೈಲ್ ಮತ್ತು ಆಧಾರ್ ಸಂಖ್ಯೆ ತಿಳಿಸಿದರೆ ನಾನೇ ನಿಮಗಾಗಿ ಅರ್ಜಿ ಭರ್ತಿ ಮಾಡುತ್ತೇನೆ."
            if effective_lang == "Kannada" else
            "Opening an account with SIRI Bank is 100% paperless with zero minimum balance! Click 'Open Account' on the homepage, or simply tell me your full name, phone number, and Aadhaar number and I will register it for you hands-free."
        )
        return {
            'intent': 'OPEN_ACCOUNT_INFO',
            'reply': reply_msg,
            'action': 'FILL_REGISTER' if is_visitor else None,
            'mode': 'register',
            'target_form': 'register' if is_visitor else None,
            'switch_language': effective_lang
        }

    # 5. Smart Home Loans
    if re.search(r'\b(home\s*loans?|housing\s*loans?|ಗೃಹ\s*ಸಾಲ|ಮನೆ\s*ಸಾಲ)\b', text_lower):
        reply_msg = (
            "ಸಿರಿ ಬ್ಯಾಂಕ್ ಸ್ಮಾರ್ಟ್ ಗೃಹ ಸಾಲವು ಆಕರ್ಷಕ ಬಡ್ಡಿದರದಲ್ಲಿದ್ದು, ಮಹಿಳಾ ಅರ್ಜಿದಾರರಿಗೆ ಶೂನ್ಯ ಪ್ರೊಸೆಸಿಂಗ್ ಶುಲ್ಕ ಮತ್ತು 24 ಗಂಟೆಗಳಲ್ಲಿ ಕಾಗದರಹಿತ ಡಿಜಿಟಲ್ ಪೂರ್ವ-ಅನುಮೋದನೆ ನೀಡುತ್ತದೆ."
            if effective_lang == "Kannada" else
            "SIRI Bank Smart Home Loans feature attractive interest rates starting at 8.25% p.a., with zero processing fees for women co-applicants and paperless digital pre-approval in under 24 hours."
        )
        return {
            'intent': 'HOME_LOAN_INFO',
            'reply': reply_msg,
            'action': None,
            'switch_language': effective_lang
        }

    # Navigation & Sub-tool Actions
    is_nav = bool(re.search(r'(?:\b(?:open|go\s*to|show|navigate|visit|view|take\s*me\s*to)\b|ತೆರೆ|ತೆರೆಯಿರಿ|ಹೋಗು|ಪುಟ|ಓಪನ್|ಹೋಗಿ|ತೋರಿಸಿ|ಕ್ಲಿಕ್|ಮಾಡಬೇಕಿದೆ)', text_lower))

    # Sub-tools in Pay section
    if re.search(r'(\b(?:bank\s*transfer|direct\s*bank\s*transfer)\b|ಬ್ಯಾಂಕ್\s*ವರ್ಗಾವಣೆ)', text_lower):
        reply_msg = "ಖಂಡಿತ! ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ ಆಯ್ಕೆಯನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ." if effective_lang == "Kannada" else "Opening Bank Transfer option for you."
        return {'intent': 'SUB_ACTION_BANK_TRANSFER', 'reply': reply_msg, 'action': 'OPEN_TOOL', 'tool': 'bank-transfer', 'redirect': '/pay', 'switch_language': effective_lang}

    if re.search(r'(\b(?:send\s*(?:money\s*)?to\s*(?:phone|mobile)(?:\s*number)?|pay\s*(?:money\s*)?to\s*(?:phone|mobile)(?:\s*number)?|petu\s*(?:phone|mobile)(?:\s*number)?|pay\s*phone|pay\s*mobile|to\s*mobile|to\s*phone|phone\s*transfer|mobile\s*transfer|phone\s*pay|mobile\s*pay)\b|ಮೊಬೈಲ್\s*ವರ್ಗಾವಣೆ|ಫೋನ್\s*ಪೇ|ಮೊಬೈಲ್\s*ಪಾವತಿ|ಮೊಬೈಲ್‌ಗೆ\s*ಹಣ|ಫೋನ್‌ಗೆ\s*ಹಣ)', text_lower):
        reply_msg = "ಖಂಡಿತ! ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗೆ ವರ್ಗಾವಣೆ ಆಯ್ಕೆಯನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ." if effective_lang == "Kannada" else "Opening Transfer to Mobile option."
        return {'intent': 'SUB_ACTION_PHONE_PAY', 'reply': reply_msg, 'action': 'OPEN_TOOL', 'tool': 'pay-phone', 'redirect': '/pay', 'switch_language': effective_lang}

    if re.search(r'(\b(?:to\s*upi|upi\s*pay)\b|ಯುಪಿಐ)', text_lower):
        reply_msg = "ಖಂಡಿತ! ಯುಪಿಐ ಪಾವತಿ ಆಯ್ಕೆಯನ್ನು ತೆರೆಯಲಾಗುತ್ತಿದೆ." if effective_lang == "Kannada" else "Opening UPI Pay option."
        return {'intent': 'SUB_ACTION_UPI_PAY', 'reply': reply_msg, 'action': 'OPEN_TOOL', 'tool': 'upi-pay', 'redirect': '/pay', 'switch_language': effective_lang}

    # Credit Card Request vs Debit Card Request
    is_apply_credit_card = bool(
        re.search(r'(\b(?:apply\s*(?:for\s*)?(?:an?\s*)?(?:new\s*)?credit\s*card|order\s*(?:an?\s*)?(?:new\s*)?credit\s*card|request\s*(?:an?\s*)?(?:new\s*)?credit\s*card|issue\s*(?:an?\s*)?(?:new\s*)?credit\s*card|need\s*(?:an?\s*)?(?:new\s*)?credit\s*card|get\s*(?:me\s*)?(?:an?\s*)?(?:new\s*)?credit\s*card|issue\s*credit)\b|ಕ್ರೆಡಿಟ್\s*ಕಾರ್ಡ್\s*ಬೇಕು|ಕ್ರೆಡಿಟ್\s*ಕಾರ್ಡ್\s*ಅಪ್ಲೈ|ಕ್ರೆಡಿಟ್\s*ಕಾರ್ಡ್\s*ನೀಡಿ)', text_lower) or
        (re.search(r'\b(apply|order|issue|request|want|need)\b', text_lower) and re.search(r'\b(credit)\b', text_lower))
    )

    is_apply_debit_card = bool(
        re.search(r'(\b(?:apply\s*(?:for\s*)?(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|order\s*(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|request\s*(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|issue\s*(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|need\s*(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|get\s*(?:me\s*)?(?:an?\s*)?(?:new\s*)?(?:atm|debit)?\s*card|issue\s*debit)\b|ಎಟಿಎಂ\s*ಕಾರ್ಡ್\s*ಬೇಕು|ಡೆಬಿಟ್\s*ಕಾರ್ಡ್\s*ಬೇಕು|ಕಾರ್ಡ್\s*ಅಪ್ಲೈ|ಕಾರ್ಡ್\s*ನೀಡಿ|ಹೊಸ\s*ಕಾರ್ಡ್|ಹೊಸ\s*ಎಟಿಎಂ)', text_lower) or
        (re.search(r'\b(apply|order|issue|request|want|need)\b', text_lower) and re.search(r'\b(atm|card|debit)\b', text_lower))
    )

    if is_apply_credit_card:
        if is_visitor:
            reply_msg = "ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್‌ಗಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ದಯವಿಟ್ಟು ಮೊದಲು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಿ." if effective_lang == "Kannada" else "Please log in to your account first to apply for a Credit card."
            return {'intent': 'SWITCH_AUTH_MODE', 'reply': reply_msg, 'action': 'SWITCH_AUTH_MODE', 'mode': 'login', 'switch_language': effective_lang}
        reply_msg = (
            "ಹೊಸ ಸಿರಿ ಪ್ಲಾಟಿನಮ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್‌ಗಾಗಿ ನಿಮ್ಮ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸಲಾಗಿದೆ! ನೀವು ಇದರ ಸ್ಥಿತಿಯನ್ನು ವಿನಂತಿ ಇತಿಹಾಸದಲ್ಲಿ ಪರಿಶೀಲಿಸಬಹುದು."
            if effective_lang == "Kannada" else
            "Your application for a new SIRI Platinum Credit Card has been submitted for credit review! You can track the status under Request History."
        )
        return {
            'intent': 'CREDIT_CARD_REQUEST',
            'reply': reply_msg,
            'action': 'CREATE_REQUEST_CREDIT',
            'card_type': 'credit',
            'redirect': '/atm-services',
            'switch_language': effective_lang
        }

    if is_apply_debit_card:
        if is_visitor:
            reply_msg = (
                "ಎಟಿಎಂ ಕಾರ್ಡ್‌ಗಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ದಯವಿಟ್ಟು ಮೊದಲು ನಿಮ್ಮ ಖಾತೆಗೆ ಲಾಗಿನ್ ಮಾಡಿ."
                if effective_lang == "Kannada" else
                "Please log in to your account first to apply for an ATM card."
            )
            return {
                'intent': 'SWITCH_AUTH_MODE',
                'reply': reply_msg,
                'action': 'SWITCH_AUTH_MODE',
                'mode': 'login',
                'switch_language': effective_lang
            }
        reply_msg = (
            "ಹೊಸ ವೀಸಾ ಡೆಬಿಟ್ ಎಟಿಎಂ ಕಾರ್ಡ್‌ಗಾಗಿ ನಿಮ್ಮ ಅರ್ಜಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ! ನೀವು ಇದರ ಸ್ಥಿತಿಯನ್ನು ವಿನಂತಿ ಇತಿಹಾಸದಲ್ಲಿ ಪರಿಶೀಲಿಸಬಹುದು."
            if effective_lang == "Kannada" else
            "Your application for a new Visa Debit ATM card has been submitted successfully! You can track the status under Request History."
        )
        return {
            'intent': 'ATM_CARD_REQUEST',
            'reply': reply_msg,
            'action': 'CREATE_REQUEST_ATM',
            'card_type': 'debit',
            'redirect': '/atm-services',
            'switch_language': effective_lang
        }

    # KYC / Aadhaar section
    if re.search(r'(?:\b(?:kyc|aadhaar|aadhar|adhsr|adhhar|adhar|e-kyc)\b|ಆಧಾರ್|ಕೆವೈಸಿ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|tab|screen|other|form)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ|ಫಾರ್ಮ್)', text_lower) or
        text_clean.lower().strip() in ['kyc', 'aadhaar kyc', 'aadhar kyc', 'adhsr kyc', 'adhar kyc', 'adhhar kyc', 'open kyc', 'open aadhar kyc', 'open aadhaar kyc', 'open adhsr kyc', 'open other kyc', 'other kyc', 'e-kyc', 'aadhaar', 'aadhar', 'adhsr', 'adhar', 'ಆಧಾರ್ ಕೆವೈಸಿ', 'ಕೆವೈಸಿ', 'ಆಧಾರ್']
    ):
        if not is_visitor and user_state.get('kyc_status') == 'REJECTED' and not user_state.get('kyc_retry_mode'):
            reason = (user_state.get('kyc_rejection_reason') or 'Verification rejected by bank administrator').strip().rstrip('.')
            reply_msg = (
                f"ಬ್ಯಾಂಕ್ ಆಡಳಿತಾಧಿಕಾರಿಗಳು ನೀಡಿದ ತಿರಸ್ಕರಿಸಿದ ಕಾರಣ: {reason}. ನೀವು ಮತ್ತೆ ಕೆವೈಸಿ (Re-KYC) ಮಾಡಲು ಬಯಸುವಿರಾ? ನಿಮಗಾಗಿ ಹೊಸ ಕೆವೈಸಿ ಫಾರ್ಮ್ ಅನ್ನು ತೆರೆದಿದ್ದೇನೆ. ಪ್ರಾರಂಭಿಸಲು 'ಹೌದು' ಎಂದು ಹೇಳಿ ಅಥವಾ ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರನ್ನು ತಿಳಿಸಿ."
                if effective_lang == "Kannada" else
                f"Your previous Aadhaar KYC was rejected by the bank administrator because: {reason}. Would you like to complete re-KYC now? I have opened the fresh KYC form for you. Say 'Yes' or provide your full name to start."
            )
            user_name = user_state.get('user_name') or 'Customer'
            kyc_flow = {'step': 1, 'name': user_name} if user_name != 'Visitor' else {'step': 1}
            return {
                'intent': 'KYC_REJECTED_EXPLAIN',
                'reply': reply_msg,
                'action': 'RESET_KYC',
                'redirect': '/aadhaar-kyc?retry=true',
                'mode': 'kyc',
                'target_form': 'kyc',
                'fields': {'name': kyc_flow.get('name')},
                'kyc_flow': kyc_flow,
                'switch_language': effective_lang
            }
        
        # Fresh KYC Start: Prompt for Full Name step-by-step
        kyc_flow = {'step': 1}
        reply_msg, next_field = get_next_kyc_prompt(
            kyc_flow,
            effective_lang,
            acknowledged_msg="ಖಂಡಿತ! ಆಧಾರ್ ಕೆವೈಸಿ ವಿಭಾಗ ತೆರೆಯಲಾಗುತ್ತಿದೆ. ಹಂತ ಹಂತವಾಗಿ ಪರಿಶೀಲನೆ ಮಾಡೋಣ." if effective_lang == "Kannada" else "Navigating to Aadhaar KYC. Let's complete your verification step by step."
        )
        return {
            'intent': 'NAVIGATE_KYC',
            'reply': reply_msg,
            'action': 'NAVIGATE',
            'redirect': '/aadhaar-kyc',
            'mode': 'kyc',
            'target_form': 'kyc',
            'kyc_flow': kyc_flow,
            'switch_language': effective_lang
        }

    # ATM Cards / Services section / Switch Cards
    if re.search(r'(?:\b(?:credit\s*card)\b|ಕ್ರೆಡಿಟ್\s*ಕಾರ್ಡ್)', text_lower):
        reply_msg = "ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ನಿರ್ವಹಣೆಗೆ ಬದಲಾಯಿಸಲಾಗಿದೆ." if effective_lang == "Kannada" else "Switched to Credit Card management."
        return {'intent': 'SHOW_CREDIT_CARD', 'reply': reply_msg, 'action': 'SWITCH_CARD_TAB', 'card_type': 'credit', 'redirect': '/atm-services', 'switch_language': effective_lang}

    if re.search(r'(?:\b(?:debit\s*card)\b|ಡೆಬಿಟ್\s*ಕಾರ್ಡ್)', text_lower) and not re.search(r'\b(offer|offers|benefits|ಆಫರ್)\b', text_lower):
        reply_msg = "ಡೆಬಿಟ್ ಕಾರ್ಡ್ ನಿರ್ವಹಣೆಗೆ ಬದಲಾಯಿಸಲಾಗಿದೆ." if effective_lang == "Kannada" else "Switched to Debit Card management."
        return {'intent': 'SHOW_DEBIT_CARD', 'reply': reply_msg, 'action': 'SWITCH_CARD_TAB', 'card_type': 'debit', 'redirect': '/atm-services', 'switch_language': effective_lang}

    if re.search(r'(?:\b(?:atm|cards?)\b|ಕಾರ್ಡ್|ಎಟಿಎಂ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:services?|serv|section|page|tab|screen)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ|ಸೇವೆ|ಸೇವೆಗಳು)', text_lower) or
        text_clean.lower().strip() in ['atm', 'atm serv', 'atm services', 'atm section', 'atm card', 'cards', 'ಎಟಿಎಂ', 'ಎಟಿಎಂ ಸೇವೆಗಳು', 'ಕಾರ್ಡ್']
    ):
        reply_msg = "ಖಂಡಿತ! ಎಟಿಎಂ ಸೇವೆಗಳ ವಿಭಾಗಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to ATM Services."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/atm-services', 'switch_language': effective_lang}

    # History section
    if re.search(r'(?:\b(?:history|records|transactions?)\b|ಇತಿಹಾಸ|ಹಿಂದಿನ|ವ್ಯವಹಾರ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:request|section|page|tab|screen)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ|ವಿನಂತಿ)', text_lower) or
        text_clean.lower().strip() in ['history', 'request history', 'transaction history', 'records', 'past transactions', 'ಇತಿಹಾಸ', 'ವಿನಂತಿ ಇತಿಹಾಸ', 'ವ್ಯವಹಾರ ಇತಿಹಾಸ']
    ):
        reply_msg = "ಖಂಡಿತ! ವ್ಯವಹಾರ ಇತಿಹಾಸ ವಿಭಾಗಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Request History."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/request-history', 'switch_language': effective_lang}

    # Pay section
    if re.search(r'(?:\b(?:pay|payment|transfer|money\s*transfer|send\s*money)\b|ಪಾವತಿ|ವರ್ಗಾವಣೆ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|tab|screen)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ)', text_lower) or
        text_clean.lower().strip() in ['pay', 'pay section', 'transfer', 'transfers', 'money transfer', 'payment', 'ಪಾವತಿ', 'ಹಣ ವರ್ಗಾವಣೆ']
    ):
        reply_msg = "ಖಂಡಿತ! ಪಾವತಿ ಮತ್ತು ವರ್ಗಾವಣೆ ವಿಭಾಗಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Pay & Transfers."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/pay', 'switch_language': effective_lang}

    # Profile section
    if re.search(r'(?:\b(?:profile|my\s*details)\b|ನನ್ನ ವಿವರ|ಪ್ರೊಫೈಲ್)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|tab|screen)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ)', text_lower) or
        text_clean.lower().strip() in ['profile', 'my profile', 'profile section', 'ಪ್ರೊಫೈಲ್']
    ):
        reply_msg = "ಖಂಡಿತ! ಪ್ರೊಫೈಲ್ ವಿಭಾಗಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Profile."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/profile', 'switch_language': effective_lang}

    # Home / Dashboard section
    if re.search(r'(?:\b(?:home|dashboard)\b|ಮುಖಪುಟ|ಹೋಮ್|ಡ್ಯಾಶ್‌ಬೋರ್ಡ್)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|tab|screen)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ)', text_lower) or
        text_clean.lower().strip() in ['home', 'dashboard', 'home dashboard', 'main dashboard', 'ಮುಖಪುಟ', 'ಹೋಮ್']
    ):
        reply_msg = "ಖಂಡಿತ! ಮುಖಪುಟಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Home Dashboard."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/home', 'switch_language': effective_lang}

    # Register / New Account section
    if re.search(r'(?:\b(?:register|sign\s*up|signup|new\s*account|open\s*account)\b|ಹೊಸ ಖಾತೆ|ನೋಂದಣಿ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|form)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ|ಫಾರ್ಮ್)', text_lower) or
        text_clean.lower().strip() in ['register', 'registration', 'sign up', 'signup', 'open account', 'new account', 'ನೋಂದಣಿ']
    ):
        reply_msg = "ಖಂಡಿತ! ನೋಂದಣಿ ಪುಟಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Registration."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/register', 'switch_language': effective_lang}

    # Login section
    if re.search(r'(?:\b(?:login|log\s*in|sign\s*in|signin)\b|ಲಾಗಿನ್|ಪ್ರವೇಶ)', text_lower) and (
        is_nav or
        re.search(r'(?:\b(?:section|page|form)\b|ಸೆಕ್ಷನ್|ವಿಭಾಗ|ಪುಟ|ಫಾರ್ಮ್)', text_lower) or
        text_clean.lower().strip() in ['login', 'sign in', 'log in', 'signin', 'ಲಾಗಿನ್']
    ):
        reply_msg = "ಖಂಡಿತ! ಲಾಗಿನ್ ಪುಟಕ್ಕೆ ಹೋಗುತ್ತಿದ್ದೇವೆ." if effective_lang == "Kannada" else "Navigating to Login."
        return {'intent': 'NAVIGATE', 'reply': reply_msg, 'action': 'NAVIGATE', 'redirect': '/login', 'switch_language': effective_lang}

    # Greetings & Wake words
    if re.search(r'(hi|hello|hey|namaskara|namaste|ನಮಸ್ಕಾರ|ನಮಸ್ತೆ|ಹೇಸಿರಿ|ಹೇಸರಿ|ಹೆಸರಿ|ಹೇ\s*ಸಿರಿ)', text_lower):
        return {
            'intent': 'GREETING',
            'reply': get_translation(effective_lang, 'greeting'),
            'action': None,
            'switch_language': effective_lang
        }

    # 2. Intelligent Conversational Brain: Invoke Gemini AI for open-ended queries
    gemini_result = call_gemini_conversational_ai(text_clean, user_state, effective_lang, conversation_history)
    if gemini_result and gemini_result.get('reply'):
        return gemini_result

    # Default fallback
    return {
        'intent': 'GENERAL_QUERY',
        'reply': get_translation(effective_lang, 'not_understood'),
        'action': None,
        'switch_language': effective_lang
    }
