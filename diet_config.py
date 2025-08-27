from typing import Dict, Any

# Diet type configurations and helpers

DIETS: Dict[str, Dict[str, Any]] = {
    "standard_american": {
        "label": "Standard American Diet",
        "macros": {"carbs_pct": (0.45, 0.50), "protein_pct": (0.15, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "Balanced nutrition, portion control",
        "restrictions": [],
        "recommended": ["Whole grains", "Lean proteins", "Fruits", "Vegetables", "Dairy"],
        "avoid": ["Excessive processed foods", "Added sugars >25g/day"],
        "good_for": ["general_health"],
        "difficulty": "easy",
        "timeline": "2-4 weeks for noticeable improvements",
        "student_notes": "Good default. Campus dining friendly."
    },
    "mediterranean": {
        "label": "Mediterranean Diet",
        "macros": {"carbs_pct": (0.45, 0.50), "protein_pct": (0.15, 0.20), "fat_pct": (0.35, 0.40)},
        "focus": "Olive oil, fish, whole grains, legumes, fruits, vegetables",
        "restrictions": ["Limit red meat", "Minimal processed foods"],
        "recommended": ["Olive oil", "Fish 2x/week", "Nuts", "Whole grains", "Legumes"],
        "avoid": ["Processed meats", "Refined sugars", "Trans fats"],
        "good_for": ["heart_health", "general_health"],
        "difficulty": "easy",
        "timeline": "3-6 weeks for energy and lipid improvements",
        "student_notes": "Great if cafeteria has salad bar, olive oil, fish options."
    },
    "ketogenic": {
        "label": "Ketogenic Diet",
        "macros": {"carbs_pct": (0.05, 0.10), "protein_pct": (0.20, 0.25), "fat_pct": (0.70, 0.80), "carbs_cap_g": (20, 50)},
        "focus": "High fat, very low carb, moderate protein",
        "restrictions": ["Grains", "Sugar", "Most fruits", "Starchy vegetables"],
        "recommended": ["Avocados", "Nuts", "Oils", "Fatty fish", "Low-carb vegetables"],
        "avoid": ["Bread", "Pasta", "Rice", "Potatoes", "Most fruits", "Sugar"],
        "good_for": ["weight_loss", "blood_sugar"],
        "difficulty": "hard",
        "timeline": "1-2 weeks adaptation; 4+ weeks for results",
        "student_notes": "Meal prep helps. Watch hidden sugars in sauces."
    },
    "paleo": {
        "label": "Paleo Diet",
        "macros": {"carbs_pct": (0.25, 0.35), "protein_pct": (0.25, 0.35), "fat_pct": (0.35, 0.45)},
        "focus": "Whole foods, no processed foods",
        "restrictions": ["Grains", "Legumes", "Dairy", "Refined sugar", "Processed foods"],
        "recommended": ["Meat", "Fish", "Eggs", "Vegetables", "Fruits", "Nuts", "Seeds"],
        "avoid": ["Wheat", "Rice", "Beans", "Dairy", "Refined sugar", "Processed foods"],
        "good_for": ["weight_loss", "general_health"],
        "difficulty": "medium",
        "timeline": "2-4 weeks for digestion and energy changes",
        "student_notes": "Focus on grill stations, salads; avoid grains/legumes sides."
    },
    "plant_based_vegan": {
        "label": "Plant-Based Vegan",
        "macros": {"carbs_pct": (0.50, 0.60), "protein_pct": (0.12, 0.18), "fat_pct": (0.25, 0.35)},
        "focus": "No animal products, whole plant foods",
        "restrictions": ["Meat", "Dairy", "Eggs", "Honey"],
        "recommended": ["Legumes", "Nuts", "Seeds", "Whole grains", "Vegetables", "Fruits"],
        "avoid": ["Ultra-processed vegan junk foods"],
        "good_for": ["general_health", "environment"],
        "difficulty": "medium",
        "timeline": "3-6 weeks; ensure supplements",
        "nutrients_to_watch": ["B12", "Iron", "Calcium", "Omega-3", "Vitamin D"],
        "student_notes": "Check dining hall vegan station; supplement B12."
    },
    "vegetarian": {
        "label": "Vegetarian",
        "macros": {"carbs_pct": (0.45, 0.55), "protein_pct": (0.15, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "No meat, includes dairy and eggs",
        "restrictions": ["Meat", "Fish", "Poultry"],
        "recommended": ["Eggs", "Dairy", "Legumes", "Nuts", "Whole grains", "Vegetables"],
        "good_for": ["general_health"],
        "difficulty": "easy",
        "timeline": "2-4 weeks",
        "nutrients_to_watch": ["Iron", "B12", "Zinc"],
        "student_notes": "Omelet and yogurt bars are useful."
    },
    "pescatarian": {
        "label": "Pescatarian",
        "macros": {"carbs_pct": (0.40, 0.50), "protein_pct": (0.20, 0.25), "fat_pct": (0.30, 0.35)},
        "focus": "Fish and seafood, no other meat",
        "restrictions": ["Meat", "Poultry"],
        "recommended": ["Fish", "Seafood", "Eggs", "Dairy", "Plants"],
        "good_for": ["heart_health"],
        "difficulty": "easy",
        "timeline": "2-4 weeks",
        "student_notes": "Canned tuna/salmon are budget-friendly."
    },
    "dash_diet": {
        "label": "DASH Diet",
        "macros": {"carbs_pct": (0.50, 0.55), "protein_pct": (0.18, 0.18), "fat_pct": (0.27, 0.27), "sodium_limit_mg": 1500},
        "focus": "Lower sodium, high potassium",
        "restrictions": ["High sodium foods", "Excess saturated fat"],
        "recommended": ["Fruits", "Vegetables", "Whole grains", "Lean proteins", "Low-fat dairy"],
        "good_for": ["blood_pressure", "heart_health"],
        "difficulty": "medium",
        "timeline": "2-4 weeks for blood pressure changes",
        "student_notes": "Avoid soups and processed sides high in sodium."
    },
    "intermittent_fasting_16_8": {
        "label": "Intermittent Fasting 16:8",
        "macros": {"base": "standard_american"},
        "focus": "8-hour eating window (e.g., 12pm-8pm)",
        "restrictions": ["No calories during 16-hour fast"],
        "recommended": ["Water", "Black coffee", "Plain tea during fast"],
        "good_for": ["weight_loss", "insulin_sensitivity"],
        "difficulty": "medium",
        "timeline": "2-3 weeks for adaptation",
        "student_notes": "Align eating window with class schedule."
    },
    "low_fodmap": {
        "label": "Low-FODMAP",
        "macros": {"carbs_pct": (0.45, 0.50), "protein_pct": (0.20, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "Reduce digestive symptoms",
        "restrictions": ["High-FODMAP foods: onions, garlic, wheat, certain fruits"],
        "recommended": ["Rice", "Potatoes", "Carrots", "Spinach", "Chicken", "Fish"],
        "good_for": ["ibs"],
        "difficulty": "hard",
        "timeline": "6-8 weeks elimination; then reintroduction",
        "student_notes": "Read labels; sauces often have onion/garlic."
    },
    "low_carb": {
        "label": "Low Carb",
        "macros": {"carbs_pct": (0.20, 0.35), "protein_pct": (0.25, 0.30), "fat_pct": (0.35, 0.45)},
        "focus": "Reduced carbs, higher protein/fat",
        "restrictions": ["Refined carbs", "Sugary drinks"],
        "recommended": ["Lean proteins", "Non-starchy vegetables", "Healthy fats"],
        "good_for": ["weight_loss", "blood_sugar"],
        "difficulty": "medium",
        "timeline": "2-4 weeks",
        "student_notes": "Swap rice/pasta for veggies; add protein."
    }
}


def get_activity_multiplier(level: str) -> float:
    return {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extremely_active': 1.9
    }.get(level or 'sedentary', 1.2)


def mifflin_st_jeor_bmr(weight_kg: float, height_cm: float, age_years: int, biological_sex: str) -> float:
    if biological_sex == 'male':
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + 5
    # female or other
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) - 161


def goal_adjustment_calories(goal_type: str) -> int:
    return {
        'lose_weight_slow': -250,
        'lose_weight_moderate': -500,
        'lose_weight_fast': -750,
        'maintain_weight': 0,
        'gain_weight_slow': 250,
        'gain_weight_moderate': 500,
        'build_muscle': 300,
        'improve_health': 0,
        'manage_diabetes': 0,
        'lower_cholesterol': 0
    }.get(goal_type or 'maintain_weight', 0)


def midpoint(a: float, b: float) -> float:
    return (a + b) / 2.0


def get_diet_config(diet_slug: str) -> Dict[str, Any]:
    return DIETS.get(diet_slug, DIETS['standard_american'])


def calculate_daily_targets(age: int, sex: str, weight_kg: float, height_cm: float, activity_level: str, goal_type: str, diet_slug: str) -> Dict[str, int]:
    bmr = mifflin_st_jeor_bmr(weight_kg, height_cm, age, sex)
    maintenance = int(bmr * get_activity_multiplier(activity_level))
    target_calories = max(1200, maintenance + goal_adjustment_calories(goal_type))

    config = get_diet_config(diet_slug)
    macros = config.get('macros', {})

    # Resolve macros from base diet in IF
    if 'base' in macros:
        base = get_diet_config(macros['base'])
        macros = base['macros']

    carbs_pct = midpoint(*macros.get('carbs_pct', (0.45, 0.50)))
    protein_pct = midpoint(*macros.get('protein_pct', (0.15, 0.20)))
    fat_pct = midpoint(*macros.get('fat_pct', (0.30, 0.35)))

    # Ensure sum ~1.0
    total_pct = carbs_pct + protein_pct + fat_pct
    if total_pct != 0:
        carbs_pct /= total_pct
        protein_pct /= total_pct
        fat_pct /= total_pct

    # Keto special carb cap in grams
    carbs_g = int((target_calories * carbs_pct) / 4)
    if diet_slug == 'ketogenic' and 'carbs_cap_g' in macros:
        cap_min, cap_max = macros['carbs_cap_g']
        carbs_g = min(carbs_g, cap_max)

    protein_g = int((target_calories * protein_pct) / 4)
    fat_g = int((target_calories * fat_pct) / 9)
    fiber_g = max(25, int(target_calories / 1000 * 14))
    sodium_mg = 1500 if diet_slug == 'dash_diet' else 2300
    sugar_g = int(target_calories * 0.10 / 4)

    return {
        'target_calories': target_calories,
        'protein_grams': protein_g,
        'carbs_grams': carbs_g,
        'fat_grams': fat_g,
        'fiber_grams': fiber_g,
        'sodium_mg': sodium_mg,
        'sugar_grams': sugar_g
    }


def score_meal_adherence(nutrients: Dict[str, Any], diet_slug: str) -> Dict[str, Any]:
    """Return adherence percentage and violations based on available nutrients.
    nutrients may include: calories, carbs (g), protein (g), fat (g), sodium_mg, sodium_level.
    """
    violations = []
    score = 100
    cfg = get_diet_config(diet_slug)
    macros = cfg.get('macros', {})

    carbs_g = nutrients.get('carbs')
    protein_g = nutrients.get('protein')
    fat_g = nutrients.get('fat')
    sodium_mg = nutrients.get('sodium_mg')
    sodium_level = (nutrients.get('sodium_level') or '').lower()

    # Keto: strong penalty for carbs > 50g
    if diet_slug == 'ketogenic':
        cap_max = macros.get('carbs_cap_g', (20, 50))[1]
        if carbs_g is not None and carbs_g > cap_max:
            over = carbs_g - cap_max
            score -= min(60, over)  # heavy penalty
            violations.append({"type": "carbs", "message": f"Carbs exceed keto cap ({carbs_g}g > {cap_max}g)"})

    # DASH: sodium > 1500-2300 mg
    if diet_slug == 'dash_diet':
        limit = macros.get('sodium_limit_mg', 1500)
        approx = None
        if sodium_mg is not None:
            approx = sodium_mg
        elif sodium_level:
            approx = 1000 if 'low' in sodium_level else 1800 if 'medium' in sodium_level else 2400
        if approx and approx > limit:
            delta = approx - limit
            score -= min(40, int(delta / 50))
            violations.append({"type": "sodium", "message": f"Sodium estimated high (~{approx} mg > {limit} mg)"})

    # Low-FODMAP: we cannot parse specific FODMAPs; leave as neutral

    # General macro balance check vs midpoints
    if all(v is not None for v in [carbs_g, protein_g, fat_g]):
        total_cal = carbs_g * 4 + protein_g * 4 + fat_g * 9
        if total_cal > 0:
            cp = midpoint(*macros.get('carbs_pct', (0.45, 0.50)))
            pp = midpoint(*macros.get('protein_pct', (0.15, 0.20)))
            fp = midpoint(*macros.get('fat_pct', (0.30, 0.35)))
            actual_cp = (carbs_g * 4) / total_cal
            actual_pp = (protein_g * 4) / total_cal
            actual_fp = (fat_g * 9) / total_cal
            # penalize deviations > 10 percentage points
            for name, target, actual in [("carbs", cp, actual_cp), ("protein", pp, actual_pp), ("fat", fp, actual_fp)]:
                diff = abs(actual - target)
                if diff > 0.10:
                    penalty = int(diff * 100)  # 10% diff => 10 points
                    score -= penalty
                    violations.append({"type": name, "message": f"{name.title()} off target by {int(diff*100)}%"})

    score = max(0, min(100, score))
    suggestions = []
    if diet_slug == 'ketogenic' and carbs_g is not None and carbs_g > 50:
        suggestions.append("Replace high-carb sides with leafy greens or zucchini.")
    if diet_slug == 'dash_diet' and ((sodium_mg and sodium_mg > 1500) or 'high' in sodium_level):
        suggestions.append("Choose fresh items over soups or processed foods to reduce sodium.")

    return {"score": score, "violations": violations, "suggestions": suggestions}


def generate_transition_plan(diet_from: str, diet_to: str) -> Dict[str, Any]:
    """Simple 7-day macro transition plan from current to target diet."""
    from_cfg = get_diet_config(diet_from)
    to_cfg = get_diet_config(diet_to)

    def pct(cfg, key):
        a, b = cfg.get('macros', {}).get(key, (0.33, 0.34))
        return midpoint(a, b)

    from_macros = {k: pct(from_cfg, k) for k in ['carbs_pct', 'protein_pct', 'fat_pct']}
    to_macros = {k: pct(to_cfg, k) for k in ['carbs_pct', 'protein_pct', 'fat_pct']}

    days = []
    steps = 6  # transitions in 6 steps, day 7 equals target
    for d in range(1, 8):
        t = d / 7.0
        day_pct = {
            k: round(from_macros[k] + (to_macros[k] - from_macros[k]) * t, 3)
            for k in from_macros
        }
        days.append({"day": d, "carbs_pct": day_pct['carbs_pct'], "protein_pct": day_pct['protein_pct'], "fat_pct": day_pct['fat_pct']})

    return {"from": diet_from, "to": diet_to, "days": days}


