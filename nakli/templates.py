"""Message templates: bank chat, KYC, call-centre notes and vendor onboarding.

Placeholders are filled with fake values. Hindi, Hinglish and Odia templates should be
reviewed by native speakers; corrections are very welcome.
"""

TEMPLATES = {
    "en": [
        "Hi, I am {PERSON}. My Aadhaar number is {AADHAAR} and PAN is {PAN}. Please update my KYC.",
        "Customer {PERSON} called about a failed payment to {UPI}. Callback number: {PHONE}.",
        "Please send the loan statement to {EMAIL}. Registered mobile {PHONE}, PAN {PAN}.",
        "Vendor onboarding: GSTIN {GSTIN}, bank IFSC {IFSC}, contact {PERSON} ({PHONE}).",
        "Address proof received for {PERSON}, PIN code {PINCODE}. Aadhaar {AADHAAR} verified.",
    ],
    "hinglish": [
        "Hello, main {PERSON} bol raha hoon. Mera Aadhaar {AADHAAR} hai, KYC update kar do please.",
        "Sir, maine {UPI} pe payment kiya tha par fail ho gaya. Mera number {PHONE} hai.",
        "Loan ka statement {EMAIL} pe bhej dijiye. PAN {PAN} hai.",
        "GST number {GSTIN} hai aur IFSC {IFSC}. Contact {PERSON}, {PHONE}.",
        "{PERSON} ka address proof aa gaya, PIN {PINCODE}, Aadhaar {AADHAAR}.",
    ],
    "hi": [
        "नमस्ते, मैं {PERSON} हूँ। मेरा आधार नंबर {AADHAAR} है और पैन {PAN} है। कृपया मेरा केवाईसी अपडेट करें।",
        "ग्राहक {PERSON} ने {UPI} पर असफल भुगतान के बारे में कॉल किया। कॉलबैक नंबर: {PHONE}।",
        "कृपया लोन स्टेटमेंट {EMAIL} पर भेजें। पंजीकृत मोबाइल {PHONE}, पैन {PAN}।",
        "विक्रेता पंजीकरण: जीएसटीआईएन {GSTIN}, बैंक आईएफएससी {IFSC}, संपर्क {PERSON} ({PHONE})।",
        "{PERSON} का पता प्रमाण मिल गया, पिन कोड {PINCODE}। आधार {AADHAAR} सत्यापित।",
    ],
    "or": [
        "ନମସ୍କାର, ମୁଁ {PERSON}। ମୋର ଆଧାର ନମ୍ବର {AADHAAR} ଏବଂ ପାନ୍ {PAN}। ଦୟାକରି ମୋର KYC ଅପଡେଟ୍ କରନ୍ତୁ।",
        "ଗ୍ରାହକ {PERSON} {UPI} କୁ ବିଫଳ ପେମେଣ୍ଟ ବିଷୟରେ କଲ୍ କରିଥିଲେ। କଲବ୍ୟାକ୍ ନମ୍ବର: {PHONE}।",
        "ଦୟାକରି ଋଣ ଷ୍ଟେଟମେଣ୍ଟ {EMAIL} କୁ ପଠାନ୍ତୁ। ପଞ୍ଜୀକୃତ ମୋବାଇଲ୍ {PHONE}, ପାନ୍ {PAN}।",
        "ବିକ୍ରେତା ପଞ୍ଜୀକରଣ: GSTIN {GSTIN}, ବ୍ୟାଙ୍କ IFSC {IFSC}, ଯୋଗାଯୋଗ {PERSON} ({PHONE})।",
        "{PERSON}ଙ୍କ ଠିକଣା ପ୍ରମାଣ ମିଳିଲା, ପିନ୍ କୋଡ୍ {PINCODE}। ଆଧାର {AADHAAR} ଯାଞ୍ଚ ହୋଇଛି।",
    ],
}

# Which script names are written in, and which Indian digits the indic_digits variant uses.
NAME_SCRIPT = {"en": "latin", "hinglish": "latin", "hi": "devanagari", "or": "odia"}
DIGIT_SCRIPT = {"en": "devanagari", "hinglish": "devanagari", "hi": "devanagari", "or": "odia"}
LANGS = tuple(TEMPLATES)
