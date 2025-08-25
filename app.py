from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
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

# MongoDB import
from database import get_db

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'diet-designer-secret-key-2024'

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

class DietAnalyzer:
    def __init__(self):
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel(
                'gemini-2.5-pro',
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
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle meal analysis requests - VERCEL VERSION"""
    try:
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
            # Save analysis to MongoDB
            db_save_result = save_to_history(result["data"], None)
            
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
    """Display analysis history from MongoDB"""
    try:
        history_data = db.get_history(20)
        return render_template('history.html', history=history_data)
    except Exception as e:
        print(f"❌ History error: {e}")
        return render_template('history.html', history=[])

@app.route('/api/history')
def api_history():
    """API endpoint to get analysis history with proper ObjectIds"""
    try:
        history_data = db.get_history(20)
        return jsonify({
            "success": True,
            "history": history_data,
            "count": len(history_data)
        })
    except Exception as e:
        print(f"❌ API History error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "history": []
        })

@app.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear all analysis history from MongoDB"""
    try:
        result = db.clear_all_history()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete-analysis/<analysis_id>', methods=['POST'])
def delete_analysis(analysis_id):
    """Delete specific analysis by MongoDB ID"""
    try:
        result = db.delete_analysis(analysis_id)
        return jsonify(result)
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
    return app.send_static_file('favicon.svg')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve Apple touch icon"""
    return app.send_static_file('favicon.svg')

@app.route('/android-chrome-192x192.png')
def android_chrome_192():
    """Serve Android Chrome icon 192x192"""
    return app.send_static_file('favicon.svg')

@app.route('/android-chrome-512x512.png')
def android_chrome_512():
    """Serve Android Chrome icon 512x512"""
    return app.send_static_file('favicon.svg')

@app.route('/favicon-16x16.png')
def favicon_16():
    """Serve 16x16 favicon"""
    return app.send_static_file('favicon.svg')

@app.route('/favicon-32x32.png')
def favicon_32():
    """Serve 32x32 favicon"""
    return app.send_static_file('favicon.svg')

@app.route('/safari-pinned-tab.svg')
def safari_pinned_tab():
    """Serve Safari pinned tab icon"""
    return app.send_static_file('favicon.svg')

@app.route('/manifest.json')
def manifest():
    """Serve web app manifest"""
    return app.send_static_file('manifest.json')

@app.route('/browserconfig.xml')
def browserconfig():
    """Serve browser config for Windows"""
    return app.send_static_file('browserconfig.xml')

# Catch-all for missing PNG favicons - serve SVG instead
@app.route('/mstile-<size>.png')
def mstile_fallback(size):
    """Serve SVG for missing MS tile icons"""
    return app.send_static_file('favicon.svg')

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