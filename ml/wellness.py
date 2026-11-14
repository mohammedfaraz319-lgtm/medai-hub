"""Wellness Hub data and calculators (BMI, daily calories, today's recommendation)."""
import datetime

# Weekly split. "REST" days appear exactly as in the project screenshot.
SPLIT = {0: "Chest & Triceps", 1: "Back & Biceps", 2: "Legs", 3: "Shoulders & Abs", 4: "Full Body", 5: "Cardio & Core", 6: "REST"}

WORKOUTS = {
    "Chest": ["Push-ups 4x12", "Dumbbell bench press 4x10", "Incline press 3x10", "Chest fly 3x12", "Dips 3x8"],
    "Back": ["Pull-ups / assisted 4x8", "Bent-over row 4x10", "Lat pulldown 3x12", "Seated cable row 3x12", "Superman hold 3x30s"],
    "Legs": ["Squats 4x12", "Lunges 3x12 each", "Romanian deadlift 3x10", "Leg press 3x12", "Calf raises 4x15"],
    "Shoulders": ["Overhead press 4x10", "Lateral raises 3x15", "Front raises 3x12", "Face pulls 3x15", "Shrugs 3x12"],
    "Arms": ["Barbell curls 3x10", "Hammer curls 3x12", "Triceps pushdown 3x12", "Skull crushers 3x10", "Bench dips 3x12"],
    "Core": ["Plank 3x45s", "Bicycle crunches 3x20", "Leg raises 3x12", "Russian twists 3x20", "Mountain climbers 3x30s"],
    "Glutes": ["Hip thrusts 4x12", "Glute bridges 3x15", "Sumo squats 3x12", "Donkey kicks 3x15", "Step-ups 3x12"],
    "Cardio": ["Brisk walk / jog 30 min", "Jump rope 5x1 min", "Cycling 30 min", "Burpees 3x10", "High knees 4x30s"],
}
GENDER_FOCUS = {
    "Men": "Build upper-body strength with progressive overload; keep rest 60-90s between sets.",
    "Women": "Mix strength training with glute/leg work and cardio; progressive overload builds lean muscle without bulk.",
}

DIETS = {
    "Weight Loss": {
        "tip": "Aim for a gentle 300-500 kcal daily deficit with high protein and fibre.",
        "meals": {"Breakfast": "Vegetable oats / moong dal chilla + 1 fruit", "Lunch": "2 rotis, dal, large salad, curd", "Snack": "Roasted chana or a handful of nuts", "Dinner": "Grilled paneer/chicken or sprouts salad + sauteed vegetables"},
    },
    "Muscle Gain": {
        "tip": "Eat in a small surplus (+250-400 kcal) with 1.6-2.0 g protein per kg body weight.",
        "meals": {"Breakfast": "3 eggs / paneer bhurji, 2 toasts, banana", "Lunch": "Rice, dal, chicken/soya chunks, vegetables, curd", "Snack": "Peanut butter sandwich + milk", "Dinner": "3 rotis, paneer/fish curry, salad"},
    },
    "Maintain Weight": {
        "tip": "Balanced plate: half vegetables, a quarter protein, a quarter whole grains.",
        "meals": {"Breakfast": "Idli/dosa with sambar or poha with sprouts", "Lunch": "Rice/roti, dal, vegetable, curd", "Snack": "Fruit or buttermilk with nuts", "Dinner": "Light khichdi or roti-sabzi with a protein"},
    },
    "Diabetes-Friendly": {
        "tip": "Choose low-glycaemic foods, avoid sugary drinks, and keep meal timings regular. Follow your doctor's plan.",
        "meals": {"Breakfast": "Ragi dosa / vegetable upma + unsweetened curd", "Lunch": "Millet roti, dal, green vegetables, salad", "Snack": "Cucumber, sprouts or roasted makhana", "Dinner": "Vegetable soup + grilled protein + 1 roti"},
    },
    "Heart-Healthy": {
        "tip": "Low salt, low saturated fat; lots of vegetables, fruits, nuts, oats and fish.",
        "meals": {"Breakfast": "Oats with fruit and flaxseed", "Lunch": "Brown rice/roti, dal, mixed vegetables, salad", "Snack": "Walnuts/almonds or guava", "Dinner": "Grilled fish or legumes with steamed vegetables"},
    },
}


def todays_recommendation(today=None):
    today = today or datetime.date.today()
    focus = SPLIT[today.weekday()]
    if focus == "REST":
        return {"title": "Today's Recommendation", "text": "We suggest training REST (Men) or REST (Women) today.",
                "focus": "REST", "tip": "Recovery is when muscles grow. Take a walk, stretch, hydrate and sleep 7-8 hours."}
    return {"title": "Today's Recommendation", "text": f"Today's focus: {focus}.", "focus": focus,
            "tip": "Warm up for 5-10 minutes first and cool down with stretching."}


def bmi_report(weight_kg, height_cm, age, sex, activity):
    h = height_cm / 100
    bmi = weight_kg / (h * h)
    if bmi < 18.5:
        cat = "Underweight"
    elif bmi < 23:   # Asian cut-offs (WHO Asia-Pacific)
        cat = "Healthy weight"
    elif bmi < 27.5:
        cat = "Overweight"
    else:
        cat = "Obese"
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)
    mult = {"low": 1.2, "light": 1.375, "moderate": 1.55, "high": 1.725}.get(activity, 1.375)
    tdee = bmr * mult
    return {
        "bmi": round(bmi, 1), "category": cat, "bmr": round(bmr), "maintenance_kcal": round(tdee),
        "loss_kcal": round(tdee - 400), "gain_kcal": round(tdee + 300),
        "healthy_range_kg": [round(18.5 * h * h, 1), round(22.9 * h * h, 1)],
        "water_litres": round(weight_kg * 0.035, 1),
    }
