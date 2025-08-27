# profile.py - User Profile Management System
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timezone
from bson import ObjectId
from database import get_db
import json

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
db = get_db()

# Validation constants and enums
BIOLOGICAL_SEX_OPTIONS = ['male', 'female', 'other']
ACTIVITY_LEVELS = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active']
HEALTH_CONDITIONS = [
    'diabetes_type1', 'diabetes_type2', 'hypertension', 'heart_disease', 
    'kidney_disease', 'celiac', 'ibs', 'food_allergies', 'thyroid_issues', 'none'
]
GOAL_TYPES = [
    'lose_weight_slow', 'lose_weight_moderate', 'lose_weight_fast',
    'maintain_weight', 'gain_weight_slow', 'gain_weight_moderate',
    'build_muscle', 'improve_health', 'manage_diabetes', 'lower_cholesterol'
]
DIET_TYPES = [
    'standard_american', 'mediterranean', 'ketogenic', 'paleo',
    'plant_based_vegan', 'vegetarian', 'pescatarian', 'flexitarian',
    'intermittent_fasting_16_8', 'intermittent_fasting_18_6',
    'dash_diet', 'low_carb', 'gluten_free', 'low_fodmap',
    'whole30', 'anti_inflammatory'
]
FOOD_ALLERGIES = ['nuts', 'dairy', 'eggs', 'shellfish', 'fish', 'soy', 'gluten', 'sesame']
FOOD_RESTRICTIONS = ['halal', 'kosher', 'no_pork', 'no_beef', 'no_alcohol', 'organic_only']
MEAL_TIMING = ['early_bird', 'normal', 'night_owl']
COOKING_SKILLS = ['beginner', 'intermediate', 'advanced']

@profile_bp.route('/setup')
@login_required
def setup():
    """Multi-step profile setup form"""
    user_id = ObjectId(current_user.id)
    
    # Check if profile already exists
    existing_profile = db.user_profiles.find_one({'user_id': user_id})
    existing_goals = db.nutrition_goals.find_one({'user_id': user_id})
    existing_preferences = db.diet_preferences.find_one({'user_id': user_id})
    
    # Convert ObjectIds to strings for frontend
    if existing_profile and 'user_id' in existing_profile:
        existing_profile['user_id'] = str(existing_profile['user_id'])
    if existing_goals and 'user_id' in existing_goals:
        existing_goals['user_id'] = str(existing_goals['user_id'])
    if existing_preferences and 'user_id' in existing_preferences:
        existing_preferences['user_id'] = str(existing_preferences['user_id'])
    
    return render_template('profile/setup.html', 
                         user=current_user,
                         existing_profile=existing_profile,
                         existing_goals=existing_goals,
                         existing_preferences=existing_preferences,
                         constants={
                             'biological_sex_options': BIOLOGICAL_SEX_OPTIONS,
                             'activity_levels': ACTIVITY_LEVELS,
                             'health_conditions': HEALTH_CONDITIONS,
                             'goal_types': GOAL_TYPES,
                             'diet_types': DIET_TYPES,
                             'food_allergies': FOOD_ALLERGIES,
                             'food_restrictions': FOOD_RESTRICTIONS,
                             'meal_timing': MEAL_TIMING,
                             'cooking_skills': COOKING_SKILLS
                         })

@profile_bp.route('/api/save', methods=['POST'])
@login_required
def save_profile():
    """Save user profile data (user-specific only)"""
    try:
        data = request.get_json()
        user_id = ObjectId(current_user.id)
        now = datetime.now(timezone.utc)
        
        # Validate required fields
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Save UserProfile data
        if 'basic_info' in data:
            profile_data = data['basic_info']
            
            # Validate age range
            if 'age' in profile_data:
                age = int(profile_data['age'])
                if age < 13 or age > 120:
                    return jsonify({'success': False, 'error': 'Age must be between 13 and 120'}), 400
            
            # Validate height range (in cm)
            if 'height_cm' in profile_data:
                height = float(profile_data['height_cm'])
                if height < 100 or height > 250:
                    return jsonify({'success': False, 'error': 'Height must be between 100-250 cm'}), 400
            
            # Validate weight range (in kg)
            if 'weight_kg' in profile_data:
                weight = float(profile_data['weight_kg'])
                if weight < 30 or weight > 300:
                    return jsonify({'success': False, 'error': 'Weight must be between 30-300 kg'}), 400
            
            # Validate enum fields
            if 'biological_sex' in profile_data and profile_data['biological_sex'] not in BIOLOGICAL_SEX_OPTIONS:
                return jsonify({'success': False, 'error': 'Invalid biological sex'}), 400
            
            if 'activity_level' in profile_data and profile_data['activity_level'] not in ACTIVITY_LEVELS:
                return jsonify({'success': False, 'error': 'Invalid activity level'}), 400
            
            # Prepare profile document
            profile_doc = {
                'user_id': user_id,
                'age': profile_data.get('age'),
                'height_cm': profile_data.get('height_cm'),
                'weight_kg': profile_data.get('weight_kg'),
                'biological_sex': profile_data.get('biological_sex'),
                'activity_level': profile_data.get('activity_level'),
                'health_conditions': profile_data.get('health_conditions', []),
                'medications': profile_data.get('medications', ''),
                'supplements': profile_data.get('supplements', []),
                'updated_at': now
            }
            
            # Check if profile exists, update or insert
            existing = db.user_profiles.find_one({'user_id': user_id})
            if existing:
                profile_doc['created_at'] = existing.get('created_at', now)
                db.user_profiles.update_one({'user_id': user_id}, {'$set': profile_doc})
            else:
                profile_doc['created_at'] = now
                db.user_profiles.insert_one(profile_doc)
        
        # Save NutritionGoals data
        if 'goals' in data:
            goals_data = data['goals']
            
            # Validate goal type
            if 'goal_type' in goals_data and goals_data['goal_type'] not in GOAL_TYPES:
                return jsonify({'success': False, 'error': 'Invalid goal type'}), 400
            
            goals_doc = {
                'user_id': user_id,
                'goal_type': goals_data.get('goal_type'),
                'target_weight_kg': goals_data.get('target_weight_kg'),
                'timeline_weeks': goals_data.get('timeline_weeks'),
                'daily_calories': goals_data.get('daily_calories'),
                'protein_grams': goals_data.get('protein_grams'),
                'carbs_grams': goals_data.get('carbs_grams'),
                'fat_grams': goals_data.get('fat_grams'),
                'fiber_grams': goals_data.get('fiber_grams'),
                'sodium_mg': goals_data.get('sodium_mg'),
                'sugar_grams': goals_data.get('sugar_grams'),
                'secondary_goals': goals_data.get('secondary_goals', []),
                'updated_at': now
            }
            
            # Remove existing goals for this user and insert new ones
            db.nutrition_goals.delete_many({'user_id': user_id})
            if any(goals_doc.values()):  # Only insert if there's actual data
                goals_doc['created_at'] = now
                db.nutrition_goals.insert_one(goals_doc)
        
        # Save DietPreferences data
        if 'preferences' in data:
            pref_data = data['preferences']
            
            # Validate diet type
            if 'diet_type' in pref_data and pref_data['diet_type'] not in DIET_TYPES:
                return jsonify({'success': False, 'error': 'Invalid diet type'}), 400
            
            # Validate meal timing
            if 'meal_timing_preference' in pref_data and pref_data['meal_timing_preference'] not in MEAL_TIMING:
                return jsonify({'success': False, 'error': 'Invalid meal timing preference'}), 400
            
            # Validate cooking skill
            if 'cooking_skill' in pref_data and pref_data['cooking_skill'] not in COOKING_SKILLS:
                return jsonify({'success': False, 'error': 'Invalid cooking skill level'}), 400
            
            pref_doc = {
                'user_id': user_id,
                'diet_type': pref_data.get('diet_type'),
                'allergies': pref_data.get('allergies', []),
                'food_restrictions': pref_data.get('food_restrictions', []),
                'meal_timing_preference': pref_data.get('meal_timing_preference'),
                'cooking_skill': pref_data.get('cooking_skill'),
                'prep_time_limit': pref_data.get('prep_time_limit'),
                'budget_per_meal': pref_data.get('budget_per_meal'),
                'living_situation': pref_data.get('living_situation'),
                'meal_prep_preference': pref_data.get('meal_prep_preference'),
                'class_schedule': pref_data.get('class_schedule', {}),
                'updated_at': now
            }
            
            # Upsert diet preferences
            existing = db.diet_preferences.find_one({'user_id': user_id})
            if existing:
                pref_doc['created_at'] = existing.get('created_at', now)
                db.diet_preferences.update_one({'user_id': user_id}, {'$set': pref_doc})
            else:
                pref_doc['created_at'] = now
                db.diet_preferences.insert_one(pref_doc)
        
        return jsonify({'success': True, 'message': 'Profile saved successfully'})
        
    except Exception as e:
        print(f"❌ Profile save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/api/load')
@login_required
def load_profile():
    """Load user profile data (user-specific only)"""
    try:
        user_id = ObjectId(current_user.id)
        
        # Load all profile data for current user only
        profile = db.user_profiles.find_one({'user_id': user_id})
        goals = db.nutrition_goals.find_one({'user_id': user_id})
        preferences = db.diet_preferences.find_one({'user_id': user_id})
        
        # Convert ObjectIds to strings and clean up data
        result = {}
        
        if profile:
            profile['_id'] = str(profile['_id'])
            profile['user_id'] = str(profile['user_id'])
            result['profile'] = profile
        
        if goals:
            goals['_id'] = str(goals['_id'])
            goals['user_id'] = str(goals['user_id'])
            result['goals'] = goals
        
        if preferences:
            preferences['_id'] = str(preferences['_id'])
            preferences['user_id'] = str(preferences['user_id'])
            result['preferences'] = preferences
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"❌ Profile load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/view')
@login_required
def view_profile():
    """View completed profile summary"""
    user_id = ObjectId(current_user.id)
    
    # Load all profile data for current user only
    profile = db.user_profiles.find_one({'user_id': user_id})
    goals = db.nutrition_goals.find_one({'user_id': user_id})
    preferences = db.diet_preferences.find_one({'user_id': user_id})
    
    if not profile:
        flash('Please complete your profile setup first.', 'info')
        return redirect(url_for('profile.setup'))
    
    return render_template('profile/view.html', 
                         user=current_user,
                         profile=profile,
                         goals=goals,
                         preferences=preferences)

def calculate_bmr(weight_kg, height_cm, age, biological_sex):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if biological_sex == 'male':
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female or other
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

def calculate_daily_calories(bmr, activity_level):
    """Calculate daily calorie needs based on activity level"""
    multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extremely_active': 1.9
    }
    return int(bmr * multipliers.get(activity_level, 1.2))

@profile_bp.route('/api/calculate-needs', methods=['POST'])
@login_required
def calculate_nutritional_needs():
    """Calculate personalized nutritional needs based on profile"""
    try:
        data = request.get_json()
        
        # Extract data
        weight_kg = float(data.get('weight_kg', 0))
        height_cm = float(data.get('height_cm', 0))
        age = int(data.get('age', 0))
        biological_sex = data.get('biological_sex', 'female')
        activity_level = data.get('activity_level', 'sedentary')
        goal_type = data.get('goal_type', 'maintain_weight')
        
        # Calculate BMR and daily calories
        bmr = calculate_bmr(weight_kg, height_cm, age, biological_sex)
        maintenance_calories = calculate_daily_calories(bmr, activity_level)
        
        # Adjust calories based on goal
        calorie_adjustments = {
            'lose_weight_slow': -250,
            'lose_weight_moderate': -500,
            'lose_weight_fast': -750,
            'maintain_weight': 0,
            'gain_weight_slow': 250,
            'gain_weight_moderate': 500,
            'build_muscle': 300
        }
        
        target_calories = maintenance_calories + calorie_adjustments.get(goal_type, 0)
        
        # Calculate macronutrient distribution (standard balanced approach)
        protein_grams = int(weight_kg * 1.6)  # 1.6g per kg body weight
        protein_calories = protein_grams * 4
        
        fat_calories = int(target_calories * 0.25)  # 25% from fat
        fat_grams = int(fat_calories / 9)
        
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = int(carb_calories / 4)
        
        # Calculate other nutrients
        fiber_grams = max(25, int(target_calories / 1000 * 14))  # 14g per 1000 calories
        sodium_mg = 2300  # Standard recommendation
        sugar_grams = int(target_calories * 0.1 / 4)  # 10% of calories from added sugar max
        
        return jsonify({
            'success': True,
            'calculations': {
                'bmr': int(bmr),
                'maintenance_calories': maintenance_calories,
                'target_calories': target_calories,
                'protein_grams': protein_grams,
                'carbs_grams': carb_grams,
                'fat_grams': fat_grams,
                'fiber_grams': fiber_grams,
                'sodium_mg': sodium_mg,
                'sugar_grams': sugar_grams
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
