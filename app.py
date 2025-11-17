from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, make_response, current_app, session
import google.generativeai as genai
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
import os
import json
from datetime import datetime
import re
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import tempfile

# Auth-related imports
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from itsdangerous import URLSafeSerializer
from authlib.integrations.flask_client import OAuth
from bson import ObjectId

# MongoDB import
from database import get_db

# Usage tracking import
from usage_tracker import check_limit, track_usage, get_usage_summary
from diet_config import score_meal_adherence
from diet_config import (
    DIET_CONFIGURATIONS,
    calculate_bmr,
    calculate_tdee,
    calculate_macro_grams,
    compute_macro_adherence_10pt,
    detect_allergens_from_text,
    portion_feedback,
    goal_specific_advice,
    goal_adjustment_calories,
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'diet-designer-secret-key-2024')

# VERCEL FIX: Use /tmp directory for uploads (only writable directory)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# VERCEL FIX: Only create directories if not on Vercel
if not os.environ.get('VERCEL'):
    # Local development
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.config['UPLOAD_FOLDER'] = 'uploads'
else:
    # Vercel deployment - use /tmp (only writable directory)
    os.makedirs('/tmp/uploads', exist_ok=True)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables!")
    print("Create a .env file with: GEMINI_API_KEY=your_api_key_here")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured successfully")

# Initialize MongoDB database
db = get_db()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Serializer for guest session cookie
GUEST_COOKIE_NAME = 'guest_session'
serializer = URLSafeSerializer(app.secret_key, salt='guest-session')

# OAuth client will be configured in auth blueprint

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc.get('_id'))
        self.google_sub = user_doc.get('google_sub')
        self.email = user_doc.get('email')
        self.name = user_doc.get('name')
        self.picture = user_doc.get('picture')

    def get_id(self):
        return self.id
        
    @property
    def is_authenticated(self):
        """Always return True for authenticated users"""
        return True
        
    @property 
    def is_active(self):
        """Always return True - all users are active"""
        return True
        
    @property
    def is_anonymous(self):
        """Always return False for authenticated users"""
        return False


@login_manager.user_loader
def load_user(user_id):
    try:
        user_doc = db.users.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
    except Exception:
        return None


@app.context_processor
def inject_user():
    """Make current_user available in all templates"""
    from flask_login import current_user as _current_user
    return dict(current_user=_current_user)


# Register auth blueprint after User class is defined
from auth import auth_bp, init_oauth
init_oauth(app)  # Initialize OAuth with the Flask app
app.register_blueprint(auth_bp)

# Register profile blueprint
from profile import profile_bp
app.register_blueprint(profile_bp)


def ensure_guest_cookie(response=None):
    """Ensure guest_session cookie exists for anonymous visitors."""
    cookie = request.cookies.get(GUEST_COOKIE_NAME)
    if not cookie:
        gid = str(uuid.uuid4())
        signed = serializer.dumps(gid)
        if response is None:
            response = make_response()
        response.set_cookie(GUEST_COOKIE_NAME, signed, httponly=True, samesite='Lax', secure=bool(os.getenv('PRODUCTION')))
    return response


def current_identity():
    """Return dict with identity type and id: {'type':'user','id':...} or {'type':'guest','id':...}"""
    if current_user and getattr(current_user, 'is_authenticated', False):
        return {'type': 'user', 'id': current_user.get_id()}
    # else guest
    cookie = request.cookies.get(GUEST_COOKIE_NAME)
    if cookie:
        try:
            gid = serializer.loads(cookie)
            return {'type': 'guest', 'id': gid}
        except Exception:
            # invalid cookie - create a new one
            gid = str(uuid.uuid4())
            return {'type': 'guest', 'id': gid}
    # fallback
    gid = str(uuid.uuid4())
    return {'type': 'guest', 'id': gid}

class DietAnalyzer:
    def __init__(self):
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config={
                    # Increased to allow large table + payload output
                    "max_output_tokens": 8192,
                    "temperature": 0.7,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
                ]
            )
        else:
            self.model = None
    
    def enhance_image(self, img):
        """Apply basic image enhancements and fix format issues"""
        try:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                print("Converting RGBA to RGB for compatibility")
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == 'P':
                img = img.convert('RGB')
            elif img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Enhance contrast and brightness
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            
            # Resize for optimal processing
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            print(f"Image processed: {img.mode} mode, size: {img.size}")
            return img
            
        except Exception as e:
            print(f"Image enhancement error: {e}")
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
    
    def get_diet_info(self, dietary_goal):
        """Get comprehensive diet information"""
        diet_data = {
            "keto": {
                "name": "Ketogenic",
                "rules": "KETO RULES: <20g net carbs daily, 70-80% calories from healthy fats, moderate protein",
                "focus": "Focus on avocados, nuts, olive oil, fatty fish, low-carb vegetables",
                "icon": "🥑",
                "color": "#FF6B35"
            },
            "vegan": {
                "name": "Vegan",
                "rules": "VEGAN RULES: No animal products (meat, dairy, eggs, honey)",
                "focus": "Focus on legumes, nuts, seeds, whole grains, fruits, vegetables",
                "icon": "🌱",
                "color": "#4CAF50"
            },
            "paleo": {
                "name": "Paleo",
                "rules": "PALEO RULES: No processed foods, grains, legumes, dairy, refined sugar",
                "focus": "Focus on grass-fed meats, wild fish, eggs, vegetables, fruits, nuts",
                "icon": "🥩",
                "color": "#D84315"
            },
            "mediterranean": {
                "name": "Mediterranean",
                "rules": "MEDITERRANEAN: High in olive oil, fish, vegetables, whole grains, moderate wine",
                "focus": "Focus on olive oil, fish, vegetables, legumes, whole grains, herbs",
                "icon": "🫒",
                "color": "#1976D2"
            },
            "low-carb": {
                "name": "Low Carb",
                "rules": "LOW-CARB: <100g carbs daily, emphasis on protein and healthy fats",
                "focus": "Focus on lean proteins, healthy fats, non-starchy vegetables",
                "icon": "⚖️",
                "color": "#9C27B0"
            }
        }
        
        return diet_data.get(dietary_goal, {
            "name": "Healthy",
            "rules": "HEALTHY EATING: Balanced nutrition, whole foods",
            "focus": "Focus on nutrient-dense whole foods",
            "icon": "🍎",
            "color": "#607D8B"
        })
    
    def analyze_meal(self, image_path, dietary_goal, user_preferences=""):
        """Analyze meal with comprehensive AI assessment"""
        if not self.model:
            return {"error": "Gemini API not configured. Please set GEMINI_API_KEY in .env file"}
        
        try:
            print(f"Loading image from: {image_path}")
            
            # Load and enhance image
            img = Image.open(image_path)
            print(f"Original image: {img.mode} mode, size: {img.size}")
            
            img = self.enhance_image(img)
            
            # VERCEL FIX: Save processed image to /tmp
            processed_path = image_path.replace('.', '_processed.')
            if not processed_path.lower().endswith(('.jpg', '.jpeg')):
                processed_path = processed_path + '.jpg'
            
            img.save(processed_path, 'JPEG', quality=90)
            print(f"Processed image saved: {processed_path}")
            
            diet_info = self.get_diet_info(dietary_goal)
            
            # Enhanced analysis prompt without markdown formatting
            prompt = f"""COMPREHENSIVE MEAL ANALYSIS FOR {diet_info['name'].upper()} DIET {diet_info['icon']}

Please analyze this meal image and provide a detailed, well-structured analysis using clean text formatting (NO MARKDOWN SYMBOLS like ** or *):

MEAL IDENTIFICATION:
List all visible food items with estimated portions and cooking methods.

NUTRITIONAL ESTIMATION:
Provide estimates for:
• Total Calories: [number] kcal
• Carbohydrates: [number]g (including fiber)
• Protein: [number]g 
• Fat: [number]g
• Key vitamins/minerals present
• Sodium level: [Low/Medium/High]

DIET COMPATIBILITY SCORE: [X]/10
{diet_info['rules']}

POSITIVE ASPECTS:
• What makes this meal good for {dietary_goal} diet
• Health benefits identified
• Nutritionally strong points

AREAS FOR IMPROVEMENT:
• What doesn't align with {dietary_goal} diet
• Specific concerns or issues
• Missing nutrients

PERSONALIZED RECOMMENDATIONS:
{diet_info['focus']}
1. Ingredient Modifications: Specific swaps to make
2. Portion Adjustments: What to increase/decrease
3. Preparation Changes: Better cooking methods
4. Additions: What to add to make it more {dietary_goal}-friendly

OVERALL HEALTH SCORE: [X]/10
Explanation of why this score was given.

PERSONALIZED ADVICE:
{f'Based on your preferences: {user_preferences}' if user_preferences else 'General recommendations for optimal nutrition'}

SUMMARY:
One paragraph summary of the meal's suitability for {dietary_goal} diet and key takeaways.

Please be specific with numbers, practical with suggestions, and format the response clearly with the section headers shown above. Use NO markdown symbols like asterisks or underscores."""

            # Generate analysis
            response = self.model.generate_content([prompt, img])
            
            if response.text:
                # Store analysis data
                analysis_data = {
                    "timestamp": datetime.now().isoformat(),
                    "dietary_goal": dietary_goal,
                    "diet_info": diet_info,
                    "analysis": response.text,
                    "user_preferences": user_preferences,
                    "image_path": processed_path
                }
                
                print("Analysis completed successfully")
                return {"success": True, "analysis": response.text, "data": analysis_data}
            else:
                return {"error": "AI returned empty response. Please try again."}
                
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}

    def analyze_meal_with_profile(self, image_path, user_context, meal_context: str = ""):
        """Analyze meal using full user profile and return structured JSON.
        user_context keys expected: age, gender, weight_kg, height_cm, activity_level, diet_type,
        daily_calorie_target, protein_target, carb_target, fat_target, allergies, health_conditions, restrictions
        """
        if not self.model:
            return {"error": "Gemini API not configured. Please set GEMINI_API_KEY in .env file"}

        try:
            img = Image.open(image_path)
            img = self.enhance_image(img)
            processed_path = image_path.replace('.', '_processed.')
            if not processed_path.lower().endswith(('.jpg', '.jpeg')):
                processed_path = processed_path + '.jpg'
            img.save(processed_path, 'JPEG', quality=90)

            # Build prompt to produce Markdown + DATA_PAYLOAD tail
            uc = user_context or {}
            system_profile = f"""
You are a professional nutritionist. Analyze the MEAL IMAGE with the USER PROFILE below and output
ONLY: (1) a clean Markdown report and (2) a fenced JSON code block labeled DATA_PAYLOAD.

USER PROFILE:
- Age: {uc.get('age','N/A')}, Gender: {uc.get('gender','N/A')}
- Weight: {uc.get('weight_kg','N/A')}kg, Height: {uc.get('height_cm','N/A')}cm
- Activity: {uc.get('activity_level','N/A')}
- Diet Type: {uc.get('diet_type','N/A')}
- Daily Targets: {uc.get('daily_calorie_target','N/A')} cal, {uc.get('protein_target','N/A')}g protein, {uc.get('carb_target','N/A')}g carbs, {uc.get('fat_target','N/A')}g fat
- Allergies: {', '.join(uc.get('allergies',[]) or []) or 'None'}
- Health Conditions: {', '.join(uc.get('health_conditions',[]) or []) or 'None'}
- Food Restrictions: {', '.join(uc.get('restrictions',[]) or []) or 'None'}
- Meal Context: {meal_context or 'general'}

STRICT OUTPUT CONTRACT:
- Markdown sections (exact order):
  1) # <Diet Type> Diet Analysis
  2) **Meal Breakdown** table (Item | Portion | Method | Notes)
  3) **Macros & Key Nutrients** table (Total Calories | Carbs (g) | Protein (g) | Fat (g) | Fiber (g) | Sodium (mg))
     - Add sodium/fiber notes when applicable
  4) **Diet Compatibility Score** bold (e.g., **Score: 5/10**)
  5) **Positives**
  6) **Areas for Improvement**
  7) **Personalized Recommendations** with three bold sublists:
     - **Ingredient Swaps**, **Portion Tweaks**, **Cooking Methods** (3–5 bullets each)
  8) **Overall Health Score** (1–2 sentences)
- Do NOT include dates/timestamps anywhere in the markdown.
- After the markdown, append a fenced code block named DATA_PAYLOAD with keys:
  {"diet_type","calories_kcal","carbs_g","protein_g","fat_g","fiber_g","sodium_mg","adherence_score","flags","top_violations","top_suggestions"}
- No extra commentary; keep lines under ~100 chars.
"""

            response = self.model.generate_content([system_profile, img])
            # Robust text extraction for multi-part responses
            raw = ""
            try:
                if hasattr(response, 'text') and response.text:
                    raw = response.text
                elif getattr(response, 'candidates', None):
                    parts = getattr(response.candidates[0].content, 'parts', [])
                    texts = []
                    for p in parts:
                        t = getattr(p, 'text', None)
                        if t:
                            texts.append(t)
                    raw = "\n".join(texts)
            except Exception:
                raw = ""

            # Extract DATA_PAYLOAD and markdown
            import re
            md = raw or ""
            payload = {}
            m = re.search(r"```\s*DATA_PAYLOAD[\w\s]*\n([\s\S]*?)```", raw or "")
            if m:
                json_part = m.group(1)
                try:
                    payload = json.loads(json_part)
                except Exception:
                    payload = {}
                md = (raw[:m.start()]).strip()
            else:
                # Fallback: any fenced JSON code block
                m2 = re.search(r"```\s*(?:json)?\s*\n(\{[\s\S]*?\})\s*```", raw or "")
                if m2:
                    try:
                        payload = json.loads(m2.group(1))
                        md = (raw[:m2.start()]).strip()
                    except Exception:
                        payload = {}
                else:
                    # Fallback: last JSON-like object in text
                    start = (raw or '').rfind('{')
                    end = (raw or '').rfind('}')
                    if start != -1 and end != -1 and end > start:
                        try:
                            payload = json.loads((raw or '')[start:end+1])
                            md = (raw[:start]).strip()
                        except Exception:
                            payload = {}
            
            # Remove any remaining fenced code blocks (e.g., unlabeled JSON) from the visible markdown section
            md = re.sub(r"```[\s\S]*?```", "", md).strip()
            # Remove standalone ISO-like date lines if any slipped in
            md = "\n".join([ln for ln in md.splitlines() if not re.match(r"^\s*20\d{2}[-/].*", ln)]).strip()

            # Normalize payload keys for downstream logic
            def _num(x):
                try:
                    return float(x)
                except Exception:
                    return None
            if payload:
                # Map alt shapes to flat keys
                tn = payload.get('total_nutrition') or {}
                if 'calories_kcal' not in payload:
                    if 'calories' in payload:
                        payload['calories_kcal'] = _num(payload.get('calories'))
                    elif 'calories' in tn:
                        payload['calories_kcal'] = _num(tn.get('calories'))
                for k_src, k_dst in [('carbs','carbs_g'), ('protein','protein_g'), ('fat','fat_g'), ('fiber','fiber_g'), ('sodium','sodium_mg')]:
                    if k_dst not in payload:
                        if k_src in payload:
                            payload[k_dst] = _num(payload.get(k_src))
                        elif k_src in tn:
                            payload[k_dst] = _num(tn.get(k_src))
                # Ensure numbers are numeric
                for key in ['calories_kcal','carbs_g','protein_g','fat_g','fiber_g','sodium_mg']:
                    if key in payload:
                        payload[key] = _num(payload.get(key))

            def _looks_structured(_md: str, _payload: dict) -> bool:
                has_tables = ('|' in (_md or '')) and ('Meal Breakdown' in (_md or '') or 'Macros' in (_md or ''))
                has_core = bool(_payload) and any(k in _payload for k in ['calories_kcal','carbs_g','protein_g','fat_g'])
                return has_tables and has_core

            # If the first pass doesn't satisfy structure, attempt a repair pass
            if not _looks_structured(md, payload):
                try:
                    repair_prompt = f"""
You are a formatter. Take the ANALYSIS CONTENT below and output EXACTLY:
1) Clean Markdown with these sections in order:
   # <Diet Type> Diet Analysis
   Meal Breakdown (as a Markdown table with headers: Item | Portion | Method | Notes)
   Macros & Key Nutrients (as a Markdown table with headers: Nutrient | Amount)
   Diet Compatibility Score: X/10
   Positives (bullets)
   Areas for Improvement (bullets)
   Personalized Recommendations with bold subheads (Ingredient Swaps, Portion Tweaks, Cooking Methods)
   Overall Health Score (1–2 sentences)
2) Then append a fenced code block named DATA_PAYLOAD containing JSON with keys:
   {{"diet_type","calories_kcal","carbs_g","protein_g","fat_g","fiber_g","sodium_mg","adherence_score","flags","top_violations","top_suggestions"}}
No extra commentary. Keep lines < 100 chars. Do not include any other code blocks.

USER PROFILE SUMMARY:
- Diet Type: {uc.get('diet_type','N/A')}, Goal: {uc.get('goal_type','maintain_weight')}, Activity: {uc.get('activity_level','N/A')}
- Allergies: {', '.join(uc.get('allergies',[]) or []) or 'None'} | Restrictions: {', '.join(uc.get('restrictions',[]) or []) or 'None'}
- Meal Context: {meal_context or 'general'}

ANALYSIS CONTENT:
{raw}
"""
                    response2 = self.model.generate_content(repair_prompt)
                    raw2 = ''
                    if hasattr(response2, 'text') and response2.text:
                        raw2 = response2.text
                    elif getattr(response2, 'candidates', None):
                        parts = getattr(response2.candidates[0].content, 'parts', [])
                        raw2 = "\n".join([getattr(p, 'text', '') for p in parts if getattr(p, 'text', '')])

                    # Parse repaired
                    md2 = raw2 or ""
                    payload2 = {}
                    m3 = re.search(r"```\s*DATA_PAYLOAD[\w\s]*\n([\s\S]*?)```", raw2 or "")
                    if m3:
                        try:
                            payload2 = json.loads(m3.group(1))
                        except Exception:
                            payload2 = {}
                        md2 = (raw2[:m3.start()]).strip()
                    else:
                        m4 = re.search(r"```\s*(?:json)?\s*\n(\{[\s\S]*?\})\s*```", raw2 or "")
                        if m4:
                            try:
                                payload2 = json.loads(m4.group(1))
                                md2 = (raw2[:m4.start()]).strip()
                            except Exception:
                                payload2 = {}
                    md2 = re.sub(r"```[\s\S]*?```", "", md2).strip()

                    # Normalize payload2 keys
                    if payload2:
                        tn2 = payload2.get('total_nutrition') or {}
                        if 'calories_kcal' not in payload2:
                            if 'calories' in payload2:
                                payload2['calories_kcal'] = _num(payload2.get('calories'))
                            elif 'calories' in tn2:
                                payload2['calories_kcal'] = _num(tn2.get('calories'))
                        for k_src, k_dst in [('carbs','carbs_g'), ('protein','protein_g'), ('fat','fat_g'), ('fiber','fiber_g'), ('sodium','sodium_mg')]:
                            if k_dst not in payload2:
                                if k_src in payload2:
                                    payload2[k_dst] = _num(payload2.get(k_src))
                                elif k_src in tn2:
                                    payload2[k_dst] = _num(tn2.get(k_src))
                        for key in ['calories_kcal','carbs_g','protein_g','fat_g','fiber_g','sodium_mg']:
                            if key in payload2:
                                payload2[key] = _num(payload2.get(key))

                    # If repair looks good, replace
                    if _looks_structured(md2, payload2):
                        md, payload = md2, payload2
                except Exception:
                    pass

            if not _looks_structured(md, payload):
                return {"success": False, "error": "structured_markdown_missing", "raw_text": raw, "processed_image": processed_path}

            return {"success": True, "markdown": md, "data_payload": payload, "processed_image": processed_path}

        except Exception as e:
            print(f"Profile analysis error: {str(e)}")
            return {"error": f"Profile analysis failed: {str(e)}"}
    
    def extract_nutrition_data(self, analysis_text):
        """Extract key numerical data for display cards"""
        nutrition_data = {}
        
        try:
            # Extract calories
            calories_match = re.search(r'calories?:?\s*(\d+)', analysis_text, re.IGNORECASE)
            if calories_match:
                nutrition_data['calories'] = int(calories_match.group(1))
            
            # Extract macronutrients
            macros = {
                'carbs': r'carbohydrates?:?\s*(\d+)g',
                'protein': r'protein:?\s*(\d+)g', 
                'fat': r'fat:?\s*(\d+)g'
            }
            
            for macro, pattern in macros.items():
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match:
                    nutrition_data[macro] = int(match.group(1))
            
            # Extract scores
            compatibility_match = re.search(r'compatibility.*?(\d+)/10', analysis_text, re.IGNORECASE)
            if compatibility_match:
                nutrition_data['compatibility_score'] = int(compatibility_match.group(1))
                
            health_match = re.search(r'health.*?score.*?(\d+)/10', analysis_text, re.IGNORECASE)
            if health_match:
                nutrition_data['health_score'] = int(health_match.group(1))

            # Extract sodium level if present (Low/Medium/High)
            sodium_match = re.search(r'sodium\s+level:\s*(low|medium|high)', analysis_text, re.IGNORECASE)
            if sodium_match:
                nutrition_data['sodium_level'] = sodium_match.group(1).lower()
            
            print(f"Extracted nutrition data: {nutrition_data}")
            
        except Exception as e:
            print(f"Data extraction warning: {e}")
        
        return nutrition_data

# Initialize analyzer
analyzer = DietAnalyzer()

@app.route('/')
def index():
    """Main page with meal analysis form"""
    # Ensure guest cookie for anonymous users
    resp = make_response(render_template('index.html'))
    ensure_guest_cookie(resp)
    return resp

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle meal analysis requests with usage limits"""
    try:
        # Check usage limits first
        limit_check = check_limit('analyses')
        if not limit_check['allowed']:
            return jsonify({
                'error': 'limit_exceeded',
                'feature': 'analyze',
                'limit': limit_check['limit'],
                'current': limit_check['current'],
                'user_type': limit_check['user_type'],
                'message': f"Daily limit reached ({limit_check['current']}/{limit_check['limit']}). {'Sign in for higher limits.' if limit_check['user_type'] == 'guest' else 'Try again tomorrow.'}"
            }), 429  # Too Many Requests
        
        image_path = None
        
        # Handle file upload - VERCEL COMPATIBLE
        if 'image_file' in request.files and request.files['image_file'].filename:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_base = os.path.splitext(filename)[0]
                filename = f"{timestamp}_{filename_base}.jpg"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                file.save(image_path)
                print(f"File uploaded: {image_path}")
        
        # Handle URL input
        elif request.form.get('image_url'):
            try:
                response = requests.get(request.form.get('image_url'), timeout=15)
                response.raise_for_status()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"url_image_{timestamp}.jpg"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                img = Image.open(BytesIO(response.content))
                img = analyzer.enhance_image(img)
                img.save(image_path, 'JPEG', quality=90)
                print(f"URL image processed and saved: {image_path}")
                
            except Exception as e:
                return jsonify({"error": f"Failed to download image: {str(e)}"})
        
        if not image_path:
            return jsonify({"error": "Please provide an image file or URL"})
        
        # Get form data
        diet_goal = request.form.get('diet_goal', 'keto')
        user_preferences = request.form.get('user_preferences', '').strip()
        
        print(f"Analyzing for {diet_goal} diet")
        
        # Analyze meal
        result = analyzer.analyze_meal(image_path, diet_goal, user_preferences)
        
        if result.get("success"):
            # Only save to database if user is signed in
            db_save_result = None
            if current_user and getattr(current_user, 'is_authenticated', False):
                db_save_result = save_to_history(result["data"], None)
            
            # Track usage after successful analysis
            track_usage('analyses')
            
            # Compute adherence score to selected diet
            extracted = analyzer.extract_nutrition_data(result["analysis"])
            adherence = None
            try:
                from profile import db as _db
                if current_user and getattr(current_user, 'is_authenticated', False):
                    prefs = _db.diet_preferences.find_one({'user_id': ObjectId(current_user.id)}) or {}
                    diet_slug = prefs.get('diet_type') or 'standard_american'
                else:
                    diet_slug = 'standard_american'
                adherence = score_meal_adherence({
                    'carbs': extracted.get('carbs'),
                    'protein': extracted.get('protein'),
                    'fat': extracted.get('fat'),
                    'sodium_mg': None,
                    'sodium_level': extracted.get('sodium_level')
                }, diet_slug)
            except Exception as _:
                adherence = None

            return jsonify({
                "success": True,
                "analysis": result["analysis"],
                "chart_url": None,
                "nutrition_data": extracted,
                "diet_info": analyzer.get_diet_info(diet_goal),
                "adherence": adherence,
                "database_id": db_save_result.get("id") if db_save_result and db_save_result.get("success") else None
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"})

@app.route('/history')
def history():
    """Display analysis history from MongoDB - SIGNED IN USERS ONLY"""
    try:
        # Only show history for signed-in users
        if not (current_user and getattr(current_user, 'is_authenticated', False)):
            # For guests, show empty history
            return render_template('history.html', history=[], is_guest=True)
        
        # Get history for signed-in user only
        history_data = db.collection.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1).limit(20)

        # Normalize docs
        history = []
        for doc in history_data:
            doc['_id'] = str(doc['_id'])
            if 'created_at' in doc:
                doc['timestamp'] = doc['created_at'].isoformat()
            history.append(doc)
        return render_template('history.html', history=history, is_guest=False)
    except Exception as e:
        print(f"History error: {e}")
        return render_template('history.html', history=[], is_guest=True)

@app.route('/api/history')
def api_history():
    """API endpoint to get analysis history - SIGNED IN USERS ONLY"""
    try:
        # Only return history for signed-in users
        if not (current_user and getattr(current_user, 'is_authenticated', False)):
            return jsonify({
                "success": True,
                "history": [],
                "count": 0,
                "is_guest": True
            })
        
        # Get history for signed-in user only
        cursor = db.collection.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1).limit(20)

        history = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            if 'user_id' in doc:
                doc['user_id'] = str(doc['user_id'])
            if 'created_at' in doc:
                doc['timestamp'] = doc['created_at'].isoformat()
            history.append(doc)
        
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history),
            "is_guest": False,
            "user_id": current_user.id
        })
    except Exception as e:
        print(f"API History error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "history": [],
            "is_guest": True
        })

@app.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear analysis history - SIGNED IN USERS ONLY"""
    try:
        # Only allow signed-in users to clear history
        if not (current_user and getattr(current_user, 'is_authenticated', False)):
            return jsonify({"success": False, "error": "Must be signed in to clear history"})
        
        # Clear only current user's history
        res = db.collection.delete_many({'user_id': ObjectId(current_user.id)})
        return jsonify({"success": True, "deleted_count": res.deleted_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete-analysis/<analysis_id>', methods=['POST'])
def delete_analysis(analysis_id):
    """Delete specific analysis - SIGNED IN USERS ONLY"""
    try:
        # Only allow signed-in users to delete analyses
        if not (current_user and getattr(current_user, 'is_authenticated', False)):
            return jsonify({"success": False, "error": "Must be signed in to delete analyses"})
        
        # Delete only if owned by current user
        obj_id = ObjectId(analysis_id)
        res = db.collection.delete_one({'_id': obj_id, 'user_id': ObjectId(current_user.id)})

        if res.deleted_count > 0:
            return jsonify({"success": True, "message": "Analysis deleted successfully"})
        else:
            return jsonify({"success": False, "error": "Analysis not found or not owned by you"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/stats')
def stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/debug-auth')
def debug_auth():
    """Debug authentication status"""
    debug_info = {
        "current_user_exists": current_user is not None,
        "is_authenticated": getattr(current_user, 'is_authenticated', False),
        "user_id": getattr(current_user, 'id', None),
        "user_email": getattr(current_user, 'email', None),
        "user_name": getattr(current_user, 'name', None),
        "user_picture": getattr(current_user, 'picture', None),
        "session_keys": list(session.keys()) if session else [],
    }
    return jsonify(debug_info)

@app.route('/api/me')
def api_me():
    """Get current user info"""
    if current_user and getattr(current_user, 'is_authenticated', False):
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'picture': current_user.picture
            }
        })
    else:
        # Ensure guest cookie exists
        cookie = request.cookies.get(GUEST_COOKIE_NAME)
        resp = make_response(jsonify({'authenticated': False, 'user': None}))
        if not cookie:
            gid = str(uuid.uuid4())
            signed = serializer.dumps(gid)
            resp.set_cookie(GUEST_COOKIE_NAME, signed, httponly=True, samesite='Lax', secure=bool(os.getenv('PRODUCTION')))
        return resp


@app.route('/api/usage')
def api_usage():
    """Get current usage status and limits"""
    from usage_tracker import get_current_scope, get_user_type, LIMITS
    
    user_type = get_user_type()
    scope = get_current_scope()
    usage_summary = get_usage_summary(scope)
    
    limits = LIMITS[user_type]
    
    # Calculate usage percentages and warnings
    usage_status = {}
    for feature, limit in limits.items():
        current = usage_summary.get(feature, 0)
        usage_status[feature] = {
            'current': current,
            'limit': limit,
            'percentage': (current / limit * 100) if limit > 0 else 0,
            'near_limit': current >= (limit * 0.8) if limit > 0 else False,
            'at_limit': current >= limit if limit > 0 else False
        }
    
    return jsonify({
        'user_type': user_type,
        'scope': scope,
        'usage': usage_status,
        'raw_usage': usage_summary
    })


@app.route('/api/analyze-with-profile', methods=['POST'])
def api_analyze_with_profile():
    """Analyze meal with full user profile context. Requires image and uses current user's saved data.
    If guest, falls back to standard analysis prompt without profile-specific targets.
    """
    try:
        # Validate image input
        image_path = None
        if 'image_file' in request.files and request.files['image_file'].filename:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_base = os.path.splitext(filename)[0]
                filename = f"{timestamp}_{filename_base}.jpg"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
        elif request.form.get('image_url'):
            response = requests.get(request.form.get('image_url'), timeout=15)
            response.raise_for_status()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"url_image_{timestamp}.jpg"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img = Image.open(BytesIO(response.content))
            img = analyzer.enhance_image(img)
            img.save(image_path, 'JPEG', quality=90)
        else:
            return jsonify({"success": False, "error": "Please provide an image"}), 400

        # Build user context if authenticated
        meal_context = request.form.get('meal_context', '')
        user_context = {}
        if current_user and getattr(current_user, 'is_authenticated', False):
            # Load user-specific data
            prefs = db.diet_preferences.find_one({'user_id': ObjectId(current_user.id)}) or {}
            prof = db.user_profiles.find_one({'user_id': ObjectId(current_user.id)}) or {}
            goals = db.nutrition_goals.find_one({'user_id': ObjectId(current_user.id)}) or {}
            user_context = {
                'age': prof.get('age'),
                'gender': prof.get('biological_sex'),
                'weight_kg': prof.get('weight_kg'),
                'height_cm': prof.get('height_cm'),
                'activity_level': prof.get('activity_level'),
                'diet_type': (prefs.get('diet_type') or 'standard_american'),
                'allergies': prefs.get('allergies', []),
                'health_conditions': prof.get('health_conditions', []),
                'daily_calorie_target': goals.get('daily_calories'),
                'protein_target': goals.get('protein_grams'),
                'carb_target': goals.get('carbs_grams'),
                'fat_target': goals.get('fat_grams'),
                'restrictions': prefs.get('food_restrictions', []),
                'goal_type': goals.get('goal_type') or 'maintain_weight',
            }

        result = analyzer.analyze_meal_with_profile(image_path, user_context, meal_context)
        if not result.get('success'):
            return jsonify(result), 500

        # If model returned markdown + payload, use that; else use previous fallback path
        markdown = result.get('markdown')
        payload = result.get('data_payload') or {}

        analysis_text = None
        if markdown:
            analysis_text = markdown
        structured = {}
        if payload:
            structured = payload

        if not analysis_text:
            # Enforce table-based markdown output only; remove legacy narrative fallback
            return jsonify({
                'success': False,
                'error': 'structured_markdown_missing',
                'message': 'The AI did not return the expected table-based markdown. Please try again.'
            }), 502

        # Fallback: parse macros from Markdown if payload missing
        def parse_macros_from_markdown(md_text: str):
            import re
            if not md_text:
                return {}
            t = md_text
            # Pipe-table pattern
            m = re.search(r"\|\s*Total\s*Calories\s*\|[\s\S]*?\n\|[\-:\s\|]+\n\|\s*(?P<cal>\d+(?:\.\d+)?)\s*\|\s*(?P<carb>\d+(?:\.\d+)?)\s*\|\s*(?P<pro>\d+(?:\.\d+)?)\s*\|\s*(?P<fat>\d+(?:\.\d+)?)\s*\|\s*(?P<fiber>\d+(?:\.\d+)?)\s*\|\s*(?P<sod>\d+(?:\.\d+)?)", t, re.IGNORECASE)
            if m:
                return {
                    'calories_kcal': float(m.group('cal')),
                    'carbs_g': float(m.group('carb')),
                    'protein_g': float(m.group('pro')),
                    'fat_g': float(m.group('fat')),
                    'fiber_g': float(m.group('fiber')),
                    'sodium_mg': float(m.group('sod')),
                }
            # Loose text fallback
            def pick(rx):
                mm = re.search(rx, t, re.IGNORECASE)
                return float(mm.group(1)) if mm else None
            cal = pick(r"Total\s*Calories\D+(\d+(?:\.\d+)?)")
            carb = pick(r"Carbs\s*\(g\)\D+(\d+(?:\.\d+)?)")
            pro = pick(r"Protein\s*\(g\)\D+(\d+(?:\.\d+)?)")
            fat = pick(r"Fat\s*\(g\)\D+(\d+(?:\.\d+)?)")
            fiber = pick(r"Fiber\s*\(g\)\D+(\d+(?:\.\d+)?)")
            sod = pick(r"Sodium\s*\(mg\)\D+(\d+(?:\.\d+)?)")
            got = {k:v for k,v in [('calories_kcal',cal),('carbs_g',carb),('protein_g',pro),('fat_g',fat),('fiber_g',fiber),('sodium_mg',sod)] if v is not None}
            return got

        if analysis_text and (not structured or not any(structured.get(k) for k in ['calories_kcal','carbs_g','protein_g','fat_g'])):
            parsed = parse_macros_from_markdown(analysis_text)
            if parsed:
                structured.update(parsed)

        # Compute personalization using configs and user profile (if available)
        personalization = {}
        try:
            diet_slug = user_context.get('diet_type', 'standard_american')
            daily_target_kcal = user_context.get('daily_calorie_target')
            # Fallback: compute daily target if missing using BMR/TDEE and goal adjustment
            if not daily_target_kcal:
                try:
                    if all(user_context.get(k) for k in ['weight_kg','height_cm','age','gender','activity_level']):
                        bmr = calculate_bmr(float(user_context['weight_kg']), float(user_context['height_cm']), int(user_context['age']), user_context['gender'])
                        tdee = calculate_tdee(bmr, user_context['activity_level'])
                        adj = goal_adjustment_calories(user_context.get('goal_type') or 'maintain_weight')
                        daily_target_kcal = max(1200, int(tdee + adj))
                except Exception:
                    daily_target_kcal = None
            if structured:
                macro_score = compute_macro_adherence_10pt(
                    structured.get('calories_kcal'),
                    structured.get('carbs_g'),
                    structured.get('protein_g'),
                    structured.get('fat_g'),
                    diet_slug,
                )
                portion_msg = portion_feedback(structured.get('calories_kcal'), daily_target_kcal, meal_context)
            else:
                macro_score = {"score": None, "explanation": "No structured macros"}
                portion_msg = portion_feedback(None, daily_target_kcal, meal_context)
            allergens = detect_allergens_from_text(analysis_text, user_context.get('allergies', []))
            # Dynamic goal tips based on deviations and sodium
            goal_tips = goal_specific_advice(user_context.get('goal_type'))
            try:
                tips_dynamic = []
                if macro_score and macro_score.get('explanation') and 'carbs off' in macro_score.get('explanation').lower():
                    tips_dynamic.append("Reduce refined carbs; add more non-starchy vegetables.")
                if macro_score and macro_score.get('explanation') and 'protein off' in macro_score.get('explanation').lower():
                    tips_dynamic.append("Add a lean protein portion to balance macros.")
                if structured.get('sodium_mg') and structured['sodium_mg'] > 1500:
                    tips_dynamic.append("Choose fresh items and limit salty seasonings to reduce sodium.")
                if structured.get('calories_kcal') and daily_target_kcal:
                    pct = structured['calories_kcal'] / max(1, daily_target_kcal)
                    if pct > 0.6:
                        tips_dynamic.append("Since this meal is large, keep other meals lighter today.")
                if tips_dynamic:
                    goal_tips = list(dict.fromkeys(goal_tips + tips_dynamic))
            except Exception:
                pass
            cfg = DIET_CONFIGURATIONS.get(diet_slug) or {}
            limits = cfg.get('daily_limits') or cfg.get('daily_targets')
            personalization = {
                'macro_adherence': macro_score,
                'portion_advice': portion_msg,
                'allergen_matches': allergens,
                'goal_tips': goal_tips,
                'diet_limits': limits,
            }
        except Exception as _:
            personalization = {}

        # Attach ownership and save result
        save_payload = {
            'timestamp': datetime.now().isoformat(),
            'dietary_goal': user_context.get('diet_type', 'standard_american'),
            'analysis': analysis_text,
            'analysis_json': structured,
            'personalization': personalization,
            'image_path': result.get('processed_image'),
            'meal_context': meal_context
        }
        db_result = None
        if current_user and getattr(current_user, 'is_authenticated', False):
            db_result = save_to_history(save_payload, None)

        return jsonify({
            'success': True,
            'structured': structured,
            'analysis': analysis_text,
            'personalization': personalization,
            'database_id': db_result.get('id') if db_result and db_result.get('success') else None
        })

    except Exception as e:
        print(f"analyze-with-profile error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
        
@app.route('/test-auth')
def test_auth():
    """Simple test page to verify authentication"""
    return f"""
    <h1>Authentication Test</h1>
    <p>current_user: {current_user}</p>
    <p>is_authenticated: {getattr(current_user, 'is_authenticated', 'N/A')}</p>
    <p>email: {getattr(current_user, 'email', 'N/A')}</p>
    <p>name: {getattr(current_user, 'name', 'N/A')}</p>
    <p>Session: {dict(session)}</p>
    <p><a href="/login">Login with Google</a></p>
    <p><a href="/">Back to Home</a></p>
    """

@app.route('/test')
def test():
    """Test route to check if basic Flask works"""
    return jsonify({
        "status": "Flask is working on Vercel!",
        "environment": "Vercel" if os.environ.get('VERCEL') else "Local",
        "gemini_configured": bool(GEMINI_API_KEY),
        "mongodb_uri_exists": bool(os.getenv('MONGODB_URI')),
        "upload_folder": app.config['UPLOAD_FOLDER']
    })

@app.route('/debug-db-analyses')
def debug_db_analyses():
    """Debug route to check what's in the database"""
    try:
        # Get all analyses with user_id
        cursor = db.collection.find({'user_id': {'$exists': True}}).limit(10)
        analyses = []
        for doc in cursor:
            analyses.append({
                '_id': str(doc['_id']),
                'user_id': str(doc.get('user_id', 'no_user_id')),
                'dietary_goal': doc.get('dietary_goal', 'no_goal'),
                'created_at': doc.get('created_at', 'no_date'),
                'has_analysis': bool(doc.get('analysis'))
            })
        
        return jsonify({
            "success": True,
            "total_analyses": len(analyses),
            "analyses": analyses,
            "current_user_id": str(current_user.id) if current_user and getattr(current_user, 'is_authenticated', False) else 'not_authenticated'
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/debug-users')
def debug_users():
    """Debug route to check all users in the database"""
    try:
        # Get all users
        cursor = db.users.find({}).limit(10)
        users = []
        for doc in cursor:
            users.append({
                '_id': str(doc['_id']),
                'email': doc.get('email', 'no_email'),
                'name': doc.get('name', 'no_name'),
                'google_sub': doc.get('google_sub', 'no_google_sub'),
                'created_at': doc.get('created_at', 'no_date'),
                'last_login_at': doc.get('last_login_at', 'no_login')
            })
        
        return jsonify({
            "success": True,
            "total_users": len(users),
            "users": users
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/fix-users', methods=['POST'])
def fix_users():
    """Fix corrupted users with null google_sub"""
    try:
        # Find users with null or missing google_sub
        bad_users = list(db.users.find({'$or': [{'google_sub': None}, {'google_sub': {'$exists': False}}]}))
        
        if not bad_users:
            return jsonify({"success": True, "message": "No bad users found"})
        
        # Delete bad users (they'll be recreated properly on next login)
        result = db.users.delete_many({'$or': [{'google_sub': None}, {'google_sub': {'$exists': False}}]})
        
        return jsonify({
            "success": True, 
            "message": f"Deleted {result.deleted_count} corrupted users. They will be recreated properly on next login.",
            "deleted_users": [{'email': u.get('email'), '_id': str(u['_id'])} for u in bad_users]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/debug-db')
def debug_db():
    """Enhanced database debugging"""
    try:
        # Test database connection
        db_connected = db.is_connected()
        
        debug_info = {
            "mongodb_uri_exists": bool(os.getenv('MONGODB_URI')),
            "database_connected": db_connected,
            "client_exists": bool(db.client),
        }
        
        if db_connected:
            # Test saving a document
            test_data = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Database test from Vercel",
                "dietary_goal": "test",
                "analysis": "This is a test analysis"
            }
            
            save_result = db.save_analysis(test_data)
            history = db.get_history(3)
            
            debug_info.update({
                "save_test": save_result,
                "history_count": len(history),
                "sample_history": history[:1] if history else []
            })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "mongodb_uri_exists": bool(os.getenv('MONGODB_URI'))
        })

def save_to_history(analysis_data, chart_path):
    """Save analysis to MongoDB database"""
    try:
        if chart_path:
            analysis_data['chart_path'] = chart_path
        # Attach ownership based on current identity
        ident = current_identity()
        if ident['type'] == 'user':
            analysis_data['user_id'] = ObjectId(ident['id'])
            analysis_data['guest_session_id'] = None
        else:
            analysis_data['guest_session_id'] = ident['id']
            analysis_data['user_id'] = None

        result = db.save_analysis(analysis_data)
        if result["success"]:
            print(f"Analysis saved to MongoDB with ID: {result['id']}")
        else:
            print(f"Database save error: {result['error']}")
        
        return result
            
    except Exception as e:
        print(f"History save error: {e}")
        return {"success": False, "error": str(e)}

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

# Favicon and icon routes for comprehensive device support
@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return app.send_static_file('icon32.png')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve Apple touch icon"""
    return app.send_static_file('icon256.png')

@app.route('/android-chrome-192x192.png')
def android_chrome_192():
    """Serve Android Chrome icon 192x192"""
    return app.send_static_file('icon256.png')

@app.route('/android-chrome-512x512.png')
def android_chrome_512():
    """Serve Android Chrome icon 512x512"""
    return app.send_static_file('icon512.png')

@app.route('/favicon-16x16.png')
def favicon_16():
    """Serve 16x16 favicon"""
    return app.send_static_file('icon16.png')

@app.route('/favicon-32x32.png')
def favicon_32():
    """Serve 32x32 favicon"""
    return app.send_static_file('icon32.png')

@app.route('/safari-pinned-tab.svg')
def safari_pinned_tab():
    """Serve Safari pinned tab icon"""
    return app.send_static_file('icon512.png')

@app.route('/manifest.json')
def manifest():
    """Serve web app manifest"""
    return app.send_static_file('manifest.json')

@app.route('/browserconfig.xml')
def browserconfig():
    """Serve browser config for Windows"""
    return app.send_static_file('browserconfig.xml')

# Catch-all for missing PNG favicons - serve appropriate icon
@app.route('/mstile-<size>.png')
def mstile_fallback(size):
    """Serve appropriate icon for missing MS tile icons"""
    if size in ['70x70', '150x150']:
        return app.send_static_file('icon128.png')
    elif size in ['310x310', '310x150']:
        return app.send_static_file('icon256.png')
    else:
        return app.send_static_file('icon128.png')

@app.route('/dashboard')
def dashboard():
    """Dashboard page (requires login)"""
    if not (current_user and getattr(current_user, 'is_authenticated', False)):
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@app.route('/api/dashboard/today')
def dashboard_today():
    """Today's metrics for the signed-in user only"""
    if not (current_user and getattr(current_user, 'is_authenticated', False)):
        return jsonify({'success': False, 'error': 'auth_required'}), 401
    try:
        uid = ObjectId(current_user.id)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        meals = list(db.collection.find({'user_id': uid, 'created_at': {'$gte': start, '$lt': end}}).sort('created_at', 1))
        for m in meals:
            m['_id'] = str(m['_id'])
            m['user_id'] = str(m['user_id']) if m.get('user_id') else None

        total_cal = 0.0
        carbs_g = 0.0
        protein_g = 0.0
        fat_g = 0.0
        adherence_scores = []
        for m in meals:
            sj = m.get('analysis_json') or {}
            if 'calories_kcal' in sj:
                total_cal += float(sj.get('calories_kcal') or 0)
                carbs_g += float(sj.get('carbs_g') or 0)
                protein_g += float(sj.get('protein_g') or 0)
                fat_g += float(sj.get('fat_g') or 0)
            elif sj.get('total_nutrition'):
                tn = sj['total_nutrition']
                total_cal += float(tn.get('calories') or 0)
                carbs_g += float(tn.get('carbs') or 0)
                protein_g += float(tn.get('protein') or 0)
                fat_g += float(tn.get('fat') or 0)
            pers = m.get('personalization') or {}
            ms = pers.get('macro_adherence', {}).get('score')
            if ms is not None:
                adherence_scores.append(float(ms))

        avg_adherence = round(sum(adherence_scores)/len(adherence_scores), 1) if adherence_scores else None

        prefs = db.diet_preferences.find_one({'user_id': uid}) or {}
        prof = db.user_profiles.find_one({'user_id': uid}) or {}
        goals = db.nutrition_goals.find_one({'user_id': uid}) or {}
        diet_slug = prefs.get('diet_type') or 'standard_american'
        daily_target = goals.get('daily_calories')
        if not daily_target:
            try:
                bmr = calculate_bmr(float(prof.get('weight_kg') or 0), float(prof.get('height_cm') or 0), int(prof.get('age') or 0), prof.get('biological_sex') or 'female')
                tdee = calculate_tdee(bmr, prof.get('activity_level') or 'sedentary')
                daily_target = max(1200, int(tdee + goal_adjustment_calories(goals.get('goal_type') or 'maintain_weight')))
            except Exception:
                daily_target = None

        today_key = start.strftime('%Y-%m-%d')
        hyd = db.hydration_logs.find_one({'user_id': uid, 'date': today_key}) or {'glasses': 0, 'ml': 0}

        return jsonify({
            'success': True,
            'diet_type': diet_slug,
            'totals': {
                'calories': round(total_cal, 1),
                'carbs_g': round(carbs_g, 1),
                'protein_g': round(protein_g, 1),
                'fat_g': round(fat_g, 1),
            },
            'targets': {
                'calories': daily_target,
                'macros_g': calculate_macro_grams(daily_target, diet_slug) if daily_target else None
            },
            'adherence_avg': avg_adherence,
            'meals': [
                {
                    'id': m['_id'],
                    'ts': m.get('timestamp'),
                    'analysis_json': m.get('analysis_json'),
                    'personalization': m.get('personalization'),
                    'image_path': m.get('image_path')
                } for m in meals
            ],
            'hydration': {
                'glasses': hyd.get('glasses', 0),
                'ml': hyd.get('ml', 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/hydration', methods=['POST'])
def dashboard_hydration():
    if not (current_user and getattr(current_user, 'is_authenticated', False)):
        return jsonify({'success': False, 'error': 'auth_required'}), 401
    try:
        from datetime import datetime, timezone
        uid = ObjectId(current_user.id)
        payload = request.get_json() or {}
        add_glasses = int(payload.get('add_glasses', 1))
        add_ml = int(payload.get('add_ml', 250))
        today_key = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        existing = db.hydration_logs.find_one({'user_id': uid, 'date': today_key})
        if existing:
            db.hydration_logs.update_one({'_id': existing['_id']}, {'$inc': {'glasses': add_glasses, 'ml': add_ml}})
        else:
            db.hydration_logs.insert_one({'user_id': uid, 'date': today_key, 'glasses': add_glasses, 'ml': add_ml})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/insights')
def dashboard_insights():
    """Generate smart insights for the signed-in user.
    Uses Gemini if available, with a heuristic fallback.
    """
    if not (current_user and getattr(current_user, 'is_authenticated', False)):
        return jsonify({'success': False, 'error': 'auth_required'}), 401
    try:
        from datetime import datetime, timezone, timedelta
        uid = ObjectId(current_user.id)
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        week_start = start - timedelta(days=6)

        # Fetch last 7 days
        meals = list(db.collection.find({'user_id': uid, 'created_at': {'$gte': week_start, '$lt': start + timedelta(days=1)}}).sort('created_at', 1))

        # Aggregate by day
        daily = {}
        for m in meals:
            dt = m.get('created_at')
            key = dt.date().isoformat() if dt else start.date().isoformat()
            d = daily.setdefault(key, {'calories': 0.0, 'carbs_g': 0.0, 'protein_g': 0.0, 'fat_g': 0.0, 'count': 0})
            sj = m.get('analysis_json') or {}
            if 'calories_kcal' in sj:
                d['calories'] += float(sj.get('calories_kcal') or 0)
                d['carbs_g'] += float(sj.get('carbs_g') or 0)
                d['protein_g'] += float(sj.get('protein_g') or 0)
                d['fat_g'] += float(sj.get('fat_g') or 0)
            elif sj.get('total_nutrition'):
                tn = sj['total_nutrition']
                d['calories'] += float(tn.get('calories') or 0)
                d['carbs_g'] += float(tn.get('carbs') or 0)
                d['protein_g'] += float(tn.get('protein') or 0)
                d['fat_g'] += float(tn.get('fat') or 0)
            d['count'] += 1

        # Targets
        prefs = db.diet_preferences.find_one({'user_id': uid}) or {}
        prof = db.user_profiles.find_one({'user_id': uid}) or {}
        goals = db.nutrition_goals.find_one({'user_id': uid}) or {}
        diet_slug = prefs.get('diet_type') or 'standard_american'
        daily_target = goals.get('daily_calories')
        if not daily_target:
            try:
                bmr = calculate_bmr(float(prof.get('weight_kg') or 0), float(prof.get('height_cm') or 0), int(prof.get('age') or 0), prof.get('biological_sex') or 'female')
                tdee = calculate_tdee(bmr, prof.get('activity_level') or 'sedentary')
                daily_target = max(1200, int(tdee + goal_adjustment_calories(goals.get('goal_type') or 'maintain_weight')))
            except Exception:
                daily_target = None
        macro_targets = calculate_macro_grams(daily_target, diet_slug) if daily_target else None

        # Build a concise context
        today_key = start.date().isoformat()
        today = daily.get(today_key, {'calories': 0, 'carbs_g': 0, 'protein_g': 0, 'fat_g': 0, 'count': 0})

        insights = []
        used_ai = False
        try:
            # Use Gemini if available
            if analyzer.model:
                summary = {
                    'diet_type': diet_slug,
                    'target_calories': daily_target,
                    'target_macros_g': macro_targets,
                    'today': today,
                    'week': daily
                }
                prompt = (
                    "You are a nutrition coach. Given this JSON summary of a student's meals (today and last 7 days), "
                    "generate 3-5 short, actionable insights (one line each). Focus on protein adequacy, fiber/veg, "
                    "sodium if high, balance vs diet type, and practical next steps for the rest of the day. "
                    "Return plain text bullets starting with '-' only.\n\nSUMMARY:\n" + json.dumps(summary)
                )
                resp = analyzer.model.generate_content(prompt)
                text = ''
                if hasattr(resp, 'text') and resp.text:
                    text = resp.text
                elif getattr(resp, 'candidates', None):
                    parts = getattr(resp.candidates[0].content, 'parts', [])
                    text = "\n".join([getattr(p, 'text', '') for p in parts if getattr(p, 'text', '')])
                for line in text.splitlines():
                    line = line.strip().lstrip('-').strip()
                    if line:
                        insights.append(line)
                used_ai = True
        except Exception:
            used_ai = False

        # Heuristic fallback
        if not insights:
            if daily_target:
                diff = today['calories'] - daily_target
                if diff < -200:
                    insights.append("You're under calories so far—consider a protein-rich meal later.")
                elif diff > 200:
                    insights.append("Calories are high today—choose lighter, high-fiber options next meal.")
            if macro_targets:
                if today['protein_g'] < macro_targets['protein'] * 0.5:
                    insights.append("Protein looks low—add eggs, yogurt, tofu, or lean meat.")
                if today['carbs_g'] > macro_targets['carbs'] * 0.9:
                    insights.append("Carbs are nearing target—prefer non-starchy veggies for volume.")
                if today['fat_g'] > macro_targets['fat'] * 1.1:
                    insights.append("Fat slightly high—keep dressings and oils moderate next meal.")
            if not insights:
                insights.append("Keep prioritizing whole foods and hydrate regularly today.")

        return jsonify({'success': True, 'insights': insights, 'used_ai': used_ai})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Diet Designer Web App Starting...")
    print("Python version:", __import__('sys').version)
    print("Flask version:", __import__('flask').__version__)
    
    if GEMINI_API_KEY:
        print("Gemini API key configured")
    else:
        print("Gemini API key missing - create .env file")
    
    if db.client:
        print("MongoDB Atlas connected")
    else:
        print("MongoDB Atlas connection failed")
    
    print("Starting server at: http://localhost:5001")
    print("Access from mobile: http://your-ip:5001")
    print("MongoDB Atlas integration enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
