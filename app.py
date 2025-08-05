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

# Job storage file
JOBS_FILE = 'saved_jobs.json'

def load_saved_jobs():
    """Load saved jobs from file."""
    try:
        if os.path.exists(JOBS_FILE):
            with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"jobs": [], "last_updated": None, "resume_info": None}
    except Exception as e:
        logger.error(f"Error loading saved jobs: {e}")
        return {"jobs": [], "last_updated": None, "resume_info": None}

def save_jobs_to_file(jobs_data):
    """Save jobs to file."""
    try:
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(jobs_data.get('jobs', []))} jobs to file")
    except Exception as e:
        logger.error(f"Error saving jobs: {e}")

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

def extract_experience_and_skills(resume_text: str) -> dict:
    """Uses Gemini API to extract experience level and skills from resume."""
    if not resume_text:
        return {"experience_level": "entry", "years_experience": 0, "skills": [], "job_titles": []}
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Analyze the following resume text and extract:
    1. Total years of experience (sum of all work experience), If the resume dont have end date for experience instead it says Present, then it will be Current month and year as end date.
    2. Experience level (entry, junior, mid, senior, lead)
    3. Key technical skills
    4. Relevant job titles based on experience level, Job titles should be based on the skills provided in the resume not on the current role. There can be multiple variations off the job titles.

    Experience Level Guidelines:
    - Entry: 0-1 years (Associate, Entry Level, Junior)
    - Junior: 1-3 years (SDE I, Full Stack Engineer I, Junior)
    - Mid: 3-5 years (SDE II, Full Stack Engineer II, Mid-level)
    - Senior: 5-8 years (Senior SDE, Senior Engineer, Senior)
    - Lead: 8+ years (Lead Engineer, Principal Engineer, Lead)

    Return a JSON object with:
    {{
        "experience_level": "entry|junior|mid|senior|lead",
        "years_experience": number,
        "skills": ["skill1", "skill2", ...],
        "job_titles": ["title1", "title2", ...]
    }}

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
        return data
    except Exception as e:
        logger.error(f"Error calling Gemini API for experience extraction: {e}")
        return {"experience_level": "entry", "years_experience": 0, "skills": [], "job_titles": []}

def generate_experience_based_job_titles(experience_data: dict) -> list:
    """Generate job titles based on experience level."""
    experience_level = experience_data.get('experience_level', 'entry')
    years_experience = experience_data.get('years_experience', 0)
    
    # Base job titles by experience level
    experience_titles = {
        'entry': [
            'Associate Software Engineer',
            'Entry Level Developer',
            'Junior Software Engineer',
            'Software Engineer I',
            'Full Stack Developer I',
            'Frontend Developer I',
            'Backend Developer I',
            'Associate Developer',
            'Graduate Software Engineer',
            'Junior Full Stack Engineer'
        ],
        'junior': [
            'Software Engineer I',
            'Full Stack Engineer I',
            'Frontend Engineer I',
            'Backend Engineer I',
            'Junior Software Engineer',
            'Software Developer I',
            'Web Developer I',
            'Application Developer I',
            'Systems Engineer I',
            'Junior Full Stack Developer'
        ],
        'mid': [
            'Software Engineer II',
            'Full Stack Engineer II',
            'Frontend Engineer II',
            'Backend Engineer II',
            'Mid-level Software Engineer',
            'Software Developer II',
            'Web Developer II',
            'Application Developer II',
            'Systems Engineer II',
            'Full Stack Developer II'
        ],
        'senior': [
            'Senior Software Engineer',
            'Senior Full Stack Engineer',
            'Senior Frontend Engineer',
            'Senior Backend Engineer',
            'Senior Software Developer',
            'Senior Web Developer',
            'Senior Application Developer',
            'Senior Systems Engineer',
            'Lead Software Engineer',
            'Principal Software Engineer'
        ],
        'lead': [
            'Lead Software Engineer',
            'Lead Full Stack Engineer',
            'Lead Frontend Engineer',
            'Lead Backend Engineer',
            'Principal Software Engineer',
            'Senior Lead Developer',
            'Technical Lead',
            'Engineering Lead',
            'Team Lead',
            'Senior Principal Engineer'
        ]
    }
    
    # Get titles for the experience level
    titles = experience_titles.get(experience_level, experience_titles['entry'])
    
    # Add experience-specific keywords
    if experience_level == 'entry':
        titles.extend(['Associate', 'Entry Level', 'Graduate', 'Fresher'])
    elif experience_level == 'junior':
        titles.extend(['Junior', 'I', 'Early Career'])
    elif experience_level == 'mid':
        titles.extend(['II', 'Mid-level', 'Intermediate'])
    elif experience_level == 'senior':
        titles.extend(['Senior', 'III', 'Advanced'])
    elif experience_level == 'lead':
        titles.extend(['Lead', 'Principal', 'Senior Lead', 'IV'])
    
    return titles

def get_experience_based_search_filters(experience_data: dict) -> dict:
    """Get search filters based on experience level."""
    experience_level = experience_data.get('experience_level', 'entry')
    years_experience = experience_data.get('years_experience', 0)
    
    filters = {
        'entry': {
            'keywords': ['entry level', 'associate', 'junior', 'graduate', 'fresher', '0-1 years', '1 year'],
            'exclude': ['senior', 'lead', 'principal', 'manager', 'director', '5+ years', '10+ years']
        },
        'junior': {
            'keywords': ['junior', 'I', '1-3 years', '2 years', '3 years', 'early career'],
            'exclude': ['senior', 'lead', 'principal', 'manager', 'director', '5+ years', '10+ years']
        },
        'mid': {
            'keywords': ['II', 'mid-level', '3-5 years', '4 years', '5 years', 'intermediate'],
            'exclude': ['entry level', 'associate', 'fresher', 'graduate', '10+ years']
        },
        'senior': {
            'keywords': ['senior', 'III', '5+ years', '6 years', '7 years', '8 years', 'advanced'],
            'exclude': ['entry level', 'associate', 'fresher', 'graduate', 'junior']
        },
        'lead': {
            'keywords': ['lead', 'principal', 'senior lead', 'IV', '8+ years', '10+ years', 'team lead'],
            'exclude': ['entry level', 'associate', 'fresher', 'graduate', 'junior']
        }
    }
    
    return filters.get(experience_level, filters['entry'])

def scrape_linkedin_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Scrape jobs from LinkedIn using SerpApi with experience filters."""
    jobs = []
    try:
        # Add experience keywords to search
        search_query = job_title
        if experience_filters:
            keywords = experience_filters.get('keywords', [])
            if keywords:
                search_query += f" {' '.join(keywords[:3])}"  # Add top 3 keywords
        
        params = {
            "engine": "linkedin_jobs",
            "keywords": search_query,
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "LinkedIn")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping LinkedIn jobs for '{job_title}': {e}")
    
    return jobs

def scrape_indeed_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Scrape jobs from Indeed using SerpApi with experience filters."""
    jobs = []
    try:
        # Add experience keywords to search
        search_query = job_title
        if experience_filters:
            keywords = experience_filters.get('keywords', [])
            if keywords:
                search_query += f" {' '.join(keywords[:3])}"  # Add top 3 keywords
        
        params = {
            "engine": "indeed",
            "q": search_query,
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "Indeed")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping Indeed jobs for '{job_title}': {e}")
    
    return jobs

def scrape_naukri_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Scrape jobs from Naukri.com using SerpApi with experience filters."""
    jobs = []
    try:
        # Add experience keywords to search
        search_query = f"{job_title} site:naukri.com"
        if experience_filters:
            keywords = experience_filters.get('keywords', [])
            if keywords:
                search_query += f" {' '.join(keywords[:3])}"  # Add top 3 keywords
        
        params = {
            "engine": "google_jobs",
            "q": search_query,
            "location": location,
            "api_key": SERPAPI_KEY,
            "num": 15
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "jobs_results" in results:
            for job in results["jobs_results"]:
                cleaned_job = clean_job_data(job, "Naukri")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    jobs.append(cleaned_job)
                    
    except Exception as e:
        logger.error(f"Error scraping Naukri jobs for '{job_title}': {e}")
    
    return jobs

def matches_experience_level(job: dict, experience_filters: dict) -> bool:
    """Check if job matches the experience level filters."""
    if not experience_filters:
        return True
    
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    
    # Check for excluded keywords
    exclude_keywords = experience_filters.get('exclude', [])
    for keyword in exclude_keywords:
        if keyword.lower() in job_text:
            return False
    
    # Check for required keywords (at least one should match)
    include_keywords = experience_filters.get('keywords', [])
    if include_keywords:
        has_matching_keyword = any(keyword.lower() in job_text for keyword in include_keywords)
        if not has_matching_keyword:
            return False
    
    return True

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
            
            # Limit to maximum 3 apply links
            if len(apply_links) >= 3:
                break
        
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

def discover_jobs_enhanced(experience_data: dict, date_filter: str = "all") -> list:
    """Enhanced job discovery using experience-based filtering."""
    all_jobs = []
    
    # Get experience-based job titles
    job_titles = generate_experience_based_job_titles(experience_data)
    
    # Get experience filters
    experience_filters = get_experience_based_search_filters(experience_data)
    
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
                        # Use custom scraper with experience filters
                        for location in config["locations"]:
                            jobs = config["scraper"](variation, location, experience_filters)
                            for job in jobs:
                                if is_recent_job(job, date_filter) and not is_duplicate_job(job, all_jobs):
                                    all_jobs.append(job)
                    else:
                        # Use SerpApi with experience keywords
                        for location in config["locations"]:
                            # Add experience keywords to search query
                            search_query = variation
                            if experience_filters:
                                keywords = experience_filters.get('keywords', [])
                                if keywords:
                                    search_query += f" {' '.join(keywords[:3])}"
                            
                            params = {
                                "engine": config["engine"],
                                "q": search_query,
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
                                        if not is_duplicate_job(cleaned_job, all_jobs) and matches_experience_level(cleaned_job, experience_filters):
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

def rank_jobs_by_similarity(resume_text: str, jobs: list, experience_data: dict) -> list:
    """Ranks jobs based on cosine similarity between resume and job description, with experience bonus."""
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
    
    # Add the score to each job dictionary with experience bonus
    for i, job in enumerate(jobs):
        base_score = cosine_sim[0][i] * 100
        
        # Add experience level bonus
        experience_bonus = get_experience_bonus(job, experience_data)
        final_score = min(100, base_score + experience_bonus)
        
        job['match_score'] = round(final_score, 2)
        
    # Sort jobs by score in descending order
    sorted_jobs = sorted(jobs, key=lambda x: x['match_score'], reverse=True)
    return sorted_jobs

def get_experience_bonus(job: dict, experience_data: dict) -> float:
    """Calculate experience bonus for job matching."""
    experience_level = experience_data.get('experience_level', 'entry')
    years_experience = experience_data.get('years_experience', 0)
    
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    
    # Experience level bonuses
    level_bonuses = {
        'entry': {
            'keywords': ['entry', 'associate', 'junior', 'graduate', 'fresher', '0-1', '1 year'],
            'bonus': 15
        },
        'junior': {
            'keywords': ['junior', 'I', '1-3', '2 years', '3 years', 'early career'],
            'bonus': 10
        },
        'mid': {
            'keywords': ['II', 'mid-level', '3-5', '4 years', '5 years', 'intermediate'],
            'bonus': 5
        },
        'senior': {
            'keywords': ['senior', 'III', '5+', '6 years', '7 years', '8 years', 'advanced'],
            'bonus': 0
        },
        'lead': {
            'keywords': ['lead', 'principal', 'senior lead', 'IV', '8+', '10+', 'team lead'],
            'bonus': 0
        }
    }
    
    level_config = level_bonuses.get(experience_level, level_bonuses['entry'])
    
    # Check if job contains experience-appropriate keywords
    for keyword in level_config['keywords']:
        if keyword.lower() in job_text:
            return level_config['bonus']
    
    return 0

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
        
        # Extract experience and skills
        experience_data = extract_experience_and_skills(resume_text)
        logger.info(f"Extracted experience data: {experience_data}")
        # logger.info(f"Extracted resume text: {resume_text}")
        
        if not experience_data.get('job_titles'):
            return jsonify({"error": "Could not extract experience information from resume. Please try again."}), 500
            
        # Discover Jobs with experience-based filtering
        discovered_jobs = discover_jobs_enhanced(experience_data, date_filter)
        if not discovered_jobs:
            experience_level = experience_data.get('experience_level', 'entry')
            years = experience_data.get('years_experience', 0)
            return jsonify({"error": f"No jobs found for {experience_level} level roles ({years} years experience) in your area. Try updating your resume or checking back later."}), 404
            
        # Rank Jobs by Similarity with experience bonus
        ranked_jobs = rank_jobs_by_similarity(resume_text, discovered_jobs, experience_data)

        # Return the final sorted list to the frontend
        return jsonify(ranked_jobs)

    except Exception as e:
        logger.error(f"Unexpected error in find_jobs: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@app.route('/save-jobs', methods=['POST'])
def save_jobs():
    """Save jobs to local storage."""
    try:
        data = request.get_json()
        jobs = data.get('jobs', [])
        resume_info = data.get('resume_info', {})
        
        # Prepare data to save
        jobs_data = {
            "jobs": jobs,
            "last_updated": datetime.now().isoformat(),
            "resume_info": resume_info
        }
        
        # Save to file
        save_jobs_to_file(jobs_data)
        
        return jsonify({"success": True, "message": f"Saved {len(jobs)} jobs successfully"})
        
    except Exception as e:
        logger.error(f"Error saving jobs: {e}")
        return jsonify({"error": "Failed to save jobs"}), 500

@app.route('/get-saved-jobs', methods=['GET'])
def get_saved_jobs():
    """Retrieve saved jobs from local storage."""
    try:
        saved_data = load_saved_jobs()
        return jsonify(saved_data)
        
    except Exception as e:
        logger.error(f"Error loading saved jobs: {e}")
        return jsonify({"error": "Failed to load saved jobs"}), 500

@app.route('/clear-saved-jobs', methods=['POST'])
def clear_saved_jobs():
    """Clear saved jobs from local storage."""
    try:
        # Clear the file
        if os.path.exists(JOBS_FILE):
            os.remove(JOBS_FILE)
        
        return jsonify({"success": True, "message": "Saved jobs cleared successfully"})
        
    except Exception as e:
        logger.error(f"Error clearing saved jobs: {e}")
        return jsonify({"error": "Failed to clear saved jobs"}), 500

if __name__ == '__main__':
    app.run(debug=True)
