# NutriAI

**AI-powered nutrition analysis with Google OAuth authentication and personalized insights**

Transform your meals into actionable nutrition data with cutting-edge AI technology. NutriAI provides instant, detailed nutritional analysis of your food photos with support for multiple dietary goals and secure user profiles.

![NutriAI Interface](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3+-green) ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)

## Key Features

- **AI-Powered Analysis**: Instant nutrition breakdown (Calories, Macros, Micros) using Gemini 2.5 Pro.
- **Global Dashboard**: Timezone-aware tracking for meals & hydration that works anywhere.
- **Personalized Goals**: Smart scoring & insights for Keto, Vegan, Paleo, and more.
- **Secure & Private**: Google OAuth, private history, and dedicated guest sessions.
- **Modern UX**: Responsive Glassmorphism design with Dark Mode support.

## Quick Setup

### Prerequisites
- **Python 3.9+**
- **Google AI API key** (Gemini)
- **MongoDB Atlas** account
- **Google Cloud Console** project (for OAuth)

### Installation

1. **Clone & Environment Setup**
   ```bash
   git clone <repository-url>
   cd nutriai
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create `.env` file:
   ```env
   # AI Configuration
   GEMINI_API_KEY=your_google_ai_api_key
   
   # Database
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/nutriai
   
   # Authentication
   GOOGLE_CLIENT_ID=your_google_oauth_client_id
   GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
   OAUTH_REDIRECT_URI=http://localhost:5001/auth/callback
   FLASK_SECRET_KEY=your_secure_secret_key
   
   # Optional
   ADMIN_EMAILS=admin@example.com,admin2@example.com
   ```

3. **Google Cloud Console Setup**
   - Create a new project or use existing
   - Enable **Google+ API** and **OAuth 2.0**
   - Configure OAuth consent screen
   - Add authorized origins: `http://localhost:5001`
   - Add authorized redirect URIs: `http://localhost:5001/auth/callback`

4. **Database Setup**
   - Create MongoDB Atlas cluster
   - Whitelist your IP address
   - Get connection string and add to `.env`

5. **Run Application**
   ```bash
   python app.py
   ```

6. **Access Application**
   ```
   http://localhost:5001
   ```

## Tech Stack

### Backend
- **Flask 2.3+** - Web framework
- **Google Gemini 2.5 Pro** - AI image analysis
- **MongoDB Atlas** - Cloud database
- **Flask-Login** - Session management
- **Authlib** - OAuth 2.0 implementation

### Frontend
- **Tailwind CSS** - Utility-first styling
- **Phosphor Icons** - Modern icon set
- **Vanilla JavaScript** - Interactive functionality
- **Responsive Design** - Mobile-first approach

### Security & Auth
- **Google OAuth 2.0** - Secure authentication
- **Session cookies** - Secure user sessions
- **CSRF protection** - Form security
- **Usage rate limiting** - Prevent abuse

### Deployment
- **Vercel-ready** configuration
- **Environment variable** support
- **Static file** optimization
- **Production** security settings



## Security Features

### Authentication
- **Google OAuth 2.0** - Industry standard security
- **Secure session** management
- **HTTPS-ready** for production
- **CSRF protection** on forms

### Privacy
- **User data isolation** - strict ownership rules
- **Guest session** isolation with signed cookies
- **IP and browser** tracking for security
- **No cross-user** data leakage

### Rate Limiting
- **Daily usage limits** to prevent abuse
- **Per-user tracking** with MongoDB
- **Graceful limit** notifications

## Deployment

### Vercel (Recommended)
1. **Connect repository** to Vercel
2. **Add environment variables** in dashboard
3. **Deploy automatically** on push

### Manual Deployment
1. **Set PRODUCTION=true** in environment
2. **Configure HTTPS** and secure cookies
3. **Update OAuth redirects** for production domain
4. **Monitor usage** and performance

## Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Author

**Mayur Bijarniya**
- Email: bijarniya.m@northeastern.edu
- LinkedIn: [linkedin.com/in/mayurbijarniya](https://linkedin.com/in/mayurbijarniya)
- GitHub: [github.com/mayurbijarniya](https://github.com/mayurbijarniya)

---

<div align="center">

**Made with love for healthier eating choices**

⭐ Star this repo if you found it helpful!

</div> 
