"""
Phase 1: Data Foundation - Synthetic Dataset Generator & Splitter.
Generates balanced, labeled grievances in English, Hindi, and Tamil across 5 key categories.
Supports duplicate pair generation and train/val/test split creation.
"""

import json
import random
import uuid
from typing import Dict, List, Tuple
from pathlib import Path
from config import CATEGORIES, LANGUAGES, DATA_DIR

# Template seed sentences per language and category
TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "Water Supply & Quality": [
            "There is no drinking water supply in Ward {ward} for the last 3 days. People are suffering.",
            "Contaminated brown water coming from municipal tap near Street {street}. Smells foul.",
            "Main water pipeline burst near {street} crossing. Thousands of gallons leaking continuously.",
            "Water pressure is extremely low in block {block} since yesterday morning.",
            "Water tanker requested for {area} area due to acute shortage in summer."
        ],
        "Sanitation & Garbage": [
            "Garbage overflow in open dustbin at {street}. Stray dogs spreading trash all over the road.",
            "Sanitation workers have not cleared garbage dump near school in {area} for a week.",
            "Open sewer drain overflowing on main road in Ward {ward}, creating health hazards.",
            "Dead animal decaying near market square in {area}. Unbearable smell and disease risk.",
            "Public toilet near bus stand is choked and completely unusable."
        ],
        "Roads & Potholes": [
            "Huge pothole on main highway near {street} causing severe traffic jams and minor accidents.",
            "Road construction abandoned incomplete in block {block}. Deep trench left uncovered.",
            "Street light not working on dark curve near {area} flyover, highly unsafe for commuters.",
            "Speed breaker installed improperly without white paint marks near hospital road.",
            "Pavement completely broken near market, senior citizens struggling to walk."
        ],
        "Electricity & Power Cut": [
            "Transformer sparked and exploded in block {block}. Entire area without power for 12 hours.",
            "Frequent low voltage supply damaging electronic appliances in Ward {ward}.",
            "High voltage power cable hanging dangerously low near residential park in {area}.",
            "Power outage continuously for 8 hours in intense heat, patients and children affected.",
            "Electric pole leaning dangerously after yesterday heavy wind near {street}."
        ],
        "Public Healthcare & Clinics": [
            "Primary Health Center in {area} lacks basic anti-snake venom and emergency medicines.",
            "Doctors not present during working hours at municipal clinic in Ward {ward}.",
            "Stretcher and wheelchair facility unavailable for elderly patients in civil hospital.",
            "Hygiene conditions inside government hospital ward in {area} are severely degraded.",
            "Ambulance response delayed by over an hour for critical cardiac patient."
        ]
    },
    "hi": {
        "Water Supply & Quality": [
            "वार्ड नंबर {ward} में पिछले 3 दिनों से पीने का पानी नहीं आ रहा है। नागरिक परेशान हैं।",
            "{street} रोड पर नल से गंदा और बदबूदार पानी सप्लाई हो रहा है। बीमारी का खतरा है।",
            "{street} के पास मुख्य पेयजल पाइपलाइन फट गई है। हज़ारों लीटर पानी बह रहा है।",
            "ब्लॉक {block} में पानी का दबाव बहुत कम है, दैनिक कार्य बाधित हो रहे हैं।",
            "गर्मी के कारण {area} क्षेत्र में गंभीर जल संकट है, तुरंत टैंकर भेजा जाए।"
        ],
        "Sanitation & Garbage": [
            "{street} के पास खुले कचरा डिब्बे से कूड़ा सड़क पर फैल रहा है। अविलंब सफाई कराएं।",
            "{area} में स्कूल के पास पिछले एक हफ्ते से कचरा नहीं उठाया गया है।",
            "वार्ड {ward} में मुख्य सड़क पर नाला ओवरफ्लो हो रहा है, जिससे दुर्गंध फैल रही है।",
            "{area} बाजार के पास मृत मवेशी पड़ा है, अत्यंत दुर्गंध आ रही है।",
            "बस स्टैंड के पास सार्वजनिक शौचालय पूरी तरह से जाम और गंदगी से भरा है।"
        ],
        "Roads & Potholes": [
            "{street} हाईवे पर बड़ा गड्ढा होने से दुर्घटनाएं हो रही हैं और जाम लग रहा है।",
            "ब्लॉक {block} में सड़क का निर्माण आधा-अधूरा छोड़ दिया गया है, खुला खड्डा खतरनाक है।",
            "{area} फ्लाई-ओवर के पास स्ट्रीट लाइट बंद है, रात में आवाजाही असुरक्षित है।",
            "अस्पताल के रास्ते में अवैध स्पीड ब्रेकर के कारण मरीजों को असुविधा हो रही है।",
            "बाजार के पास फुटपाथ टूट चुका है, बुजुर्गों को पैदल चलने में दिक्कत हो रही है।"
        ],
        "Electricity & Power Cut": [
            "ब्लॉक {block} में ट्रांसफार्मर में शॉर्ट सर्किट हुआ और बिजली 12 घंटे से ठप है।",
            "वार्ड {ward} में लो वोल्टेज के कारण घर के बिजली उपकरण खराब हो रहे हैं।",
            "{area} पार्क के पास हाई टेंशन बिजली का तार नीचा लटक रहा है, बड़ा खतरा है।",
            "भीषण गर्मी में 8 घंटे से लगातार बिजली कटौती हो रही है, जनता बेहाल है।",
            "{street} पर बिजली का खंभा आंधी के बाद खतरनाक तरीके से झुक गया है।"
        ],
        "Public Healthcare & Clinics": [
            "{area} प्राथमिक स्वास्थ्य केंद्र में जरूरी दवाएं और आपातकालीन टीके उपलब्ध नहीं हैं।",
            "वार्ड {ward} के सरकारी अस्पताल में ड्यूटी के समय डॉक्टर अनुपस्थित रहते हैं।",
            "सिविल अस्पताल में बुजुर्ग मरीजों के लिए व्हीलचेयर और स्ट्रैचर की सुविधा नहीं है।",
            "{area} के सरकारी अस्पताल के वार्डों में गंदगी का माहौल है, सफाई नहीं होती।",
            "आपातकालीन मरीज के लिए एम्बुलेंस 1 घंटे से अधिक देरी से पहुंची।"
        ]
    },
    "ta": {
        "Water Supply & Quality": [
            "வார்டு {ward} பகுதியில் கடந்த 3 நாட்களாக குடிநீர் விநியோகம் முற்றிலும் நிறுத்தப்பட்டுள்ளது.",
            "{street} பகுதியில் உள்ள நகராட்சி குழாயில் சாக்கடை கலந்து துர்நாற்றத்துடன் தண்ணீர் வருகிறது.",
            "{street} சந்திப்பு அருகே பிரதான குடிநீர் குழாய் உடைந்து பல்லாயிரம் லிட்டர் நீர் வீணாகிறது.",
            "பிளாக் {block} பகுதியில் தண்ணீர் அழுத்தம் மிகவும் குறைவாக வருகிறது.",
            "{area} பகுதியில் கடுமையான தண்ணீர் தட்டுப்பாடு ஏற்பட்டுள்ளதால் உடனடியாக லாரி தண்ணீர் தேவை."
        ],
        "Sanitation & Garbage": [
            "{street} தெருவில் உள்ள குப்பை தொட்டி நிரம்பி வழிந்து சாலையில் குப்பைகள் சிதறியுள்ளன.",
            "{area} பள்ளி அருகே ஒரு வாரமாக நகராட்சி ஊழியர்கள் குப்பை அள்ளவில்லை.",
            "வார்டு {ward} பிரதான சாலையில் திறந்தவெளி கழிவுநீர் கால்வாய் பொங்கி வழிகிறது.",
            "{area} சந்தை பகுதியில் இறந்துபோன விலங்கு கிடப்பதால் கடுமையான துர்நாற்றம் வீசுகிறது.",
            "பேருந்து நிலையம் அருகிலுள்ள பொது கழிப்பறை அடைபட்டு பயன்படுத்த முடியாத நிலையில் உள்ளது."
        ],
        "Roads & Potholes": [
            "{street} பிரதான சாலையில் பெரிய பள்ளம் உள்ளதால் அடிக்கடி விபத்துகள் மற்றும் போக்குவரத்து நெரிசல் ஏற்படுகிறது.",
            "பிளாக் {block} பகுதியில் சாலை பணி அரைகுறையாக நிறுத்தப்பட்டு ஆபத்தான பள்ளம் தோண்டப்பட்டுள்ளது.",
            "{area} மேம்பாலம் அருகே தெருவிளக்குகள் எரியாததால் இரவு நேரத்தில் செல்வது ஆபத்தாக உள்ளது.",
            "மருத்துவமனை சாலையில் முறையான வெள்ளை கோடு இன்றி அமைக்கப்பட்ட வேகத்தடை ஆபத்தானது.",
            "சந்தை அருகில் நடைபாதை முற்றிலும் சேதமடைந்துள்ளதால் முதியவர்கள் நடக்க சிரமப்படுகின்றனர்."
        ],
        "Electricity & Power Cut": [
            "பிளாக் {block} பகுதியில் மின்மாற்றி வெடித்து சிதறியதால் கடந்த 12 மணி நேரமாக மின்சாரம் இல்லை.",
            "வார்டு {ward} பகுதியில் அடிக்கடி ஏற்படும் குறைந்த மின் அழுத்தம் (Low Voltage) காரணமாக மின் சாதனங்கள் பழுதாகின்றன.",
            "{area} பூங்கா அருகில் உயர் மின்னழுத்த கம்பி மிகவும் தாழ்வாக தொங்குகிறது.",
            "கடும் வெயிலில் 8 மணி நேரத்திற்கு மேலாக தொடர் மின்வெட்டு ஏற்பட்டு மக்கள் அவதிப்படுகின்றனர்.",
            "{street} தெருவில் உள்ள மின்கம்பம் சாய்ந்து விழும் ஆபத்தான நிலையில் உள்ளது."
        ]
    },
    "Public Healthcare & Clinics": {
        "ta": [
            "{area} ஆரம்ப சுகாதார நிலையத்தில் அவசியமான அவசர மருந்துகள் மற்றும் தடுப்பூசிகள் இல்லை.",
            "வார்டு {ward} நகராட்சி மருத்துவமனையில் வேலை நேரத்தில் மருத்துவர்கள் இருப்பதில்லை.",
            "அரசு மருத்துவமனையில் முதியவர்களுக்கான சக்கர நாற்காலி மற்றும் ஸ்ட்ரெச்சர் வசதி இல்லை.",
            "{area} அரசு மருத்துவமனை வார்டுகளில் சுகாதாரம் மிகவும் மோசமாக உள்ளது.",
            "அவசர நோயாளிக்கு ஆம்புலன்ஸ் வர ஒரு மணி நேரத்திற்கும் மேலாக தாமதமானது."
        ]
    }
}

# Fix Tamil Healthcare templates nested dict structure
TEMPLATES["ta"]["Public Healthcare & Clinics"] = [
    "{area} ஆரம்ப சுகாதார நிலையத்தில் அவசியமான அவசர மருந்துகள் மற்றும் தடுப்பூசிகள் இல்லை.",
    "வார்டு {ward} நகராட்சி மருத்துவமனையில் வேலை நேரத்தில் மருத்துவர்கள் இருப்பதில்லை.",
    "அரசு மருத்துவமனையில் முதியவர்களுக்கான சக்கர நாற்காலி மற்றும் ஸ்ட்ரெச்சர் வசதி இல்லை.",
    "{area} அரசு மருத்துவமனை வார்டுகளில் சுகாதாரம் மிகவும் மோசமாக உள்ளது.",
    "அவசர நோயாளிக்கு ஆம்புலன்ஸ் வர ஒரு மணி நேரத்திற்கும் மேலாக தாமதமானது."
]

AREAS = ["Raja Nagar", "Gandhi Chowk", "Anna Nagar", "Shanti Vihar", "Subhash Market", "Nehru Enclave"]
STREETS = ["MG Road", "Station Road", "Ring Road", "Church Street", "Main Bazaar"]

def generate_synthetic_dataset(num_samples_per_cat_lang: int = 50) -> List[Dict]:
    """Generates synthetic complaints balance-sampled across language and category."""
    records = []
    
    for lang in ["en", "hi", "ta"]:
        for category in CATEGORIES:
            templates = TEMPLATES[lang][category]
            for i in range(num_samples_per_cat_lang):
                template = random.choice(templates)
                text = template.format(
                    ward=random.randint(1, 45),
                    street=random.choice(STREETS),
                    block=chr(65 + random.randint(0, 5)),
                    area=random.choice(AREAS)
                )
                
                # Determine initial priority heuristic
                text_lower = text.lower()
                is_critical = any(kw in text_lower for kw in ["burst", "explode", "bleeding", "hazard", "फट गया", "अस्पताल", "ஆபத்து", "வெடித்து"])
                is_high = any(kw in text_lower for kw in ["no water", "12 hours", "foul", "गंदा", "12 घंटे", "மின்சாரம் இல்லை"])
                
                if is_critical:
                    priority = "Critical"
                elif is_high:
                    priority = "High"
                elif random.random() > 0.5:
                    priority = "Medium"
                else:
                    priority = "Low"

                item = {
                    "id": str(uuid.uuid4())[:8],
                    "text": text,
                    "language": lang,
                    "category": category,
                    "priority": priority,
                    "area": random.choice(AREAS),
                    "days_open": random.randint(0, 14)
                }
                records.append(item)
                
    # Introduce ~10% duplicate complaints with minor rephrasing or identical content
    num_duplicates = int(len(records) * 0.1)
    for _ in range(num_duplicates):
        original = random.choice(records)
        duplicate = dict(original)
        duplicate["id"] = str(uuid.uuid4())[:8]
        duplicate["text"] = "URGENT: " + original["text"] if original["language"] == "en" else "आपातकालीन: " + original["text"]
        duplicate["is_duplicate_of"] = original["id"]
        records.append(duplicate)
        
    random.shuffle(records)
    return records


def train_val_test_split(dataset: List[Dict], train_ratio=0.7, val_ratio=0.15) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Splits dataset ensuring balanced language representation in test set."""
    train, val, test = [], [], []
    
    # Group by language to guarantee balanced language splits
    lang_groups = {}
    for item in dataset:
        lang = item["language"]
        lang_groups.setdefault(lang, []).append(item)
        
    for lang, items in lang_groups.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        train.extend(items[:n_train])
        val.extend(items[n_train:n_train + n_val])
        test.extend(items[n_train + n_val:])
        
    return train, val, test


def save_dataset(num_samples_per_cat_lang: int = 50):
    """Generates and saves the datasets to JSON files."""
    data = generate_synthetic_dataset(num_samples_per_cat_lang)
    train, val, test = train_val_test_split(data)
    
    with open(DATA_DIR / "dataset_full.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    with open(DATA_DIR / "train.json", "w", encoding="utf-8") as f:
        json.dump(train, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "val.json", "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "test.json", "w", encoding="utf-8") as f:
        json.dump(test, f, ensure_ascii=False, indent=2)
        
    print(f"Dataset generated successfully!")
    print(f"Total: {len(data)} | Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    return data, train, val, test


if __name__ == "__main__":
    save_dataset(50)
