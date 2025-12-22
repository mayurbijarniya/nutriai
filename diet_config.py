from typing import Dict, Any, List

# Diet type configurations and helpers

# Legacy-lite configs used across the app (kept for compatibility)
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
    "flexitarian": {
        "label": "Flexitarian",
        "macros": {"carbs_pct": (0.45, 0.55), "protein_pct": (0.15, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "Mostly plant-based with occasional meat",
        "restrictions": [],
        "recommended": ["Plants", "Occasional lean meats"],
        "good_for": ["general_health"],
        "difficulty": "easy",
        "timeline": "2-4 weeks",
        "student_notes": "Flexible with campus options."
    },
    "gluten_free": {
        "label": "Gluten-Free",
        "macros": {"carbs_pct": (0.45, 0.50), "protein_pct": (0.18, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "Avoid gluten-containing grains",
        "restrictions": ["Wheat", "Barley", "Rye"],
        "recommended": ["Rice", "Corn", "Quinoa", "Potatoes"],
        "good_for": ["celiac", "gluten_sensitivity"],
        "difficulty": "medium",
        "timeline": "2-4 weeks",
        "student_notes": "Check labels and cross-contamination."
    },
    "whole30": {
        "label": "Whole30",
        "macros": {"carbs_pct": (0.25, 0.35), "protein_pct": (0.25, 0.35), "fat_pct": (0.35, 0.45)},
        "focus": "30-day elimination of sugar, grains, legumes, dairy",
        "restrictions": ["Added sugar", "Alcohol", "Grains", "Legumes", "Dairy"],
        "recommended": ["Meat", "Vegetables", "Fruits", "Nuts"],
        "good_for": ["reset"],
        "difficulty": "hard",
        "timeline": "30 days",
        "student_notes": "Plan meals ahead."
    },
    "anti_inflammatory": {
        "label": "Anti-Inflammatory",
        "macros": {"carbs_pct": (0.45, 0.50), "protein_pct": (0.18, 0.20), "fat_pct": (0.30, 0.35)},
        "focus": "Emphasize omega-3s, colorful vegetables, whole foods",
        "restrictions": ["Refined sugar", "Trans fats"],
        "recommended": ["Fatty fish", "Olive oil", "Berries", "Leafy greens"],
        "good_for": ["general_health"],
        "difficulty": "medium",
        "timeline": "3-6 weeks",
        "student_notes": "Choose anti-inflammatory options at salad/grill."
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
    "intermittent_fasting_18_6": {
        "label": "Intermittent Fasting 18:6",
        "macros": {"base": "standard_american"},
        "focus": "6-hour eating window (e.g., 2pm-8pm)",
        "restrictions": ["No calories during 18-hour fast"],
        "recommended": ["Water", "Black coffee", "Plain tea during fast"],
        "good_for": ["weight_loss", "autophagy"],
        "difficulty": "hard",
        "timeline": "2-4 weeks for adaptation",
        "student_notes": "Advanced fasting; stay hydrated."
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


# New comprehensive Diet Configuration System (exact fields per spec)
DIET_CONFIGURATIONS: Dict[str, Dict[str, Any]] = {
    'standard_american': {
        'name': 'Standard American Diet',
        'description': 'Balanced nutrition following USDA dietary guidelines with moderate portions and variety',
        'macro_ratios': {'carbs': 50, 'protein': 20, 'fat': 30},
        'daily_limits': {
            'sodium_mg': 2300,
            'added_sugar_g': 25,
            'saturated_fat_percent': 10,
            'fiber_g': 25
        },
        'encouraged_foods': [
            'whole_grains', 'lean_proteins', 'fish', 'poultry', 'eggs', 'dairy',
            'fruits', 'vegetables', 'nuts', 'seeds', 'legumes', 'olive_oil'
        ],
        'discouraged_foods': [
            'processed_meats', 'fried_foods', 'sugary_drinks', 'candy',
            'refined_grains', 'trans_fats', 'excessive_alcohol'
        ],
        'meal_frequency': '3 meals + 1-2 snacks',
        'difficulty': 'Easy',
        'good_for': ['General health', 'Beginners', 'Balanced lifestyle'],
        'student_notes': 'Most flexible option, works with dining hall meals'
    },

    'mediterranean': {
        'name': 'Mediterranean Diet',
        'description': 'Heart-healthy diet emphasizing olive oil, fish, whole grains, and fresh produce',
        'macro_ratios': {'carbs': 45, 'protein': 20, 'fat': 35},
        'daily_limits': {
            'sodium_mg': 2000,
            'added_sugar_g': 20,
            'red_meat_servings': 0.3,
            'fish_servings': 2
        },
        'encouraged_foods': [
            'olive_oil', 'fish', 'seafood', 'whole_grains', 'legumes', 'nuts',
            'fresh_fruits', 'vegetables', 'herbs', 'moderate_wine', 'yogurt', 'cheese'
        ],
        'discouraged_foods': [
            'red_meat', 'processed_foods', 'refined_sugars', 'butter',
            'margarine', 'processed_meats'
        ],
        'meal_frequency': '3 meals, Mediterranean-style',
        'difficulty': 'Moderate',
        'good_for': ['Heart health', 'Brain health', 'Longevity', 'Anti-inflammatory'],
        'student_notes': 'Great for campus Greek restaurants, affordable with bulk legumes and grains'
    },

    'ketogenic': {
        'name': 'Ketogenic Diet',
        'description': 'Very low-carb, high-fat diet that puts body into ketosis for fat burning',
        'macro_ratios': {'carbs': 5, 'protein': 25, 'fat': 70},
        'daily_limits': {
            'net_carbs_g': 20,
            'protein_g_per_kg': 1.6,
            'electrolytes': {'sodium_mg': 3000, 'potassium_mg': 3500, 'magnesium_mg': 400}
        },
        'encouraged_foods': [
            'meat', 'poultry', 'fatty_fish', 'eggs', 'butter', 'coconut_oil',
            'avocados', 'nuts', 'seeds', 'leafy_greens', 'low_carb_vegetables', 'cheese'
        ],
        'discouraged_foods': [
            'grains', 'sugar', 'fruits_except_berries', 'starchy_vegetables',
            'legumes', 'most_dairy', 'processed_foods', 'alcohol'
        ],
        'meal_frequency': '2-3 meals (often naturally reduces appetite)',
        'difficulty': 'Hard',
        'good_for': ['Rapid weight loss', 'Epilepsy management', 'Mental clarity'],
        'student_notes': 'Challenging with dining halls, requires meal prep and supplements',
        'warnings': ['Keto flu first week', 'Requires electrolyte supplementation', 'Medical supervision recommended']
    },

    'plant_based_vegan': {
        'name': 'Plant-Based Vegan',
        'description': 'Complete elimination of animal products, focusing on whole plant foods',
        'macro_ratios': {'carbs': 55, 'protein': 15, 'fat': 30},
        'daily_limits': {
            'b12_mcg': 2.4,
            'iron_mg': 18,
            'calcium_mg': 1200,
            'omega3_dha_epa_mg': 500
        },
        'encouraged_foods': [
            'legumes', 'nuts', 'seeds', 'whole_grains', 'vegetables', 'fruits',
            'plant_milks', 'tofu', 'tempeh', 'nutritional_yeast', 'quinoa'
        ],
        'discouraged_foods': [
            'meat', 'poultry', 'fish', 'dairy', 'eggs', 'honey', 'gelatin',
            'processed_vegan_foods_high_sodium'
        ],
        'meal_frequency': '3 meals + 2 snacks for adequate protein',
        'difficulty': 'Moderate',
        'good_for': ['Environmental impact', 'Heart health', 'Cancer prevention'],
        'student_notes': 'Many campus options, affordable with bulk grains and legumes',
        'required_supplements': ['B12', 'D3', 'Algae Omega-3'],
        'protein_combining': 'Combine grains + legumes for complete amino acids'
    },

    'intermittent_fasting_16_8': {
        'name': 'Intermittent Fasting 16:8',
        'description': '16-hour fast with 8-hour eating window, typically 12pm-8pm',
        'macro_ratios': {'carbs': 45, 'protein': 25, 'fat': 30},
        'schedule': {
            'fasting_window': '8pm - 12pm next day',
            'eating_window': '12pm - 8pm',
            'allowed_during_fast': ['water', 'black_coffee', 'plain_tea', 'sparkling_water']
        },
        'meal_timing': {
            'first_meal': '12:00pm (break-fast)',
            'second_meal': '4:00pm (lunch)',
            'third_meal': '7:30pm (early dinner)',
            'snacks': 'Within eating window only'
        },
        'encouraged_foods': [
            'high_protein_foods', 'healthy_fats', 'fiber_rich_foods',
            'nutrient_dense_foods', 'adequate_hydration'
        ],
        'difficulty': 'Moderate',
        'good_for': ['Weight management', 'Insulin sensitivity', 'Simplicity'],
        'student_notes': 'Skip breakfast, fits well with late morning classes',
        'warnings': ['May affect morning workouts', 'Social eating challenges']
    },

    'intermittent_fasting_18_6': {
        'name': 'Intermittent Fasting 18:6',
        'description': '18-hour fast with 6-hour eating window, typically 2pm-8pm',
        'macro_ratios': {'carbs': 45, 'protein': 25, 'fat': 30},
        'schedule': {
            'fasting_window': '8pm - 2pm next day',
            'eating_window': '2pm - 8pm',
            'allowed_during_fast': ['water', 'black_coffee', 'plain_tea', 'sparkling_water']
        },
        'meal_timing': {
            'first_meal': '2:00pm (break-fast)',
            'second_meal': '4:30pm (snack/light meal)',
            'third_meal': '7:30pm (dinner)',
            'snacks': 'Within eating window only'
        },
        'encouraged_foods': ['nutrient_dense_foods', 'adequate_hydration'],
        'difficulty': 'Hard',
        'good_for': ['Aggressive weight loss', 'Autophagy'],
        'student_notes': 'Advanced; ensure you eat enough calories in the short window.',
        'warnings': ['Risk of undereating', 'Requires strict timing']
    },

    'dash_diet': {
        'name': 'DASH Diet',
        'description': 'Dietary Approaches to Stop Hypertension - designed to lower blood pressure',
        'macro_ratios': {'carbs': 55, 'protein': 18, 'fat': 27},
        'daily_targets': {
            'sodium_mg': 1500,
            'potassium_mg': 4700,
            'calcium_mg': 1200,
            'magnesium_mg': 500,
            'fiber_g': 30,
            'fruits_servings': 4,
            'vegetables_servings': 5,
            'whole_grains_servings': 6,
            'lean_protein_servings': 2,
            'nuts_seeds_servings': 1,
            'low_fat_dairy_servings': 3
        },
        'encouraged_foods': [
            'fruits', 'vegetables', 'whole_grains', 'lean_meats', 'poultry',
            'fish', 'nuts', 'seeds', 'low_fat_dairy', 'beans', 'legumes'
        ],
        'discouraged_foods': [
            'high_sodium_foods', 'processed_meats', 'full_fat_dairy',
            'sugary_drinks', 'sweets', 'red_meat_excess'
        ],
        'difficulty': 'Moderate',
        'good_for': ['High blood pressure', 'Heart health', 'Stroke prevention'],
        'student_notes': 'Focus on fresh foods, avoid processed campus foods'
    }
}

# Add Flexitarian and Gluten-Free configs to the comprehensive map for completeness
DIET_CONFIGURATIONS['flexitarian'] = {
    'name': 'Flexitarian Diet',
    'description': 'Mostly plant-based with occasional lean meats; flexible and balanced',
    'macro_ratios': {'carbs': 50, 'protein': 20, 'fat': 30},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 25,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['plants', 'whole_grains', 'legumes', 'fruits', 'vegetables', 'lean_meats', 'olive_oil', 'nuts', 'seeds'],
    'discouraged_foods': ['processed_meats', 'sugary_drinks', 'refined_grains', 'trans_fats'],
    'meal_frequency': '3 meals + 1 snack',
    'difficulty': 'Easy',
    'good_for': ['General health', 'Flexibility'],
    'student_notes': 'Easy to follow on campus; choose plant mains and occasional lean meat.'
}

DIET_CONFIGURATIONS['gluten_free'] = {
    'name': 'Gluten-Free Diet',
    'description': 'Avoids wheat, barley, and rye; focus on naturally gluten-free foods',
    'macro_ratios': {'carbs': 50, 'protein': 20, 'fat': 30},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 25,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['rice', 'corn', 'quinoa', 'potatoes', 'fruits', 'vegetables', 'lean_proteins', 'dairy'],
    'discouraged_foods': ['wheat', 'barley', 'rye', 'malt'],
    'meal_frequency': '3 meals + 1-2 snacks',
    'difficulty': 'Moderate',
    'good_for': ['Celiac disease', 'Gluten sensitivity'],
    'student_notes': 'Check labels and cross-contamination; many cafeterias label GF options.'
}

DIET_CONFIGURATIONS['vegetarian'] = {
    'name': 'Vegetarian',
    'description': 'No meat, poultry, or fish; includes dairy and eggs',
    'macro_ratios': {'carbs': 50, 'protein': 20, 'fat': 30},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 25,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['eggs', 'dairy', 'legumes', 'nuts', 'whole_grains', 'vegetables', 'fruits'],
    'discouraged_foods': ['meat', 'fish', 'poultry'],
    'meal_frequency': '3 meals + 1-2 snacks',
    'difficulty': 'Easy',
    'good_for': ['General health', 'Environment'],
    'student_notes': 'Omelet station and yogurt bars are great campus options.'
}

DIET_CONFIGURATIONS['pescatarian'] = {
    'name': 'Pescatarian',
    'description': 'Vegetarian diet that includes fish and seafood',
    'macro_ratios': {'carbs': 45, 'protein': 25, 'fat': 30},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 25,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['fish', 'seafood', 'dairy', 'eggs', 'legumes', 'all_vegetables'],
    'discouraged_foods': ['meat', 'poultry'],
    'meal_frequency': '3 meals + 1-2 snacks',
    'difficulty': 'Easy',
    'good_for': ['Heart health', 'Brain health'],
    'student_notes': 'Tuna packets and grilled fish at dining halls are key.'
}

DIET_CONFIGURATIONS['low_fodmap'] = {
    'name': 'Low FODMAP',
    'description': 'Elimination diet to identify triggers for IBS; restricts fermentable carbs',
    'macro_ratios': {'carbs': 45, 'protein': 25, 'fat': 30},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 25,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['rice', 'potatoes', 'carrots', 'spinach', 'chicken', 'fish', 'eggs', 'lactose_free_dairy'],
    'discouraged_foods': ['wheat', 'onions', 'garlic', 'beans', 'apples', 'pears', 'milk'],
    'meal_frequency': '3 smaller meals + snacks',
    'difficulty': 'Hard',
    'good_for': ['IBS', 'Digestive health'],
    'student_notes': 'Very hard on campus; avoid sauces (onion/garlic) and wheat.'
}

DIET_CONFIGURATIONS['whole30'] = {
    'name': 'Whole30',
    'description': '30-day reset eliminating sugar, alcohol, grains, legumes, and dairy',
    'macro_ratios': {'carbs': 30, 'protein': 30, 'fat': 40},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 0,
        'saturated_fat_percent': 12,
        'fiber_g': 25
    },
    'encouraged_foods': ['meat', 'seafood', 'eggs', 'vegetables', 'fruit', 'natural_fats'],
    'discouraged_foods': ['sugar', 'alcohol', 'grains', 'legumes', 'dairy', 'additives'],
    'meal_frequency': '3 meals, minimal snacking',
    'difficulty': 'Hard',
    'good_for': ['Metabolic reset', 'Identifying sensitivities'],
    'student_notes': 'Stick to plain grilled meats and salads; bring your own dressing.'
}

DIET_CONFIGURATIONS['anti_inflammatory'] = {
    'name': 'Anti-Inflammatory',
    'description': 'Focuses on whole foods, omega-3s, and antioxidants to reduce inflammation',
    'macro_ratios': {'carbs': 45, 'protein': 20, 'fat': 35},
    'daily_limits': {
        'sodium_mg': 2000,
        'added_sugar_g': 15,
        'saturated_fat_percent': 8,
        'fiber_g': 30
    },
    'encouraged_foods': ['berries', 'fatty_fish', 'leafy_greens', 'nuts', 'olive_oil', 'tomatoes'],
    'discouraged_foods': ['fried_foods', 'soda', 'red_meat', 'lard', 'refined_carbs'],
    'meal_frequency': '3 meals + 1 snack',
    'difficulty': 'Moderate',
    'good_for': ['Chronic inflammation', 'Heart health', 'Autoimmune conditions'],
    'student_notes': 'Choose the "healthy station" options; add olive oil to everything.'
}

DIET_CONFIGURATIONS['low_carb'] = {
    'name': 'Low Carb',
    'description': 'Reduced carbohydrate intake with emphasis on protein and healthy fats',
    'macro_ratios': {'carbs': 20, 'protein': 30, 'fat': 50},
    'daily_limits': {
        'sodium_mg': 2300,
        'added_sugar_g': 15,
        'saturated_fat_percent': 10,
        'fiber_g': 25
    },
    'encouraged_foods': ['lean_meats', 'fish', 'eggs', 'non_starchy_vegetables', 'healthy_fats', 'nuts', 'seeds'],
    'discouraged_foods': ['sugary_drinks', 'bread', 'pasta', 'rice', 'potatoes', 'sweets'],
    'meal_frequency': '3 meals',
    'difficulty': 'Moderate',
    'good_for': ['Weight loss', 'Blood sugar control'],
    'student_notes': 'Swap grain-based sides for extra veggies; prioritize protein at every meal.'
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


# Exact-named helpers requested
def calculate_bmr(weight_kg: float, height_cm: float, age: int, biological_sex: str) -> float:
    """Mifflin-St Jeor Equation"""
    return mifflin_st_jeor_bmr(weight_kg, height_cm, age, biological_sex)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure"""
    return bmr * get_activity_multiplier(activity_level)


def calculate_macro_grams(calories: float, diet_type: str) -> Dict[str, float]:
    """Convert macro percentages to grams using DIET_CONFIGURATIONS."""
    cfg = DIET_CONFIGURATIONS.get(diet_type) or DIET_CONFIGURATIONS['standard_american']
    ratios = cfg['macro_ratios']
    carb_cal = calories * (ratios['carbs'] / 100)
    protein_cal = calories * (ratios['protein'] / 100)
    fat_cal = calories * (ratios['fat'] / 100)
    return {
        'carbs': carb_cal / 4.0,
        'protein': protein_cal / 4.0,
        'fat': fat_cal / 9.0
    }


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


def calculate_daily_targets(age: int, sex: str, weight_kg: float, height_cm: float, activity_level: str, goal_type: str, diet_slug: str, override_calories: int = None) -> Dict[str, int]:
    bmr = mifflin_st_jeor_bmr(weight_kg, height_cm, age, sex)
    maintenance = int(bmr * get_activity_multiplier(activity_level))
    
    if override_calories:
        target_calories = max(1200, override_calories)
    else:
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


# Personalized analysis helpers
def compute_macro_adherence_10pt(calories_kcal: float, carbs_g: float, protein_g: float, fat_g: float, diet_type: str) -> Dict[str, Any]:
    """Score 1-10 based on ±5% tolerance to macro ratios."""
    if not calories_kcal or calories_kcal <= 0:
        return {"score": None, "explanation": "Insufficient calorie data"}
    cfg = DIET_CONFIGURATIONS.get(diet_type) or DIET_CONFIGURATIONS['standard_american']
    ratios = cfg['macro_ratios']
    actual = {
        'carbs': (carbs_g * 4.0) / calories_kcal if carbs_g is not None else None,
        'protein': (protein_g * 4.0) / calories_kcal if protein_g is not None else None,
        'fat': (fat_g * 9.0) / calories_kcal if fat_g is not None else None,
    }
    missing = [k for k,v in actual.items() if v is None]
    if missing:
        return {"score": None, "explanation": f"Missing macros: {', '.join(missing)}"}
    target = {k: ratios[k]/100.0 for k in ['carbs','protein','fat']}
    diffs = {k: abs(actual[k] - target[k]) for k in target}
    # 0 diff => 10, 5% diff => ~8, 15% diff => ~5, >25% => ~2
    penalties = sum(max(0.0, (d - 0.05) * 20.0) for d in diffs.values())  # each 0.05 over costs 1 pt
    score = max(1.0, min(10.0, 10.0 - penalties))
    exp = ", ".join([f"{k} off by {int(d*100)}%" for k,d in diffs.items() if d > 0.05]) or "Within ±5% of targets"
    return {"score": round(score,1), "explanation": exp}


def detect_allergens_from_text(markdown_text: str, user_allergies: List[str]) -> List[Dict[str, Any]]:
    if not markdown_text or not user_allergies:
        return []
    text = (markdown_text or '').lower()
    matches = []
    # Simple keyword map
    keywords = {
        'nuts': ['almond','walnut','cashew','pistachio','pecan','hazelnut','peanut'],
        'dairy': ['milk','cheese','butter','cream','yogurt','ghee'],
        'eggs': ['egg','mayonnaise','mayo'],
        'shellfish': ['shrimp','prawn','lobster','crab','scallop'],
        'fish': ['salmon','tuna','cod','fish','anchovy','sardine'],
        'soy': ['soy','tofu','edamame','soybean', 'soy sauce'],
        'gluten': ['wheat','barley','rye','flour','bread','tortilla','pasta'],
        'sesame': ['sesame','tahini']
    }
    for allergen in user_allergies:
        for kw in keywords.get(allergen, []):
            if kw in text:
                matches.append({"allergen": allergen, "keyword": kw, "confidence": "medium"})
                break
    return matches


def portion_feedback(calories_kcal: float, daily_target_kcal: float, meal_context: str) -> str:
    if not calories_kcal or not daily_target_kcal or daily_target_kcal <= 0:
        return ""
    pct = calories_kcal / daily_target_kcal
    context_note = ""
    if meal_context in ("pre_workout","post_workout"):
        context_note = " for your workout"
    if pct < 0.20:
        return f"Light meal (~{int(pct*100)}% of day){context_note}. Consider adding protein/fiber if still hungry."
    if pct <= 0.40:
        return f"Balanced portion (~{int(pct*100)}% of day){context_note}."
    if pct <= 0.60:
        return f"Hearty meal (~{int(pct*100)}% of day){context_note}. Plan lighter meals later."
    return f"Very heavy (~{int(pct*100)}% of day){context_note}. Reduce energy-dense items for balance."


def goal_specific_advice(goal_type: str) -> List[str]:
    mapping = {
        'lose_weight_slow': ["Reduce calorie-dense toppings", "Increase non-starchy vegetables"],
        'lose_weight_moderate': ["Choose leaner proteins", "Swap refined grains for whole grains"],
        'lose_weight_fast': ["Limit liquid calories", "Avoid fried items"],
        'maintain_weight': ["Keep portions consistent", "Prioritize whole foods"],
        'gain_weight_slow': ["Add healthy fats like olive oil", "Include calorie-dense snacks"],
        'gain_weight_moderate': ["Increase meal frequency", "Add protein shakes"],
        'build_muscle': ["Target 1.6–2.2 g/kg protein", "Include protein each meal"],
        'improve_health': ["Emphasize plants and fiber", "Reduce added sugars"],
        'manage_diabetes': ["Focus on carb counting", "Prefer low-GI carbs"],
        'lower_cholesterol': ["Use olive oil over butter", "Increase soluble fiber"]
    }
    return mapping.get(goal_type or 'maintain_weight', ["Choose minimally processed foods"]) 


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


