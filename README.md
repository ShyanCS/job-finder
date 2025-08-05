# AI Job Finder

An intelligent job search application that analyzes your resume and finds the best matching job opportunities using AI.

## Features

- **AI-Powered Resume Analysis**: Uses Google's Gemini AI to extract relevant job titles from your resume
- **Multi-Platform Job Search**: Searches across LinkedIn, Indeed, Naukri, and Google Jobs
- **Smart Job Matching**: Uses TF-IDF and cosine similarity to rank jobs by relevance
- **Direct Apply Links**: Automatically finds and provides direct application links from company career pages
- **Date Filtering**: Filter jobs by posting date (24h, week, month, 3 months, all time)
- **Beautiful UI**: Modern, responsive interface with drag-and-drop file upload

## Tech Stack

- **Backend**: Flask (Python)
- **AI**: Google Gemini API
- **Job Search**: SerpAPI
- **ML**: scikit-learn for job matching
- **Frontend**: HTML, CSS, JavaScript
- **PDF Processing**: PyPDF2

## Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd job-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GOOGLE_API_KEY=your_google_gemini_api_key
   SERPAPI_KEY=your_serpapi_key
   FLASK_ENV=development
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Deployment on Render (Free)

### Step 1: Prepare Your Repository

1. Make sure your code is in a Git repository (GitHub, GitLab, etc.)
2. Ensure all files are committed and pushed

### Step 2: Deploy on Render

1. **Sign up for Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub/GitLab account

2. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select the repository containing your job-finder project

3. **Configure the service**
   - **Name**: `job-finder` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

4. **Add Environment Variables**
   Click on "Environment" tab and add:
   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `SERPAPI_KEY`: Your SerpAPI key
   - `FLASK_ENV`: `production`

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - Your app will be available at `https://your-app-name.onrender.com`

### Step 3: Get API Keys

**Google Gemini API:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your Render environment variables

**SerpAPI:**
1. Go to [SerpAPI](https://serpapi.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your Render environment variables

## API Usage Limits

- **Render Free Tier**: 750 hours/month
- **Google Gemini**: 15 requests/minute (free tier)
- **SerpAPI**: 100 searches/month (free tier)

## Project Structure

```
job-finder/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
├── runtime.txt           # Python version specification
├── README.md             # This file
├── static/
│   └── script.js         # Frontend JavaScript
└── templates/
    └── index.html        # Main HTML template
```

## How It Works

1. **Resume Upload**: User uploads a PDF resume
2. **AI Analysis**: Gemini AI analyzes the resume and generates relevant job titles
3. **Job Search**: The app searches multiple job boards using the generated titles
4. **Job Matching**: TF-IDF and cosine similarity rank jobs by relevance to the resume
5. **Direct Apply**: The app finds direct application links from company career pages
6. **Results Display**: Jobs are displayed with match scores and apply options

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues:
1. Check the Render logs in your dashboard
2. Verify your API keys are correctly set
3. Ensure all dependencies are properly installed

## Free Hosting Alternatives

If Render doesn't meet your needs, here are other free hosting options:

- **Railway**: 500 hours/month free
- **Heroku**: Free tier discontinued, but still popular
- **PythonAnywhere**: Free tier for Python apps
- **Vercel**: Great for static sites (limited for Flask)
- **Netlify**: Static sites only

Render is recommended for this Flask application as it provides the best free tier for Python web applications. 