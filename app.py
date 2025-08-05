import os
import json
import requests
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
from bs4 import BeautifulSoup
import time
import concurrent.futures
from urllib.parse import urljoin, urlparse
import logging

# Load environment variables from .env file
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_resume(file_stream) -> str:
    """Reads a PDF file stream and returns its text content."""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
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
        logger.error(f"Error calling Gemini API: {e}")
        return []

def scrape_linkedin_jobs(job_title: str, location: str = "India") -> list:
    """Scrape jobs from LinkedIn using SerpApi."""
    jobs = []
    try:
        params = {
            "engine": "linkedin_jobs",
            "keywords": job_title,
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "LinkedIn")
                if cleaned_job:
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping LinkedIn jobs for '{job_title}': {e}")
    
    return jobs

def scrape_indeed_jobs(job_title: str, location: str = "India") -> list:
    """Scrape jobs from Indeed using SerpApi."""
    jobs = []
    try:
        params = {
            "engine": "indeed",
            "q": job_title,
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "Indeed")
                if cleaned_job:
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping Indeed jobs for '{job_title}': {e}")
    
    return jobs

def scrape_naukri_jobs(job_title: str, location: str = "India") -> list:
    """Scrape jobs from Naukri.com using SerpApi."""
    jobs = []
    try:
        params = {
            "engine": "google_jobs",
            "q": f"{job_title} site:naukri.com",
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 15
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "Naukri")
                if cleaned_job:
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping Naukri jobs for '{job_title}': {e}")
    
    return jobs

def find_career_page(company_name: str, company_url: str = None) -> str:
    """Find the career page URL for a company."""
    try:
        # Common career page patterns
        career_patterns = [
            "/careers",
            "/jobs",
            "/career",
            "/job",
            "/work-with-us",
            "/join-us",
            "/opportunities"
        ]
        
        if company_url:
            base_url = company_url
        else:
            # Try to find company website using search
            search_params = {
                "engine": "google",
                "q": f"{company_name} official website",
                "api_key": SERPAPI_KEY,
                "num": 1
            }
            
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            if "organic_results" in results and results["organic_results"]:
                base_url = results["organic_results"][0].get("link", "")
            else:
                return None
        
        if not base_url:
            return None
            
        # Try different career page URLs
        for pattern in career_patterns:
            career_url = urljoin(base_url, pattern)
            try:
                response = requests.get(career_url, timeout=10)
                if response.status_code == 200:
                    return career_url
            except:
                continue
                
        return None
        
    except Exception as e:
        logger.error(f"Error finding career page for {company_name}: {e}")
        return None

def extract_apply_links_from_career_page(career_url: str) -> list:
    """Extract apply links from a company's career page."""
    apply_links = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(career_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return apply_links
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Common apply link patterns
        apply_patterns = [
            'apply',
            'apply now',
            'apply for this position',
            'submit application',
            'apply online',
            'apply here',
            'apply today'
        ]
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            link_text = link.get_text().lower().strip()
            href = link.get('href', '')
            
            # Check if link text matches apply patterns
            if any(pattern in link_text for pattern in apply_patterns):
                full_url = urljoin(career_url, href)
                apply_links.append({
                    'text': link.get_text().strip(),
                    'url': full_url
                })
            
            # Also check href for apply patterns
            elif any(pattern in href.lower() for pattern in apply_patterns):
                full_url = urljoin(career_url, href)
                apply_links.append({
                    'text': link.get_text().strip() or 'Apply',
                    'url': full_url
                })
        
        return apply_links
        
    except Exception as e:
        logger.error(f"Error extracting apply links from {career_url}: {e}")
        return apply_links

def enhance_job_with_apply_links(job: dict) -> dict:
    """Enhance job with direct apply links from career page."""
    try:
        company_name = job.get('company_name', '')
        if not company_name:
            return job
            
        # Find career page
        career_url = find_career_page(company_name)
        if not career_url:
            return job
            
        # Extract apply links
        apply_links = extract_apply_links_from_career_page(career_url)
        
        if apply_links:
            # Add career page and apply links to job
            job['career_page'] = career_url
            job['apply_links'] = apply_links
            job['has_direct_apply'] = True
        else:
            job['has_direct_apply'] = False
            
        return job
        
    except Exception as e:
        logger.error(f"Error enhancing job with apply links: {e}")
        return job

def discover_jobs_enhanced(job_titles: list, date_filter: str = "all") -> list:
    """Enhanced job discovery using multiple job boards and career page analysis."""
    all_jobs = []
    
    # Define search configurations for different job boards
    search_configs = [
        {
            "name": "Google Jobs",
            "engine": "google_jobs",
            "locations": ["Faridabad, Haryana, India", "Delhi NCR, India", "Gurgaon, Haryana, India"],
            "num": 15
        },
        {
            "name": "LinkedIn",
            "scraper": scrape_linkedin_jobs,
            "locations": ["India"]
        },
        {
            "name": "Indeed",
            "scraper": scrape_indeed_jobs,
            "locations": ["India"]
        },
        {
            "name": "Naukri",
            "scraper": scrape_naukri_jobs,
            "locations": ["India"]
        }
    ]
    
    for title in job_titles:
        # Generate title variations
        title_variations = generate_title_variations(title)
        
        for variation in title_variations:
            for config in search_configs:
                try:
                    if "scraper" in config:
                        # Use custom scraper
                        for location in config["locations"]:
                            jobs = config["scraper"](variation, location)
                            for job in jobs:
                                if is_recent_job(job, date_filter) and not is_duplicate_job(job, all_jobs):
                                    all_jobs.append(job)
                    else:
                        # Use SerpApi
                        for location in config["locations"]:
                            params = {
                                "engine": config["engine"],
                                "q": variation,
                                "location": location,
                                "api_key": SERPAPI_KEY,
                                "num": config["num"],
                                "date_posted": get_date_filter_param(date_filter)
                            }
                            
                            search = GoogleSearch(params)
                            results = search.get_dict()
                            
                            if "jobs_results" in results:
                                for job in results["jobs_results"]:
                                    cleaned_job = clean_job_data(job, config["name"])
                                    if cleaned_job and is_recent_job(cleaned_job, date_filter):
                                        if not is_duplicate_job(cleaned_job, all_jobs):
                                            all_jobs.append(cleaned_job)
                                            
                except Exception as e:
                    logger.error(f"Error searching {config['name']} for '{variation}': {e}")
    
    # Enhance jobs with apply links (limit to avoid rate limiting)
    enhanced_jobs = []
    for job in all_jobs[:50]:  # Limit to first 50 jobs for apply link enhancement
        enhanced_job = enhance_job_with_apply_links(job)
        enhanced_jobs.append(enhanced_job)
        time.sleep(1)  # Rate limiting
    
    # Add remaining jobs without enhancement
    enhanced_jobs.extend(all_jobs[50:])
    
    return enhanced_jobs

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

def clean_job_data(job: dict, source: str = "Unknown") -> dict:
    """Cleans and standardizes job data from various sources."""
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
            'related_links': job.get('related_links', []),
            'source': source,
            'career_page': None,
            'apply_links': [],
            'has_direct_apply': False
        }
        
        # Ensure we have at least a title and company
        if not cleaned['title'] or not cleaned['company_name']:
            return None
            
        return cleaned
    except Exception as e:
        logger.error(f"Error cleaning job data: {e}")
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
            
        # Discover Jobs with enhanced search across multiple job boards
        discovered_jobs = discover_jobs_enhanced(job_titles, date_filter)
        if not discovered_jobs:
            return jsonify({"error": f"No jobs found for roles like {', '.join(job_titles)} in your area. Try updating your resume or checking back later."}), 404
            
        # Rank Jobs by Similarity
        ranked_jobs = rank_jobs_by_similarity(resume_text, discovered_jobs)

        # Return the final sorted list to the frontend
        return jsonify(ranked_jobs)

    except Exception as e:
        logger.error(f"Unexpected error in find_jobs: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
