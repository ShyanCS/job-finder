# 🤖 AI Job Finder

An intelligent job search application that uses AI to analyze your resume and find the perfect job opportunities. Built with Flask, Google Gemini AI, and SerpApi for comprehensive job discovery.

## ✨ Features

### 🎯 **AI-Powered Resume Analysis**
- **Smart Resume Parsing**: Extracts skills and experience from PDF resumes
- **AI Job Title Generation**: Uses Google Gemini to generate relevant job titles
- **Intelligent Matching**: TF-IDF and cosine similarity for optimal job-resume matching

### 🔍 **Enhanced Job Search**
- **Multiple Search Engines**: Comprehensive job discovery across multiple sources
- **Location Expansion**: Searches across Faridabad, Delhi NCR, and Gurgaon
- **Title Variations**: Automatically generates job title variations for better coverage
- **Duplicate Prevention**: Smart filtering to avoid duplicate job listings

### 📅 **Smart Date Filtering**
- **Last 24 Hours**: For urgent job seekers
- **Last Week**: Recent opportunities
- **Last Month**: Balanced recency and quantity
- **Last 3 Months**: Broader search with recent focus
- **All Time**: Complete search coverage

### 🎨 **Modern User Interface**
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Drag & Drop Upload**: Easy resume file upload with visual feedback
- **Real-time Loading**: Beautiful loading animations and progress indicators
- **Professional Cards**: Clean, modern job cards with hover effects
- **Smart Apply Buttons**: Direct application links with fallback handling

### 📊 **Advanced Features**
- **Match Scoring**: AI-calculated relevance percentage for each job
- **Job Details**: Comprehensive job information including salary, type, and links
- **Error Handling**: Graceful error handling with helpful user messages
- **Mobile Optimized**: Touch-friendly interface for mobile users

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Google Gemini API key
- SerpApi key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-finder
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-cors google-generativeai serpapi PyPDF2 scikit-learn python-dotenv
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key
   SERPAPI_KEY=your_serpapi_key
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   
   Navigate to `http://localhost:5000`

## 📁 Project Structure

```
job-finder/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   └── script.js         # Frontend JavaScript
├── venv/                 # Virtual environment
├── .env                  # Environment variables
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key for AI analysis | Yes |
| `SERPAPI_KEY` | SerpApi key for job search | Yes |

### API Setup

#### Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

#### SerpApi
1. Sign up at [SerpApi](https://serpapi.com/)
2. Get your API key from the dashboard
3. Add it to your `.env` file

## 🎯 How It Works

### 1. **Resume Upload & Analysis**
- User uploads a PDF resume
- System extracts text content using PyPDF2
- AI analyzes skills and experience using Google Gemini

### 2. **Job Title Generation**
- AI generates 8-10 relevant job titles based on resume content
- Includes variations and experience levels for comprehensive coverage

### 3. **Enhanced Job Discovery**
- Searches multiple locations (Faridabad, Delhi NCR, Gurgaon)
- Uses title variations for better job coverage
- Applies date filtering based on user preferences
- Removes duplicates and incomplete listings

### 4. **Smart Ranking**
- Uses TF-IDF vectorization for text analysis
- Calculates cosine similarity between resume and job descriptions
- Ranks jobs by relevance percentage

### 5. **Results Display**
- Shows jobs in modern, responsive cards
- Displays match scores, company info, and posting dates
- Provides direct apply links when available

## 🎨 UI Features

### **Upload Section**
- Drag & drop file upload
- File type validation (PDF only)
- Visual feedback and progress indicators

### **Search Options**
- Date filtering with intuitive buttons
- Active state indicators
- Responsive design for all screen sizes

### **Job Cards**
- Clean, modern design with hover effects
- Match score badges
- Company and location information
- Posted date with smart formatting
- Apply and Details buttons

### **Results Display**
- Grid layout that adapts to screen size
- Filter badges showing active options
- Loading animations and error handling

## 🔍 Search Capabilities

### **Multiple Search Strategies**
- **Location Coverage**: Faridabad, Delhi NCR, Gurgaon
- **Title Variations**: Developer → Engineer, Programmer
- **Experience Levels**: Senior, Junior, Lead variations
- **Date Filtering**: 24h, week, month, 3 months, all time

### **AI-Powered Features**
- **Smart Resume Analysis**: Extracts relevant skills and experience
- **Job Title Generation**: Creates comprehensive job title lists
- **Intelligent Matching**: Uses machine learning for optimal job-resume matching

## 🛠️ Technical Stack

### **Backend**
- **Flask**: Web framework
- **Google Gemini AI**: Resume analysis and job title generation
- **SerpApi**: Job search and discovery
- **PyPDF2**: PDF text extraction
- **scikit-learn**: TF-IDF and cosine similarity for job matching

### **Frontend**
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with gradients and animations
- **JavaScript**: Interactive functionality
- **Font Awesome**: Icons and visual elements

### **APIs**
- **Google Gemini**: AI-powered resume analysis
- **SerpApi**: Comprehensive job search across multiple sources

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set up a production server (e.g., Ubuntu with Nginx)
2. Install Python and dependencies
3. Configure environment variables
4. Use a WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## 🔧 Customization

### Adding New Locations
Edit the `search_configs` in `app.py`:
```python
{
    "engine": "google_jobs",
    "params": {
        "location": "Your City, State, Country",
        "num": 10,
        "date_posted": get_date_filter_param(date_filter)
    }
}
```

### Modifying Date Filters
Update the `date_mapping` in `get_date_filter_param()`:
```python
date_mapping = {
    "24h": "past_24_hours",
    "week": "past_week", 
    "month": "past_month",
    "3months": "past_3_months",
    "all": None
}
```

### Styling Customization
Modify the CSS in `templates/index.html` to match your brand colors and design preferences.

## 🐛 Troubleshooting

### Common Issues

**"No jobs found" error**
- Check your SerpApi key is valid
- Verify the location settings
- Try different date filters

**"Could not read PDF" error**
- Ensure the PDF is not password protected
- Check the PDF is not corrupted
- Verify the PDF contains extractable text

**"AI analysis failed" error**
- Verify your Google Gemini API key
- Check your internet connection
- Ensure the resume contains sufficient text

### Debug Mode
Run with debug enabled for detailed error messages:
```bash
python app.py
```

## 📈 Performance Tips

1. **API Rate Limits**: Be mindful of SerpApi and Google Gemini rate limits
2. **Caching**: Consider implementing Redis for caching job results
3. **Async Processing**: For production, consider async job processing
4. **CDN**: Use a CDN for static assets in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for intelligent resume analysis
- **SerpApi** for comprehensive job search capabilities
- **Flask** for the web framework
- **Font Awesome** for beautiful icons

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the error logs in your console
3. Verify your API keys are correct
4. Ensure all dependencies are installed

---

**Made with ❤️ for job seekers everywhere** 