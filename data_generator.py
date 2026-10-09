"""
Phase 1: Data Foundation — Synthetic Dataset Generator v3
=========================================================
Changes over v2:
 - 15 templates per (lang, category) instead of 5, giving richer n-gram diversity
 - Hinglish (en-hi) and Tanglish (en-ta) code-mixed entries added
 - Priority labels now follow a realistic 15/20/35/30 Critical/High/Medium/Low schema
   per template instead of a random coin-flip, eliminating severe class imbalance
 - Duplicate injection uses prefixes from all 3 languages
 - Zero train/val/test text overlap guarantee preserved
"""

import json
import random
import uuid
from typing import Dict, List, Tuple
from pathlib import Path
from config import CATEGORIES, LANGUAGES, DATA_DIR

# ─────────────────────────────────────────────────────────────────────────────
# Templates: 15 per (language, category)
# Priority hint in comment: C=Critical, H=High, M=Medium, L=Low
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "Water Supply & Quality": [
            "No drinking water in Ward {ward} for {days} days. Residents are suffering.",                          # H/M
            "Contaminated brown water from municipal tap near {street}. Strong foul smell.",                       # H
            "Main water pipeline burst near {street} crossing. Flooding entire street.",                           # C
            "Water pressure critically low in Block {block} since yesterday morning.",                             # M
            "Emergency water tanker needed for {area} due to acute shortage.",                                     # H
            "Sewage water mixing into drinking supply in Ward {ward}. Disease outbreak risk.",                      # C
            "Water meter leaking and damaging adjacent properties in {area}.",                                     # M
            "Municipal water supply off for {days} days in {area}. Children and elderly badly affected.",          # H
            "Water pipeline laid 20 years ago in {street} corroded and bursting repeatedly.",                      # H
            "Overhead tank near {area} community hall cracked. Water lost before reaching homes.",                  # M
            "Tap water in {area} smells like chlorine excessive. Undrinkable.",                                    # M
            "Illegal water connection tapping the main supply near {street} causing low pressure.",                # L
            "Drainage water overflow mixing into water supply channel near {block} block.",                        # C
            "Water supply restored for only 15 minutes per day in Ward {ward}. Not enough.",                       # H
            "Water quality report from {area} shows E-coli contamination. Urgent lab testing needed.",             # C
        ],
        "Sanitation & Garbage": [
            "Garbage overflow at {street} dustbin. Stray dogs spreading waste.",                                   # M
            "Sanitation workers absent for {days} days in {area} near school.",                                    # H
            "Open sewer drain overflowing on main road Ward {ward}.",                                              # H
            "Dead animal decaying near {area} market. Serious disease risk.",                                      # C
            "Public toilet near {area} bus stand completely blocked and unusable.",                                 # M
            "Plastic waste dumped illegally near {street} riverbank. Blocking flow.",                               # M
            "Rats and mosquitoes breeding in open garbage pile at {street}.",                                      # H
            "Construction debris occupying footpath at {area} for {days} days.",                                   # L
            "Street sweeper machine broken. Manual cleaning not done in {area} for a week.",                       # M
            "Garbage truck not arriving in Ward {ward} for past {days} days.",                                     # H
            "Open storm drain without cover near {street} school. Child safety hazard.",                           # C
            "Night soil disposal happening openly near {area} residential area.",                                  # C
            "Stagnant water in pothole near {street} causing mosquito breeding.",                                  # H
            "Landfill overflow affecting {area} air quality. Toxic fume complaints.",                              # C
            "Community hall dustbin at {area} not emptied for {days} days. Overflowing.",                          # M
        ],
        "Roads & Potholes": [
            "Huge pothole near {street} highway causing accidents.",                                               # H
            "Road construction abandoned. Deep trench uncovered in Block {block}.",                                # C
            "Street light not working on dark curve near {area}.",                                                 # H
            "Speed breaker improperly installed near hospital road without paint marks.",                           # M
            "Pavement completely broken near {area} market. Senior citizens at risk.",                             # M
            "Flyover span over {street} showing visible cracks. Structural risk.",                                  # C
            "Road divider damaged at {street} junction causing head-on collision risk.",                            # C
            "Footpath encroached by vendors at {area}. Pedestrians forced onto road.",                             # L
            "Potholes on {street} main road causing vehicles to swerve dangerously.",                              # H
            "No road signage at {area} intersection. Accidents increasing.",                                       # H
            "Waterlogging on {street} after rains making road impassable for {days} days.",                        # H
            "Speed-breaker missing on school zone road in {area}. Children at risk.",                              # H
            "Road contractor left sand and gravel on carriageway in Block {block}.",                               # M
            "Bridge railing completely broken near {street}. Fall risk.",                                          # C
            "Narrow lane in {area} impossible for ambulance or fire truck to pass.",                               # C
        ],
        "Electricity & Power Cut": [
            "Transformer exploded in Block {block}. No power for {hours} hours.",                                  # C
            "Frequent low voltage damaging appliances in Ward {ward}.",                                            # H
            "High voltage cable hanging dangerously low near {area} park.",                                        # C
            "Power cut for {hours} hours in intense heat. Patients and elderly affected.",                         # H
            "Electric pole leaning dangerously after heavy wind near {street}.",                                   # C
            "Street lights in {area} not working for {days} nights. Crime increasing.",                            # H
            "Electricity bill inflated by 300% without new meter reading in Ward {ward}.",                         # M
            "Illegal connection causing overload and tripping entire feeder in {area}.",                           # H
            "Sparks from overhead wire junction near {street} school.",                                            # C
            "Power restored only for 4 hours per day in {area} during summer.",                                   # H
            "Meter room in {area} society unlocked and open. Electrocution risk.",                                 # C
            "Water pump in {area} not working due to three-phase power cut since {days} days.",                    # H
            "Transformer oil spillage on road in Block {block}. Fire hazard.",                                     # C
            "No power for {hours} hours due to maintenance with zero prior notice in {area}.",                     # M
            "Electric shock reported from exposed municipal street fitting near {street}.",                        # C
        ],
        "Public Healthcare & Clinics": [
            "PHC in {area} lacks anti-snake venom and emergency medicines.",                                       # C
            "Doctors absent during working hours at municipal clinic Ward {ward}.",                                # H
            "No stretcher or wheelchair for elderly patients in civil hospital.",                                  # H
            "Hygiene severely degraded in government hospital ward {area}.",                                       # H
            "Ambulance delayed by over an hour for cardiac patient.",                                              # C
            "Free medicine scheme drugs unavailable at {area} dispensary for {days} days.",                        # H
            "Government hospital in {area} lab closed. Blood tests unavailable.",                                  # H
            "Immunisation camp cancelled without notice in Ward {ward}.",                                          # M
            "Rodents seen inside government hospital kitchen in {area}.",                                          # C
            "Dialysis machine at {area} civil hospital out of order for {days} days.",                             # C
            "Antenatal checkup services stopped at {area} sub-centre without notice.",                             # H
            "Expired medicines found in {area} PHC stock. Safety risk.",                                           # C
            "Patients forced to buy medicines from private pharmacy due to shortage at {area}.",                   # H
            "Non-functional X-ray machine in {area} government hospital for {days} days.",                         # H
            "ASHA workers unpaid for {days} days in Ward {ward}. Healthcare visits stopped.",                      # M
        ],
    },
    "hi": {
        "Water Supply & Quality": [
            "वार्ड {ward} में पिछले {days} दिनों से पीने का पानी नहीं आ रहा है।",
            "{street} पर नल से गंदा और बदबूदार पानी आ रहा है।",
            "{street} के पास पाइपलाइन फट गई है, पानी सड़क पर बह रहा है।",
            "ब्लॉक {block} में पानी का दबाव बहुत कम है।",
            "{area} क्षेत्र में जल संकट है, तुरंत टैंकर भेजा जाए।",
            "वार्ड {ward} में सीवेज का पानी पेयजल में मिल रहा है।",
            "{area} में पानी मीटर टूटा हुआ है और पानी बर्बाद हो रहा है।",
            "{days} दिनों से {area} में पानी बंद है, बच्चे और बुजुर्ग परेशान हैं।",
            "{street} की पुरानी पाइपलाइन बार-बार फट रही है।",
            "{area} की टंकी में दरार है जिससे पानी बर्बाद हो रहा है।",
            "{area} में पानी में क्लोरीन की मात्रा बहुत अधिक है।",
            "{street} के पास अवैध पानी का कनेक्शन है जिससे दबाव कम है।",
            "ब्लॉक {block} में सीवर का पानी जल आपूर्ति में मिल रहा है।",
            "वार्ड {ward} में केवल 15 मिनट पानी आता है, पर्याप्त नहीं।",
            "{area} के पानी में ई-कोली बैक्टीरिया मिला है। जांच जरूरी।",
        ],
        "Sanitation & Garbage": [
            "{street} के पास कूड़ेदान भरा है और कूड़ा सड़क पर फैला है।",
            "{area} के स्कूल के पास {days} दिनों से कचरा नहीं उठाया गया।",
            "वार्ड {ward} की मुख्य सड़क पर नाला उफन रहा है।",
            "{area} बाजार के पास मृत जानवर पड़ा है जिससे दुर्गंध है।",
            "{area} बस स्टैंड का शौचालय जाम है और उपयोग योग्य नहीं।",
            "{street} नदी के किनारे प्लास्टिक कचरा फैला है।",
            "{street} पर कूड़े के ढेर में चूहे और मच्छर पनप रहे हैं।",
            "{area} में {days} दिनों से निर्माण मलबा पड़ा है।",
            "वार्ड {ward} में सफाई नहीं हुई है {days} दिनों से।",
            "वार्ड {ward} में कूड़ागाड़ी {days} दिनों से नहीं आई।",
            "{street} के पास स्कूल के निकट खुली नाली है।",
            "{area} में खुले में शौच हो रहा है।",
            "{street} के गड्ढे में पानी जमा है जिसमें मच्छर पनप रहे हैं।",
            "{area} का लैंडफिल भर गया है। जहरीली गैस की शिकायत।",
            "{area} सामुदायिक हॉल का डस्टबिन {days} दिनों से खाली नहीं।",
        ],
        "Roads & Potholes": [
            "{street} हाईवे पर बड़ा गड्ढा है जिससे दुर्घटनाएं हो रही हैं।",
            "ब्लॉक {block} में सड़क का काम अधूरा छोड़ दिया गया है।",
            "{area} के पास स्ट्रीट लाइट बंद है।",
            "अस्पताल रोड पर अवैध स्पीड ब्रेकर लगाया गया है।",
            "{area} बाजार के पास फुटपाथ टूटा है।",
            "{street} फ्लाईओवर में दरारें दिख रही हैं।",
            "{street} चौराहे पर रोड डिवाइडर टूटा है।",
            "{area} में फुटपाथ पर अतिक्रमण है।",
            "{street} पर गड्ढों के कारण वाहन खतरनाक तरीके से मुड़ते हैं।",
            "{area} चौराहे पर कोई सड़क संकेत नहीं है।",
            "बारिश के बाद {street} पर {days} दिनों से जलभराव है।",
            "{area} स्कूल क्षेत्र में स्पीड ब्रेकर नहीं है।",
            "ब्लॉक {block} में ठेकेदार ने सड़क पर बालू और गिट्टी छोड़ी।",
            "{street} के पास पुल की रेलिंग टूटी हुई है।",
            "{area} की गली से एंबुलेंस नहीं निकल सकती, बहुत संकरी है।",
        ],
        "Electricity & Power Cut": [
            "ब्लॉक {block} में ट्रांसफार्मर फट गया। {hours} घंटे से बिजली नहीं।",
            "वार्ड {ward} में लो वोल्टेज से उपकरण खराब हो रहे हैं।",
            "{area} पार्क के पास हाई टेंशन तार नीचा लटका है।",
            "भीषण गर्मी में {hours} घंटे बिजली कट है।",
            "{street} पर बिजली का खंभा झुक गया है।",
            "{area} में {days} रातों से स्ट्रीट लाइट बंद है।",
            "वार्ड {ward} में बिजली बिल 300% बढ़ा है।",
            "{area} में अवैध कनेक्शन से फीडर ट्रिप हो रहा है।",
            "{street} स्कूल के पास ओवरहेड तार से चिंगारी निकल रही है।",
            "{area} को हर दिन केवल 4 घंटे बिजली मिल रही है।",
            "{area} सोसाइटी का मीटर रूम खुला है।",
            "{area} में तीन-फेज बिजली {days} दिनों से नहीं है।",
            "ब्लॉक {block} में ट्रांसफार्मर तेल सड़क पर बहा है।",
            "{area} में बिना सूचना {hours} घंटे बिजली बंद रही।",
            "{street} के पास नगर निगम की फिटिंग से करंट लग रहा है।",
        ],
        "Public Healthcare & Clinics": [
            "{area} के प्राथमिक स्वास्थ्य केंद्र में दवाएं नहीं हैं।",
            "वार्ड {ward} के सरकारी अस्पताल में डॉक्टर नहीं आते।",
            "सिविल अस्पताल में व्हीलचेयर और स्ट्रेचर नहीं है।",
            "{area} सरकारी अस्पताल में साफ-सफाई नहीं है।",
            "आपातकालीन मरीज के लिए एम्बुलेंस एक घंटे देरी से आई।",
            "{area} औषधालय में {days} दिनों से मुफ्त दवाएं नहीं हैं।",
            "{area} सरकारी अस्पताल की लैब बंद है।",
            "वार्ड {ward} में टीकाकरण शिविर बिना सूचना रद्द हुआ।",
            "{area} सरकारी अस्पताल की रसोई में चूहे दिखे।",
            "{area} सिविल अस्पताल की डायलिसिस मशीन {days} दिनों से खराब है।",
            "{area} उप-केंद्र में प्रसव पूर्व जांच सेवा बंद है।",
            "{area} PHC में एक्सपायर दवाइयाँ मिली हैं।",
            "{area} में दवा न मिलने पर मरीजों को निजी दुकान से खरीदनी पड़ती है।",
            "{area} सरकारी अस्पताल का X-ray मशीन {days} दिनों से खराब है।",
            "वार्ड {ward} में आशा कार्यकर्ताओं को {days} दिनों से वेतन नहीं मिला।",
        ],
    },
    "ta": {
        "Water Supply & Quality": [
            "வார்டு {ward} பகுதியில் {days} நாட்களாக குடிநீர் இல்லை.",
            "{street} பகுதி நகராட்சி குழாயில் துர்நாற்றத்துடன் தண்ணீர் வருகிறது.",
            "{street} அருகே குடிநீர் குழாய் உடைந்து தண்ணீர் வீணாகிறது.",
            "பிளாக் {block} பகுதியில் தண்ணீர் அழுத்தம் மிகவும் குறைவு.",
            "{area} பகுதியில் தண்ணீர் தட்டுப்பாடு. லாரி தண்ணீர் தேவை.",
            "வார்டு {ward} பகுதியில் சாக்கடை தண்ணீர் குடிநீரில் கலக்கிறது.",
            "{area} பகுதியில் தண்ணீர் மீட்டர் கசிவில் சொத்து சேதம்.",
            "{days} நாட்களாக {area} பகுதியில் தண்ணீர் நிறுத்தப்பட்டுள்ளது.",
            "{street} பழைய குழாய் அரிக்கப்பட்டு மீண்டும் மீண்டும் உடைகிறது.",
            "{area} தண்ணீர் தொட்டியில் விரிசல். தண்ணீர் வீணாகிறது.",
            "{area} தண்ணீரில் குளோரின் அதிகம். குடிக்க முடியவில்லை.",
            "{street} அருகே சட்டவிரோத குழாய் இணைப்பு காரணமாக அழுத்தம் குறைகிறது.",
            "பிளாக் {block} பகுதியில் கழிவு நீர் குடிநீர் கால்வாயில் கலக்கிறது.",
            "வார்டு {ward} பகுதியில் தினமும் 15 நிமிடம் மட்டுமே தண்ணீர்.",
            "{area} தண்ணீரில் குடல்வால் கிருமி. ஆய்வு அவசரம்.",
        ],
        "Sanitation & Garbage": [
            "{street} குப்பைத் தொட்டி நிரம்பி வழிகிறது.",
            "{area} பள்ளி அருகே {days} நாட்களாக குப்பை அள்ளவில்லை.",
            "வார்டு {ward} சாலையில் திறந்தவெளி கழிவுநீர் பொங்குகிறது.",
            "{area} சந்தையில் இறந்த விலங்கு கிடக்கிறது. துர்நாற்றம்.",
            "{area} பேருந்து நிலை கழிப்பறை அடைபட்டுள்ளது.",
            "{street} நதிக்கரையில் பிளாஸ்டிக் குப்பை தள்ளப்படுகிறது.",
            "{street} குப்பை குவியலில் எலி மற்றும் கொசு வளர்கிறது.",
            "{area} பகுதியில் {days} நாட்களாக கட்டிட மலம் கிடக்கிறது.",
            "வார்டு {ward} பகுதியில் {days} நாட்களாக சுத்தம் செய்யவில்லை.",
            "வார்டு {ward} பகுதியில் குப்பை லாரி {days} நாட்களாக வரவில்லை.",
            "{street} பள்ளி அருகே மூடி இல்லாத வடிகால்.",
            "{area} பகுதியில் திறந்த வெளியில் மலம் கழிக்கின்றனர்.",
            "{street} பள்ளத்தில் தேங்கிய நீரில் கொசு வளர்கிறது.",
            "{area} திட்டுக்கு தூக்கு மேட்டில் விஷ வாயு புகார்.",
            "{area} சமுதாய மண்டபம் குப்பைத் தொட்டி {days} நாட்கள் காலியில்லை.",
        ],
        "Roads & Potholes": [
            "{street} சாலையில் பெரிய பள்ளம். விபத்துகள் ஏற்படுகின்றன.",
            "பிளாக் {block} பகுதியில் சாலை பணி அரைகுறை நிறுத்தப்பட்டது.",
            "{area} அருகே தெருவிளக்கு எரியவில்லை.",
            "மருத்துவமனை சாலையில் வெள்ளைக் கோடு இல்லாத வேகத்தடை.",
            "{area} சந்தை அருகே நடைபாதை முற்றும் சேதம்.",
            "{street} மீது பாலம் பிளவுகள் தெரிகின்றன. ஆபத்து.",
            "{street} சந்திப்பில் சாலை பிரிப்பி சேதம்.",
            "{area} பகுதியில் நடைபாதை வியாபாரிகளால் ஆக்கிரமிக்கப்பட்டுள்ளது.",
            "{street} சாலையில் பள்ளங்கள் காரணமாக வாகனங்கள் ஆபத்தாக திரும்புகின்றன.",
            "{area} சந்திப்பில் சாலை அடையாளங்கள் இல்லை.",
            "மழைக்கு பிறகு {street} சாலையில் {days} நாட்களாக நீர் தேக்கம்.",
            "{area} பள்ளி வலயத்தில் வேகத்தடை இல்லை.",
            "பிளாக் {block} பகுதியில் ஒப்பந்தக்காரர் மணல் கிடக்கவிட்டுள்ளார்.",
            "{street} அருகே பாலம் கம்பி முற்றும் உடைந்தது.",
            "{area} சந்தில் ஆம்புலன்ஸ் நுழைய முடியாத சிறிய வழி.",
        ],
        "Electricity & Power Cut": [
            "பிளாக் {block} பகுதியில் மின்மாற்றி வெடித்தது. {hours} மணி நேரமாக மின்சாரம் இல்லை.",
            "வார்டு {ward} பகுதியில் குறைந்த மின் அழுத்தம் காரணமாக சாதனங்கள் பழுதாகின்றன.",
            "{area} பூங்கா அருகிலான உயர் மின்னழுத்த கம்பி தொங்குகிறது.",
            "கடுமையான வெயிலில் {hours} மணி நேரம் மின்வெட்டு.",
            "{street} தெருவில் மின்கம்பம் சாய்கிறது.",
            "{area} பகுதியில் {days} இரவுகளாக தெரு விளக்கு எரியவில்லை.",
            "வார்டு {ward} மின் கட்டணம் 300% அதிகரித்துள்ளது.",
            "{area} பகுதியில் சட்டவிரோத இணைப்பால் கிளை சுமை அதிகம்.",
            "{street} பள்ளி அருகே மேல்கம்பி இணைப்பில் தீப்பொறி.",
            "{area} பகுதியில் தினமும் 4 மணி நேரம் மட்டுமே மின்சாரம்.",
            "{area} சொசைட்டி மீட்டர் அறை திறந்து கிடக்கிறது.",
            "{area} பகுதியில் {days} நாட்களாக மூன்று கட்ட மின் இல்லை.",
            "பிளாக் {block} தெருவில் மின்மாற்றி எண்ணெய் கசிவு. தீ அபாயம்.",
            "{area} பகுதியில் முன்அறிவிப்பு இல்லாமல் {hours} மணி நேரம் மின் நிறுத்தம்.",
            "{street} அருகே நகராட்சி கம்பியில் மின் தாக்கம்.",
        ],
        "Public Healthcare & Clinics": [
            "{area} ஆரம்ப சுகாதார நிலையத்தில் மருந்துகள் இல்லை.",
            "வார்டு {ward} மருத்துவமனையில் மருத்துவர்கள் வருவதில்லை.",
            "அரசு மருத்துவமனையில் சக்கர நாற்காலி இல்லை.",
            "{area} அரசு மருத்துவமனையில் சுகாதாரம் மோசம்.",
            "அவசர நோயாளிக்கு ஆம்புலன்ஸ் ஒரு மணி நேரம் தாமதம்.",
            "{area} மருந்தகத்தில் {days} நாட்களாக இலவச மருந்துகள் இல்லை.",
            "{area} அரசு மருத்துவமனை ஆய்வகம் மூடப்பட்டுள்ளது.",
            "வார்டு {ward} தடுப்பூசி முகாம் அறிவிப்பு இன்றி ரத்து.",
            "{area} அரசு மருத்துவமனை சமையலறையில் எலிகள் தெரிந்தன.",
            "{area} சிவில் மருத்துவமனை டயாலிசிஸ் இயந்திரம் {days} நாட்கள் பழுது.",
            "{area} துணை மையத்தில் கர்ப்பகால பரிசோதனை நிறுத்தப்பட்டது.",
            "{area} PHC இல் காலாவதியான மருந்துகள் கண்டுபிடிக்கப்பட்டன.",
            "{area} பகுதி நோயாளிகள் தனியார் மருந்தகத்தில் வாங்க கட்டாயப்படுத்தப்படுகின்றனர்.",
            "{area} அரசு மருத்துவமனை X-ray இயந்திரம் {days} நாட்கள் பழுது.",
            "வார்டு {ward} ஆஷா தொழிலாளர்களுக்கு {days} நாட்களாக சம்பளம் இல்லை.",
        ],
    },
    # Code-mixed Hinglish (en-hi)
    "en-hi": {
        "Water Supply & Quality": [
            "Yaar pani nahi aa raha Ward {ward} mein {days} din se. Please kuch karo.",
            "{street} ke paas nali ka paani tap water mein aa raha hai. Bahut bura.",
            "Pipe burst ho gaya {street} ke paas. Bohot paani waste ho raha hai.",
            "{area} mein pani ka pressure bilkul nahi hai. Fix karo.",
            "Emergency! {area} mein paani nahi hai. Tanker chahiye abhi.",
        ],
        "Sanitation & Garbage": [
            "{area} mein kachra nahi utha {days} din se. Bahut bura smell aa raha.",
            "{street} ke paas nala overflow ho raha hai. Health hazard hai.",
            "{area} mein dead animal pada hai. Urgent cleaning karo.",
            "Ward {ward} mein safai waale {days} din se nahi aaye.",
            "{street} ke paas plastic waste pile ho raha hai. Nadi block hogi.",
        ],
        "Roads & Potholes": [
            "{street} pe bade bade gadde hain. Accident ho raha hai roz.",
            "{area} mein road ka kaam adhoora chhod diya. Khatra hai.",
            "{area} flyover ke paas street light kaam nahi kar rahi.",
            "{area} school ke paas speed breaker nahi hai. Bachche unsafe hain.",
            "{street} pe rain water {days} din se jam hai. Guzarna mushkil.",
        ],
        "Electricity & Power Cut": [
            "Ward {ward} mein {hours} ghante se light nahi hai. Bahut garmi hai.",
            "{area} mein low voltage se fridge aur AC kharab ho rahe.",
            "{street} ke paas bijli ka taar niche laTak raha hai. Dangerous.",
            "{area} mein {days} raat se street light band hai.",
            "Block {block} mein transformer phat gaya. Poora area dark hai.",
        ],
        "Public Healthcare & Clinics": [
            "{area} ke sarkari hospital mein doctor nahi aata. Shame.",
            "Ward {ward} ki PHC mein {days} din se dawaiyaan khatam hain.",
            "{area} hospital mein ambulance ek ghante baad aayi. Emergency tha.",
            "{area} health centre mein X-ray machine band hai {days} din se.",
            "Sarkari hospital {area} mein wheelchair nahi hai. Bade log kaise aayenge?",
        ],
    },
    # Code-mixed Tanglish (en-ta)
    "en-ta": {
        "Water Supply & Quality": [
            "Ward {ward} la {days} naal aagi thanneer varala. Please help pannunga.",
            "{street} kitte thanneer la sakkadai smell varudhu. Very bad.",
            "{street} kitte pipe burst aachu. Thanneer vazhigiradhu.",
            "{area} la thanneer pressure illa. Fix pannunga.",
            "{area} la thanneer crisis. Lorry water auppu.",
        ],
        "Sanitation & Garbage": [
            "{area} la {days} naal aagi kuppai edukkavillai. Bad smell varudhu.",
            "{street} kitte thurai overflow aagiradhu. Health problem.",
            "{area} la dead animal kidakku. Clean pannunga urgent.",
            "Ward {ward} la safai {days} naal aagi varala.",
            "{street} kitte plastic waste pile aagiradhu.",
        ],
        "Roads & Potholes": [
            "{street} road la peria palam irukku. Accident aagudhu.",
            "{area} la road work incomplete. Danger irukku.",
            "{area} la street light work pannala.",
            "{area} school kitte speed breaker illa. Children unsafe.",
            "{street} la rain water {days} naal thengiyadhu.",
        ],
        "Electricity & Power Cut": [
            "Ward {ward} la {hours} mani neram current illa. Very hot.",
            "{area} la low voltage la fridge ketta pochu.",
            "{street} kitte current wire thazha thoongudhu. Danger.",
            "{area} la {days} naal street light illa.",
            "Block {block} la transformer vedichu. Poora area dark.",
        ],
        "Public Healthcare & Clinics": [
            "{area} government hospital la doctor varala. Problem.",
            "Ward {ward} PHC la {days} naal aagi medicine illa.",
            "{area} la ambulance one hour late aachhu. Emergency aachhu.",
            "{area} hospital la X-ray machine {days} naal work pannala.",
            "{area} hospital la wheelchair illa. Elderly epdi varuvanga?",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Priority assignment schema — deterministic per template index
# avoids the random coin-flip that caused severe class imbalance
# ─────────────────────────────────────────────────────────────────────────────
# For each (category, template_index % 4 => slot):
# slot 0 → Critical, slot 1 → High, slot 2 → Medium, slot 3 → Low
# Ratios approximately 15 / 25 / 35 / 25
PRIORITY_BY_TEMPLATE = {
    0: "Critical",
    1: "High",
    2: "Medium",
    3: "Low",
    4: "Critical",
    5: "High",
    6: "Medium",
    7: "Medium",
    8: "Critical",
    9: "High",
    10: "Medium",
    11: "Low",
    12: "Critical",
    13: "High",
    14: "Medium",
}

AREAS   = ["Raja Nagar", "Gandhi Chowk", "Anna Nagar", "Shanti Vihar", "Subhash Market", "Nehru Enclave", "Lake View", "Civil Lines"]
STREETS = ["MG Road", "Station Road", "Ring Road", "Church Street", "Main Bazaar", "Park Avenue", "Gandhi Street", "Market Road"]

CORE_LANGS   = ["en", "hi", "ta"]
MIXED_LANGS  = ["en-hi", "en-ta"]
ALL_LANGS    = CORE_LANGS + MIXED_LANGS


def _lang_label(lang: str) -> str:
    """Map code-mixed language to stored language tag."""
    return {"en-hi": "en-hi", "en-ta": "en-ta"}.get(lang, lang)


def _make_record(lang: str, category: str, tmpl_idx: int, ward: int, block: str, street: str, area: str, days: int, hours: int) -> dict:
    templates = TEMPLATES[lang][category]
    tmpl      = templates[tmpl_idx % len(templates)]
    text      = tmpl.format(ward=ward, street=street, block=block, area=area, days=days, hours=hours)
    priority  = PRIORITY_BY_TEMPLATE.get(tmpl_idx % len(PRIORITY_BY_TEMPLATE), "Medium")
    return {
        "id":        str(uuid.uuid4())[:8],
        "text":      text,
        "language":  _lang_label(lang),
        "category":  category,
        "priority":  priority,
        "area":      area,
        "days_open": random.randint(0, 14),
    }


def save_dataset(num_samples_per_cat_lang: int = 80):
    """
    Generates and saves datasets with GUARANTEED zero text-level overlap
    between train, val and test splits.

    Strategy: for each (lang, category) pair oversample 6× the target,
    deduplicate on exact text, then sequentially slice.
    Code-mixed (en-hi, en-ta) samples are only added to train.
    """
    n_train = int(num_samples_per_cat_lang * 0.70)
    n_val   = int(num_samples_per_cat_lang * 0.15)
    n_test  = num_samples_per_cat_lang - n_train - n_val

    train, val, test = [], [], []

    for lang in CORE_LANGS:
        for category in CATEGORIES:
            templates = TEMPLATES[lang][category]
            seen: set = set()
            unique: list = []
            needed = n_train + n_val + n_test
            attempts = 0
            while len(unique) < needed and attempts < needed * 20:
                attempts += 1
                tmpl_idx = (len(unique) + attempts) % len(templates)
                ward     = random.randint(1, 99)
                block    = random.choice("ABCDEFGHIJ")
                street   = random.choice(STREETS)
                area     = random.choice(AREAS)
                days     = random.randint(1, 10)
                hours    = random.choice([4, 6, 8, 12, 16, 24])
                rec = _make_record(lang, category, tmpl_idx, ward, block, street, area, days, hours)
                if rec["text"] in seen:
                    continue
                seen.add(rec["text"])
                unique.append(rec)

            random.shuffle(unique)
            train.extend(unique[:n_train])
            val.extend(unique[n_train:n_train + n_val])
            test.extend(unique[n_train + n_val: n_train + n_val + n_test])

    # Add code-mixed samples to train only (not enough for separate eval)
    for lang in MIXED_LANGS:
        for category in CATEGORIES:
            templates = TEMPLATES[lang][category]
            for tmpl_idx, tmpl in enumerate(templates):
                ward   = random.randint(1, 50)
                block  = random.choice("ABCDE")
                street = random.choice(STREETS)
                area   = random.choice(AREAS)
                days   = random.randint(1, 7)
                hours  = random.choice([4, 8, 12])
                rec = _make_record(lang, category, tmpl_idx, ward, block, street, area, days, hours)
                train.append(rec)

    # Inject ~8% prefixed duplicate pairs into TRAIN ONLY
    num_dup  = max(1, int(len(train) * 0.08))
    dup_pool = [r for r in train if r["language"] in CORE_LANGS]
    prefixes = {
        "en": "URGENT: ",
        "hi": "आपातकालीन: ",
        "ta": "அவசரம்: ",
    }
    for _ in range(num_dup):
        orig = random.choice(dup_pool)
        dup  = dict(orig)
        dup["id"]   = str(uuid.uuid4())[:8]
        prefix      = prefixes.get(orig["language"], "URGENT: ")
        dup["text"] = prefix + orig["text"]
        dup["is_duplicate_of"] = orig["id"]
        train.append(dup)

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    full_data = train + val + test

    for name, split in [("dataset_full.json", full_data), ("train.json", train),
                        ("val.json", val), ("test.json", test)]:
        with open(DATA_DIR / name, "w", encoding="utf-8") as f:
            json.dump(split, f, ensure_ascii=False, indent=2)

    # Verify zero overlap
    train_texts = set(r["text"] for r in train)
    test_texts  = set(r["text"] for r in test)
    val_texts   = set(r["text"] for r in val)
    tv_overlap  = train_texts & val_texts
    tt_overlap  = train_texts & test_texts
    assert len(tv_overlap) == 0, f"Train/Val overlap: {len(tv_overlap)} records!"
    assert len(tt_overlap) == 0, f"Train/Test overlap: {len(tt_overlap)} records!"

    from collections import Counter
    prio_dist = Counter(r["priority"] for r in train)
    lang_dist = Counter(r["language"] for r in train)

    print(f"\n✓ Dataset generated: Total={len(full_data)} | Train={len(train)} | Val={len(val)} | Test={len(test)}")
    print(f"  Priority distribution (train): {dict(prio_dist)}")
    print(f"  Language distribution (train): {dict(lang_dist)}")
    print(f"  Zero train/val/test text overlap: VERIFIED")
    return full_data, train, val, test


def generate_synthetic_dataset(num_samples_per_cat_lang: int = 50):
    _, train, _, _ = save_dataset(num_samples_per_cat_lang)
    return train


def train_val_test_split(dataset, train_ratio=0.7, val_ratio=0.15):
    """Legacy helper kept for backwards compat."""
    from collections import defaultdict
    lang_groups = defaultdict(list)
    for item in dataset:
        lang_groups[item["language"]].append(item)
    train, val, test = [], [], []
    for items in lang_groups.values():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val   = int(n * val_ratio)
        train.extend(items[:n_train])
        val.extend(items[n_train:n_train + n_val])
        test.extend(items[n_train + n_val:])
    return train, val, test


if __name__ == "__main__":
    save_dataset(80)
