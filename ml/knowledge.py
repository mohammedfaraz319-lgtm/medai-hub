"""Medical knowledge base used to generate training data and to explain results.

IMPORTANT: this is an educational knowledge base written for a student project.
It is NOT a substitute for real clinical datasets or medical advice.
"""

# key -> (display label, synonyms used by the chatbot's free-text matcher)
SYMPTOMS = {
    "fever": ("Fever", ["fever", "temperature", "feverish"]),
    "high_fever": ("High fever", ["high fever", "very high temperature", "103", "104"]),
    "chills": ("Chills / shivering", ["chills", "shivering", "shivers", "rigors"]),
    "headache": ("Headache", ["headache", "head ache", "head pain", "head hurts"]),
    "severe_headache": ("Severe / throbbing headache", ["severe headache", "throbbing headache", "pounding headache", "migraine"]),
    "fatigue": ("Fatigue / weakness", ["fatigue", "tired", "tiredness", "weakness", "weak", "exhausted", "low energy"]),
    "cough": ("Cough", ["cough", "coughing"]),
    "dry_cough": ("Dry cough", ["dry cough"]),
    "productive_cough": ("Cough with phlegm", ["phlegm", "mucus", "productive cough", "coughing up", "sputum"]),
    "sore_throat": ("Sore throat", ["sore throat", "throat pain", "throat hurts", "scratchy throat"]),
    "runny_nose": ("Runny / blocked nose", ["runny nose", "blocked nose", "stuffy nose", "nasal congestion", "congestion"]),
    "sneezing": ("Sneezing", ["sneezing", "sneeze"]),
    "shortness_of_breath": ("Shortness of breath", ["shortness of breath", "breathless", "difficulty breathing", "hard to breathe", "breathing problem", "out of breath"]),
    "wheezing": ("Wheezing", ["wheezing", "wheeze", "whistling"]),
    "chest_pain": ("Chest pain / tightness", ["chest pain", "chest tightness", "tight chest", "pain in chest"]),
    "body_pain": ("Body / muscle aches", ["body pain", "body ache", "muscle pain", "muscle ache", "aching", "body aches"]),
    "joint_pain": ("Joint pain", ["joint pain", "joint ache", "joints hurt", "arthralgia"]),
    "nausea": ("Nausea", ["nausea", "nauseous", "queasy", "feel sick"]),
    "vomiting": ("Vomiting", ["vomiting", "vomit", "throwing up", "puking"]),
    "diarrhea": ("Diarrhea / loose stools", ["diarrhea", "diarrhoea", "loose stool", "loose motion", "loose motions"]),
    "abdominal_pain": ("Abdominal / stomach pain", ["abdominal pain", "stomach pain", "stomach ache", "belly pain", "tummy ache", "cramps"]),
    "loss_of_appetite": ("Loss of appetite", ["loss of appetite", "no appetite", "not hungry", "don't feel like eating"]),
    "rash": ("Skin rash", ["rash", "red spots", "skin rash"]),
    "itchy_skin": ("Itchy skin", ["itchy skin", "itching", "itchy", "skin itch"]),
    "itchy_eyes": ("Itchy / watery eyes", ["itchy eyes", "watery eyes", "red eyes", "eye itching"]),
    "loss_of_taste_smell": ("Loss of taste or smell", ["loss of taste", "loss of smell", "can't smell", "cannot smell", "can't taste", "no taste"]),
    "burning_urination": ("Burning while urinating", ["burning urination", "burning while urinating", "painful urination", "burning pee", "burning when i pee"]),
    "frequent_urination": ("Frequent urination", ["frequent urination", "urinating often", "peeing a lot", "urinate frequently"]),
    "increased_thirst": ("Excessive thirst", ["excessive thirst", "very thirsty", "increased thirst", "always thirsty"]),
    "blurred_vision": ("Blurred vision", ["blurred vision", "blurry vision", "vision blurry"]),
    "dizziness": ("Dizziness", ["dizziness", "dizzy", "lightheaded", "light headed", "giddy"]),
    "pale_skin": ("Pale skin", ["pale skin", "pale", "pallor"]),
    "yellow_skin": ("Yellow skin / eyes", ["yellow skin", "yellow eyes", "jaundice", "yellowish"]),
    "dark_urine": ("Dark urine", ["dark urine", "dark coloured urine", "tea coloured urine"]),
    "weight_loss": ("Unexplained weight loss", ["weight loss", "losing weight", "lost weight"]),
    "night_sweats": ("Night sweats", ["night sweats", "sweating at night"]),
    "sensitivity_to_light": ("Sensitivity to light", ["sensitivity to light", "light sensitivity", "photophobia", "light hurts"]),
    "heartburn": ("Heartburn / acid taste", ["heartburn", "acid reflux", "acidity", "sour taste", "burning chest after eating"]),
    "sweating": ("Excessive sweating", ["sweating", "sweaty", "excessive sweating"]),
    "pain_behind_eyes": ("Pain behind the eyes", ["pain behind eyes", "pain behind the eyes", "eye pain", "retro orbital"]),
    "blisters": ("Fluid-filled blisters", ["blisters", "blister", "fluid filled spots"]),
}

# disease -> metadata + {symptom: probability that a patient with this disease reports it}
DISEASES = {
    "Common Cold": {
        "specialist": "General Physician", "severity": "mild",
        "desc": "A mild viral infection of the nose and throat that usually clears up by itself within a week.",
        "precautions": ["Rest and drink plenty of warm fluids", "Gargle with warm salt water", "Use steam inhalation for congestion", "Wash hands often to avoid spreading it"],
        "symptoms": {"runny_nose": .9, "sneezing": .8, "sore_throat": .7, "cough": .6, "fever": .25, "headache": .3, "fatigue": .4},
    },
    "Influenza (Flu)": {
        "specialist": "General Physician", "severity": "moderate",
        "desc": "A contagious viral respiratory illness that causes sudden fever, aches and tiredness.",
        "precautions": ["Rest and stay hydrated", "Paracetamol for fever (as advised by a doctor)", "Isolate to avoid infecting others", "Consult a doctor if breathing becomes difficult"],
        "symptoms": {"high_fever": .6, "fever": .85, "chills": .6, "body_pain": .8, "fatigue": .8, "headache": .6, "dry_cough": .6, "sore_throat": .4, "runny_nose": .35},
    },
    "COVID-19 (suspected)": {
        "specialist": "General Physician / Pulmonologist", "severity": "moderate",
        "desc": "A viral respiratory illness. Loss of taste or smell is a typical distinguishing symptom. Testing is needed to confirm.",
        "precautions": ["Get tested (RT-PCR / rapid antigen)", "Isolate and wear a mask", "Monitor oxygen saturation", "Seek urgent care if breathless or SpO2 is low"],
        "symptoms": {"fever": .75, "dry_cough": .7, "loss_of_taste_smell": .65, "fatigue": .7, "body_pain": .5, "sore_throat": .45, "headache": .45, "shortness_of_breath": .3},
    },
    "Dengue Fever": {
        "specialist": "General Physician / Internal Medicine", "severity": "serious",
        "desc": "A mosquito-borne viral infection causing high fever, severe body pain and a drop in platelet count.",
        "precautions": ["Get a blood test (NS1 / platelet count) urgently", "Drink lots of fluids / ORS", "Avoid aspirin and ibuprofen", "Seek emergency care for bleeding, severe stomach pain or persistent vomiting"],
        "symptoms": {"high_fever": .85, "fever": .9, "pain_behind_eyes": .7, "joint_pain": .75, "body_pain": .8, "headache": .7, "rash": .45, "nausea": .5, "vomiting": .4, "fatigue": .6},
    },
    "Malaria": {
        "specialist": "General Physician / Infectious Disease", "severity": "serious",
        "desc": "A parasitic infection spread by mosquitoes, with cyclic fever, chills and sweating.",
        "precautions": ["Get a blood smear / rapid malaria test immediately", "Complete the full anti-malarial course", "Use mosquito nets and repellents", "Seek urgent care if confused or very weak"],
        "symptoms": {"high_fever": .7, "fever": .9, "chills": .9, "sweating": .75, "headache": .6, "nausea": .5, "vomiting": .4, "body_pain": .5, "fatigue": .6},
    },
    "Typhoid Fever": {
        "specialist": "General Physician", "severity": "serious",
        "desc": "A bacterial infection from contaminated food or water, causing prolonged fever and stomach problems.",
        "precautions": ["Get a blood culture / Widal test", "Drink only boiled or filtered water", "Complete the prescribed antibiotics", "Maintain strict hand hygiene"],
        "symptoms": {"fever": .95, "high_fever": .5, "abdominal_pain": .6, "headache": .55, "loss_of_appetite": .65, "fatigue": .65, "diarrhea": .35, "nausea": .4, "rash": .2},
    },
    "Gastroenteritis (Stomach Flu)": {
        "specialist": "General Physician / Gastroenterologist", "severity": "moderate",
        "desc": "Inflammation of the stomach and intestines, usually from infection or contaminated food.",
        "precautions": ["Sip ORS or clean fluids frequently", "Eat light foods (rice, banana, toast)", "Avoid dairy, spicy and oily food", "See a doctor if there is blood in stool or signs of dehydration"],
        "symptoms": {"diarrhea": .9, "vomiting": .75, "nausea": .8, "abdominal_pain": .8, "fever": .4, "fatigue": .5, "loss_of_appetite": .5},
    },
    "Migraine": {
        "specialist": "Neurologist", "severity": "moderate",
        "desc": "A neurological condition causing intense, often one-sided throbbing headaches.",
        "precautions": ["Rest in a dark, quiet room", "Stay hydrated and keep a regular sleep schedule", "Note and avoid personal triggers", "See a neurologist if attacks are frequent or sudden and severe"],
        "symptoms": {"severe_headache": .95, "headache": .8, "nausea": .65, "vomiting": .4, "sensitivity_to_light": .8, "dizziness": .35, "blurred_vision": .3},
    },
    "Hypertension (High Blood Pressure)": {
        "specialist": "Cardiologist / General Physician", "severity": "serious",
        "desc": "Persistently high blood pressure that often has no symptoms but raises the risk of heart attack and stroke.",
        "precautions": ["Check blood pressure regularly", "Reduce salt, stay active and manage stress", "Do not stop prescribed medicines suddenly", "Seek emergency help for chest pain or severe headache with confusion"],
        "symptoms": {"headache": .6, "dizziness": .55, "blurred_vision": .35, "chest_pain": .3, "shortness_of_breath": .3, "fatigue": .4},
    },
    "Type 2 Diabetes": {
        "specialist": "Endocrinologist / Diabetologist", "severity": "serious",
        "desc": "A long-term condition where the body cannot use insulin properly, leading to high blood sugar.",
        "precautions": ["Get fasting glucose and HbA1c tests", "Reduce sugar and refined carbohydrates", "Exercise at least 30 minutes most days", "Follow up with a diabetologist for a treatment plan"],
        "symptoms": {"increased_thirst": .9, "frequent_urination": .9, "fatigue": .7, "blurred_vision": .55, "weight_loss": .4, "itchy_skin": .3, "loss_of_appetite": .15},
    },
    "Bronchial Asthma": {
        "specialist": "Pulmonologist", "severity": "serious",
        "desc": "A chronic condition in which the airways narrow and swell, causing wheezing and breathlessness.",
        "precautions": ["Keep a rescue inhaler with you", "Avoid dust, smoke and known triggers", "Follow your asthma action plan", "Seek emergency care if the inhaler does not relieve breathlessness"],
        "symptoms": {"wheezing": .9, "shortness_of_breath": .9, "dry_cough": .6, "chest_pain": .45, "fatigue": .3},
    },
    "Pneumonia": {
        "specialist": "Pulmonologist / General Physician", "severity": "serious",
        "desc": "An infection that inflames the air sacs in the lungs, which may fill with fluid or pus.",
        "precautions": ["Get a chest X-ray and doctor review promptly", "Take antibiotics exactly as prescribed", "Rest and drink fluids", "Seek emergency care if breathing is fast, laboured or lips turn bluish"],
        "symptoms": {"fever": .85, "high_fever": .45, "productive_cough": .85, "shortness_of_breath": .75, "chest_pain": .6, "chills": .55, "fatigue": .7, "body_pain": .3},
    },
    "Tuberculosis (suspected)": {
        "specialist": "Pulmonologist / TB Specialist", "severity": "serious",
        "desc": "A bacterial infection mainly of the lungs, with a long-lasting cough, weight loss and night sweats.",
        "precautions": ["Get sputum test and chest X-ray without delay", "Cough etiquette and good ventilation", "TB is curable - complete the full treatment course", "Screen close family contacts"],
        "symptoms": {"productive_cough": .9, "cough": .9, "weight_loss": .75, "night_sweats": .75, "fever": .6, "fatigue": .65, "loss_of_appetite": .6, "chest_pain": .35},
    },
    "Urinary Tract Infection (UTI)": {
        "specialist": "General Physician / Urologist", "severity": "moderate",
        "desc": "A bacterial infection of the bladder or urinary tract causing burning and frequent urination.",
        "precautions": ["Drink plenty of water", "Get a urine routine and culture test", "Complete the prescribed antibiotics", "See a doctor quickly if you have fever or back pain"],
        "symptoms": {"burning_urination": .95, "frequent_urination": .8, "abdominal_pain": .5, "fever": .3, "dark_urine": .25, "nausea": .15},
    },
    "Allergic Rhinitis": {
        "specialist": "ENT Specialist / Allergist", "severity": "mild",
        "desc": "An allergic reaction to pollen, dust or pets causing sneezing and an itchy, runny nose.",
        "precautions": ["Avoid known allergens (dust, pollen)", "Keep windows closed on high-pollen days", "Wash bedding in hot water weekly", "Antihistamines may help - ask a pharmacist or doctor"],
        "symptoms": {"sneezing": .95, "runny_nose": .9, "itchy_eyes": .85, "itchy_skin": .3, "headache": .25, "cough": .3},
    },
    "Iron-Deficiency Anemia": {
        "specialist": "General Physician / Hematologist", "severity": "moderate",
        "desc": "Too few healthy red blood cells due to low iron, causing tiredness and paleness.",
        "precautions": ["Get a complete blood count (CBC) and ferritin test", "Eat iron-rich foods (greens, dates, jaggery, legumes) with vitamin C", "Take iron supplements only as advised", "Look for the underlying cause with your doctor"],
        "symptoms": {"fatigue": .95, "pale_skin": .85, "dizziness": .65, "shortness_of_breath": .4, "headache": .4, "chest_pain": .15},
    },
    "Hepatitis / Jaundice": {
        "specialist": "Gastroenterologist / Hepatologist", "severity": "serious",
        "desc": "Inflammation of the liver causing yellowing of skin and eyes and dark urine.",
        "precautions": ["Get liver function tests (LFT) urgently", "Avoid alcohol and self-medication", "Drink boiled water and eat fresh, light food", "Seek care quickly - some types are highly contagious"],
        "symptoms": {"yellow_skin": .95, "dark_urine": .85, "fatigue": .75, "nausea": .65, "loss_of_appetite": .7, "abdominal_pain": .55, "fever": .35, "vomiting": .35},
    },
    "Chickenpox": {
        "specialist": "General Physician / Dermatologist", "severity": "moderate",
        "desc": "A highly contagious viral infection with an itchy rash of fluid-filled blisters.",
        "precautions": ["Isolate until all blisters have crusted over", "Do not scratch - keep nails short", "Calamine lotion for itching (doctor's advice)", "Avoid contact with pregnant women and newborns"],
        "symptoms": {"blisters": .95, "rash": .9, "itchy_skin": .85, "fever": .6, "fatigue": .5, "headache": .35, "loss_of_appetite": .4},
    },
    "GERD (Acid Reflux)": {
        "specialist": "Gastroenterologist", "severity": "mild",
        "desc": "Stomach acid flows back into the food pipe, causing heartburn and a sour taste.",
        "precautions": ["Eat smaller meals and avoid lying down right after eating", "Cut down on spicy, oily food, caffeine and alcohol", "Raise the head of your bed", "See a doctor if it happens often or you have trouble swallowing"],
        "symptoms": {"heartburn": .95, "chest_pain": .5, "nausea": .45, "abdominal_pain": .45, "cough": .25, "sore_throat": .25},
    },
}

# Symptom combinations that need urgent attention regardless of the model output
RED_FLAGS = [
    ({"chest_pain", "shortness_of_breath"}, "Chest pain together with breathlessness can signal a heart or lung emergency."),
    ({"chest_pain", "sweating"}, "Chest pain with sweating can signal a heart attack."),
    ({"severe_headache", "blurred_vision"}, "Sudden severe headache with vision changes needs urgent evaluation."),
    ({"high_fever", "rash"}, "High fever with rash needs prompt medical assessment."),
    ({"yellow_skin", "vomiting"}, "Jaundice with persistent vomiting needs urgent care."),
]

EMERGENCY_NUMBERS = "India: dial 112 (national emergency) or 108 (ambulance)."
