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
    print("⚠️  Warning: GEMINI_API_KEY not found in environment variables!")
    print("📝 Create a .env file with: GEMINI_API_KEY=your_api_key_here")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully")

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
                    "max_output_tokens": 4000,
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
                print("🔧 Converting RGBA to RGB for compatibility")
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
            
            print(f"✅ Image processed: {img.mode} mode, size: {img.size}")
            return img
            
        except Exception as e:
            print(f"⚠️  Image enhancement error: {e}")
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
            print(f"📂 Loading image from: {image_path}")
            
            # Load and enhance image
            img = Image.open(image_path)
            print(f"📷 Original image: {img.mode} mode, size: {img.size}")
            
            img = self.enhance_image(img)
            
            # VERCEL FIX: Save processed image to /tmp
            processed_path = image_path.replace('.', '_processed.')
            if not processed_path.lower().endswith(('.jpg', '.jpeg')):
                processed_path = processed_path + '.jpg'
            
            img.save(processed_path, 'JPEG', quality=90)
            print(f"💾 Processed image saved: {processed_path}")
            
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
                
                print("✅ Analysis completed successfully")
                return {"success": True, "analysis": response.text, "data": analysis_data}
            else:
                return {"error": "AI returned empty response. Please try again."}
                
        except Exception as e:
            print(f"❌ Analysis error: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
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
            
            print(f"📊 Extracted nutrition data: {nutrition_data}")
            
        except Exception as e:
            print(f"⚠️  Data extraction warning: {e}")
        
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
                print(f"📁 File uploaded: {image_path}")
        
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
                print(f"🌐 URL image processed and saved: {image_path}")
                
            except Exception as e:
                return jsonify({"error": f"Failed to download image: {str(e)}"})
        
        if not image_path:
            return jsonify({"error": "Please provide an image file or URL"})
        
        # Get form data
        diet_goal = request.form.get('diet_goal', 'keto')
        user_preferences = request.form.get('user_preferences', '').strip()
        
        print(f"🎯 Analyzing for {diet_goal} diet")
        
        # Analyze meal
        result = analyzer.analyze_meal(image_path, diet_goal, user_preferences)
        
        if result.get("success"):
            # Only save to database if user is signed in
            db_save_result = None
            if current_user and getattr(current_user, 'is_authenticated', False):
                db_save_result = save_to_history(result["data"], None)
            
            # Track usage after successful analysis
            track_usage('analyses')
            
            return jsonify({
                "success": True,
                "analysis": result["analysis"],
                "chart_url": None,
                "nutrition_data": analyzer.extract_nutrition_data(result["analysis"]),
                "diet_info": analyzer.get_diet_info(diet_goal),
                "database_id": db_save_result.get("id") if db_save_result and db_save_result.get("success") else None
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
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
        print(f"❌ History error: {e}")
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
        print(f"❌ API History error: {e}")
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
        "status": "Flask is working on Vercel! 🎉",
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
            print(f"💾 Analysis saved to MongoDB with ID: {result['id']}")
        else:
            print(f"⚠️ Database save error: {result['error']}")
        
        return result
            
    except Exception as e:
        print(f"⚠️ History save error: {e}")
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

if __name__ == '__main__':
    print("🍽️  Diet Designer Web App Starting...")
    print("🐍 Python version:", __import__('sys').version)
    print("📦 Flask version:", __import__('flask').__version__)
    
    if GEMINI_API_KEY:
        print("✅ Gemini API key configured")
    else:
        print("❌ Gemini API key missing - create .env file")
    
    if db.client:
        print("✅ MongoDB Atlas connected")
    else:
        print("❌ MongoDB Atlas connection failed")
    
    print("🌐 Starting server at: http://localhost:5001")
    print("📱 Access from mobile: http://your-ip:5001")
    print("📝 MongoDB Atlas integration enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5001)