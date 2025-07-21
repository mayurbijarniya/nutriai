# Nutri AI

AI-powered nutrition analysis tool using Google Gemini AI to analyze food images and provide detailed nutritional insights.

## 🚀 Quick Setup

### Requirements
- Python 3.9+
- Google AI API key
- MongoDB URI

### Installation

1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd Diet-Designer
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create `.env` file:
   ```env
   GEMINI_API_KEY=your_google_ai_api_key
   MONGODB_URI=your_mongodb_connection_string
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access**
   Open `http://localhost:5000`

## 📱 Features

- Upload food images for AI analysis
- Support for multiple diet types (Keto, Vegan, Paleo, Mediterranean, Low-Carb)
- Detailed nutrition breakdown
- Analysis history tracking
- Modern chat interface

## 🔧 Tech Stack

- **Backend**: Flask
- **AI**: Google Gemini 2.0
- **Database**: MongoDB
- **Frontend**: Tailwind CSS
- **Deployment**: Vercel-ready 
