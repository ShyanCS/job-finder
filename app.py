import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
from serpapi import GoogleSearch
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS
from datetime import datetime, timedelta
import re

# Load environment variables from .env file
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

def parse_resume(file_stream) -> str:
    """Reads a PDF file stream and returns its text content."""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def get_job_titles(resume_text: str) -> list:
    """Uses Gemini API to generate job titles from resume text."""
    if not resume_text:
        return []
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Analyze the following resume text. Based on the skills and experience, generate a comprehensive list of 8-10 relevant job titles for a job search in India.
    Include both specific roles and broader categories. Return a JSON object with a single key "job_titles" containing this list.

    Resume Text:
    ---
    {resume_text}
    ---
    """
    try:
        response = model.generate_content(prompt)
        # Clean up potential markdown formatting from the response
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_response_text)
        return data.get("job_titles", [])
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return []

def discover_jobs_enhanced(job_titles: list, date_filter: str = "all") -> list:
    """Enhanced job discovery using multiple search strategies."""
    all_jobs = []
    location = "Faridabad, Haryana, India"
    
    # Define search engines and their configurations
    search_configs = [
        {
            "engine": "google_jobs",
            "params": {
                "location": location,
                "num": 15,
                "date_posted": get_date_filter_param(date_filter)
            }
        },
        {
            "engine": "google_jobs",
            "params": {
                "location": "Delhi NCR, India",
                "num": 10,
                "date_posted": get_date_filter_param(date_filter)
            }
        },
        {
            "engine": "google_jobs", 
            "params": {
                "location": "Gurgaon, Haryana, India",
                "num": 10,
                "date_posted": get_date_filter_param(date_filter)
            }
        }
    ]
    
    for title in job_titles:
        # Add variations of the job title for better coverage
        title_variations = generate_title_variations(title)
        
        for variation in title_variations:
            for config in search_configs:
                params = {
                    "engine": config["engine"],
                    "q": variation,
                    "api_key": SERPAPI_KEY,
                    **config["params"]
                }
                
                try:
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    if "jobs_results" in results:
                        for job in results["jobs_results"]:
                            cleaned_job = clean_job_data(job)
                            if cleaned_job and is_recent_job(cleaned_job, date_filter):
                                # Check for duplicates
                                if not is_duplicate_job(cleaned_job, all_jobs):
                                    all_jobs.append(cleaned_job)
                except Exception as e:
                    print(f"Error calling SerpApi for '{variation}' in {config['engine']}: {e}")
    
    return all_jobs

def generate_title_variations(title: str) -> list:
    """Generate variations of job titles for better search coverage."""
    variations = [title]
    
    # Common variations
    if "developer" in title.lower():
        variations.extend([title.replace("Developer", "Engineer"), title.replace("Developer", "Programmer")])
    elif "engineer" in title.lower():
        variations.extend([title.replace("Engineer", "Developer"), title.replace("Engineer", "Specialist")])
    elif "manager" in title.lower():
        variations.extend([title.replace("Manager", "Lead"), title.replace("Manager", "Supervisor")])
    
    # Add experience level variations
    base_title = re.sub(r'\b(senior|junior|lead|principal)\b', '', title, flags=re.IGNORECASE).strip()
    if base_title != title:
        variations.extend([
            f"Senior {base_title}",
            f"Junior {base_title}",
            f"Lead {base_title}",
            base_title
        ])
    
    return list(set(variations))  # Remove duplicates

def get_date_filter_param(date_filter: str) -> str:
    """Convert frontend date filter to SerpApi parameter."""
    date_mapping = {
        "24h": "past_24_hours",
        "week": "past_week", 
        "month": "past_month",
        "3months": "past_3_months",
        "all": None
    }
    return date_mapping.get(date_filter)

def is_recent_job(job: dict, date_filter: str) -> bool:
    """Check if job is within the specified date range."""
    if date_filter == "all":
        return True
    
    posted_at = job.get('posted_at', '')
    if not posted_at:
        return True  # If no date info, include it
    
    try:
        # Parse the posted date
        posted_date = parse_posted_date(posted_at)
        if not posted_date:
            return True
        
        # Calculate the cutoff date based on filter
        cutoff_date = get_cutoff_date(date_filter)
        return posted_date >= cutoff_date
    except:
        return True  # If parsing fails, include the job

def parse_posted_date(date_str: str) -> datetime:
    """Parse various date formats from job postings."""
    if not date_str:
        return None
    
    # Common date patterns
    patterns = [
        "%Y-%m-%d",
        "%d/%m/%Y", 
        "%m/%d/%Y",
        "%B %d, %Y",
        "%d %B %Y"
    ]
    
    for pattern in patterns:
        try:
            return datetime.strptime(date_str, pattern)
        except:
            continue
    
    return None

def get_cutoff_date(date_filter: str) -> datetime:
    """Get the cutoff date based on filter."""
    now = datetime.now()
    
    if date_filter == "24h":
        return now - timedelta(days=1)
    elif date_filter == "week":
        return now - timedelta(weeks=1)
    elif date_filter == "month":
        return now - timedelta(days=30)
    elif date_filter == "3months":
        return now - timedelta(days=90)
    else:
        return datetime.min  # Include all jobs

def is_duplicate_job(new_job: dict, existing_jobs: list) -> bool:
    """Check if a job is a duplicate based on title and company."""
    for existing_job in existing_jobs:
        if (new_job.get('title', '').lower() == existing_job.get('title', '').lower() and
            new_job.get('company_name', '').lower() == existing_job.get('company_name', '').lower()):
            return True
    return False

def clean_job_data(job: dict) -> dict:
    """Cleans and standardizes job data from SerpApi."""
    try:
        cleaned = {
            'title': job.get('title', ''),
            'company_name': job.get('company_name', ''),
            'location': job.get('location', ''),
            'description': job.get('description', ''),
            'job_id': job.get('job_id', ''),
            'posted_at': job.get('posted_at', ''),
            'salary': job.get('salary', ''),
            'job_type': job.get('job_type', ''),
            'apply_options': job.get('apply_options', []),
            'related_links': job.get('related_links', [])
        }
        
        # Ensure we have at least a title and company
        if not cleaned['title'] or not cleaned['company_name']:
            return None
            
        return cleaned
    except Exception as e:
        print(f"Error cleaning job data: {e}")
        return None

def rank_jobs_by_similarity(resume_text: str, jobs: list) -> list:
    """Ranks jobs based on cosine similarity between resume and job description."""
    if not jobs:
        return []
    
    # Create a list of all text content: resume first, then all job descriptions
    job_descriptions = [job.get('description', '') for job in jobs]
    corpus = [resume_text] + job_descriptions
    
    # Vectorize the text using TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Calculate cosine similarity between the resume (index 0) and all jobs
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    # Add the score to each job dictionary
    for i, job in enumerate(jobs):
        job['match_score'] = round(cosine_sim[0][i] * 100, 2) # as a percentage
        
    # Sort jobs by score in descending order
    sorted_jobs = sorted(jobs, key=lambda x: x['match_score'], reverse=True)
    return sorted_jobs

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/find-jobs', methods=['POST'])
def find_jobs():
    """The main endpoint to process the resume and find matching jobs."""
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Please upload a PDF file"}), 400

        # Get date filter from request
        date_filter = request.form.get('date_filter', 'all')

        # Parse Resume
        resume_text = parse_resume(file.stream)
        if not resume_text:
            return jsonify({"error": "Could not read text from resume PDF. Please ensure the file is not corrupted."}), 400
        
        # Generate Job Titles
        job_titles = get_job_titles(resume_text)
        if not job_titles:
            return jsonify({"error": "Could not generate job titles from resume. Please try again."}), 500
            
        # Discover Jobs with enhanced search
        discovered_jobs = discover_jobs_enhanced(job_titles, date_filter)
        if not discovered_jobs:
            return jsonify({"error": f"No jobs found for roles like {', '.join(job_titles)} in your area. Try updating your resume or checking back later."}), 404
            
        # Rank Jobs by Similarity
        ranked_jobs = rank_jobs_by_similarity(resume_text, discovered_jobs)

        # Return the final sorted list to the frontend
        return jsonify(ranked_jobs)

    except Exception as e:
        print(f"Unexpected error in find_jobs: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == '__main__':
    app.run(debug=True)
