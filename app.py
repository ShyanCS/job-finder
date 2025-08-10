import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
# from serpapi import GoogleSearch  # Removed - using alternatives
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import math
from collections import Counter
from flask_cors import CORS
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import time
import concurrent.futures
from urllib.parse import urljoin, urlparse
import logging
from job_scraper_alternatives import JobScraperAlternatives, get_jobs_without_serpapi

# Load environment variables from .env file
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # Keep as backup
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Initialize the alternative scraper
alternative_scraper = JobScraperAlternatives()

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File-based job storage removed - now using localStorage
# JOBS_FILE = 'saved_jobs.json'

# def load_saved_jobs():
#     """Load saved jobs from file."""
#     # Deprecated - using localStorage instead
#     pass

# def save_jobs_to_file(jobs_data):
#     """Save jobs to file."""
#     # Deprecated - using localStorage instead
#     pass

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
    """Uses Gemini API to extract experience level and skills from resume in multiple requests."""
    if not resume_text:
        return {"experience_level": "entry", "years_experience": 0, "skills": [], "job_titles": []}
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Request 1: Extract basic experience and skills
    basic_info = extract_basic_resume_info(resume_text, model)
    
    # Request 2: Generate job titles based on skills
    job_titles = generate_job_titles_from_skills(basic_info.get('skills', []), model)
    
    # Request 3: Generate experience-level specific variants
    experience_variants = generate_experience_level_variants(
        job_titles, 
        basic_info.get('experience_level', 'entry'),
        basic_info.get('years_experience', 0),
        model
    )
    
    # Combine all results
    result = basic_info.copy()
    result['job_titles'] = experience_variants
    
    return result

def extract_basic_resume_info(resume_text: str, model) -> dict:
    """First Gemini request: Extract basic experience and skills."""
    prompt = f"""
    Analyze the following resume text and extract:
    1. Total years of experience (sum of all work experience). If the resume doesn't have end date for experience and says "Present", use current month and year as end date.
    2. Experience level based on years
    3. Key technical skills (programming languages, frameworks, tools, technologies)

    Experience Level Guidelines:
    - Entry: 0-1 years
    - Junior: 1-3 years  
    - Mid: 3-5 years
    - Senior: 5-8 years
    - Lead: 8+ years

    Return ONLY a JSON object with:
    {{
        "experience_level": "entry|junior|mid|senior|lead",
        "years_experience": number,
        "skills": ["skill1", "skill2", "skill3", ...]
    }}

    Resume Text:
    ---
    {resume_text}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        time.sleep(1)  # Rate limiting for Gemini API
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_response_text)
        return data
    except Exception as e:
        logger.error(f"Error extracting basic resume info: {e}")
        return {"experience_level": "entry", "years_experience": 0, "skills": []}

def generate_job_titles_from_skills(skills: list, model) -> list:
    """Second Gemini request: Generate popular job titles based on skills."""
    if not skills:
        return ["Software Engineer", "Developer"]
    
    skills_text = ", ".join(skills)
    prompt = f"""
    Based on the following technical skills, generate popular and in-demand job titles that would be suitable for someone with these skills.

    Skills: {skills_text}

    Requirements:
    1. Focus on popular, in-demand job titles in the current market
    2. Consider combinations of the provided skills
    3. Include both specific and general titles
    4. Prioritize titles that are commonly posted on job boards
    5. Include 8-12 different job titles

    Examples of good job titles:
    - Software Engineer
    - Full Stack Developer  
    - Python Developer
    - React Developer
    - DevOps Engineer
    - Backend Engineer
    - Frontend Engineer

    Return ONLY a JSON array of job titles:
    ["title1", "title2", "title3", ...]
    """
    
    try:
        response = model.generate_content(prompt)
        time.sleep(1)  # Rate limiting for Gemini API
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        job_titles = json.loads(json_response_text)
        return job_titles if isinstance(job_titles, list) else []
    except Exception as e:
        logger.error(f"Error generating job titles from skills: {e}")
        return ["Software Engineer", "Developer"]

def generate_experience_level_variants(job_titles: list, experience_level: str, years_experience: int, model) -> list:
    """Third Gemini request: Generate experience-level specific variants of job titles."""
    if not job_titles:
        return ["Software Engineer"]
    
    titles_text = ", ".join(job_titles)
    prompt = f"""
    Take the following job titles and create variants that are appropriate for someone with {experience_level} level experience ({years_experience} years).

    Original Job Titles: {titles_text}
    Experience Level: {experience_level}
    Years of Experience: {years_experience}

    Guidelines for experience levels:
    - Entry (0-1 years): Add prefixes like "Associate", "Entry Level", "Junior", "Graduate", or suffixes like "I", "Trainee"
    - Junior (1-3 years): Add prefixes like "Junior", or suffixes like "I", "1"
    - Mid (3-5 years): Add suffixes like "II", "2" or keep original titles
    - Senior (5-8 years): Add prefixes like "Senior" or suffixes like "III", "3"
    - Lead (8+ years): Add prefixes like "Senior", "Lead", "Principal" or suffixes like "IV", "Lead"

    Examples:
    - Entry: "Associate Software Engineer", "Junior Python Developer", "Graduate Full Stack Developer"
    - Junior: "Software Engineer I", "Junior Backend Developer", "Python Developer I"
    - Mid: "Software Engineer II", "Full Stack Developer", "Python Developer"
    - Senior: "Senior Software Engineer", "Senior Python Developer", "Senior Full Stack Developer"
    - Lead: "Lead Software Engineer", "Principal Python Developer", "Senior Lead Developer"

    Return ONLY a JSON array of 10-15 experience-appropriate job title variants:
    ["title1", "title2", "title3", ...]
    """
    
    try:
        response = model.generate_content(prompt)
        time.sleep(1)  # Rate limiting for Gemini API
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        variants = json.loads(json_response_text)
        return variants if isinstance(variants, list) else job_titles
    except Exception as e:
        logger.error(f"Error generating experience level variants: {e}")
        return job_titles

# Removed: generate_experience_based_job_titles - replaced with AI-generated titles

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
    """Updated LinkedIn scraping without SerpAPI"""
    try:
        jobs = alternative_scraper.scrape_linkedin_jobs_direct(job_title, location)
        
        # Apply experience filters
        if experience_filters:
            filtered_jobs = []
            for job in jobs:
                cleaned_job = clean_job_data_updated(job, "LinkedIn")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    filtered_jobs.append(cleaned_job)
            return filtered_jobs
        
        return [clean_job_data_updated(job, "LinkedIn") for job in jobs if clean_job_data_updated(job, "LinkedIn")]
    except Exception as e:
        logger.error(f"Error scraping LinkedIn jobs for '{job_title}': {e}")
        return []

def scrape_indeed_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Updated Indeed scraping without SerpAPI"""
    try:
        jobs = alternative_scraper.scrape_indeed_direct(job_title, location)
        
        # Apply experience filters
        if experience_filters:
            filtered_jobs = []
            for job in jobs:
                cleaned_job = clean_job_data_updated(job, "Indeed")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    filtered_jobs.append(cleaned_job)
            return filtered_jobs
        
        return [clean_job_data_updated(job, "Indeed") for job in jobs if clean_job_data_updated(job, "Indeed")]
    except Exception as e:
        logger.error(f"Error scraping Indeed jobs for '{job_title}': {e}")
        return []

def scrape_naukri_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Updated Naukri scraping without SerpAPI"""
    try:
        jobs = alternative_scraper.scrape_naukri_direct(job_title, location)
        
        # Apply experience filters
        if experience_filters:
            filtered_jobs = []
            for job in jobs:
                cleaned_job = clean_job_data_updated(job, "Naukri")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    filtered_jobs.append(cleaned_job)
            return filtered_jobs
        
        return [clean_job_data_updated(job, "Naukri") for job in jobs if clean_job_data_updated(job, "Naukri")]
    except Exception as e:
        logger.error(f"Error scraping Naukri jobs for '{job_title}': {e}")
        return []

def scrape_jsearch_jobs(job_title: str, location: str = "India", experience_filters: dict = None) -> list:
    """Scrape jobs using JSearch API (2500 free requests/month)"""
    try:
        if not RAPIDAPI_KEY:
            logger.warning("RapidAPI key not found, skipping JSearch API")
            return []
            
        jobs = alternative_scraper.use_jsearch_api(job_title, location, RAPIDAPI_KEY)
        
        # Apply experience filters
        if experience_filters:
            filtered_jobs = []
            for job in jobs:
                cleaned_job = clean_job_data_updated(job, "JSearch")
                if cleaned_job and matches_experience_level(cleaned_job, experience_filters):
                    filtered_jobs.append(cleaned_job)
            return filtered_jobs
        
        return [clean_job_data_updated(job, "JSearch") for job in jobs if clean_job_data_updated(job, "JSearch")]
    except Exception as e:
        logger.error(f"Error using JSearch API for '{job_title}': {e}")
        return []

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
            # Try to find company website using basic search (fallback to SerpAPI if available)
            if SERPAPI_KEY:
                try:
                    from serpapi import GoogleSearch
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
                except:
                    # If SerpAPI fails, try basic search approach
                    return None
            else:
                # Without SerpAPI, we can't easily find company websites
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

def discover_jobs_enhanced(experience_data: dict, date_filter: str = "all", location_filter: str = "India") -> list:
    """Enhanced job discovery using AI-generated job titles from resume analysis"""
    all_jobs = []
    
    # Use AI-generated job titles from resume analysis
    ai_generated_titles = experience_data.get('job_titles', [])
    
    # Fallback to common titles if AI generation failed
    if not ai_generated_titles:
        logger.warning("No AI-generated job titles found, using fallback titles")
        ai_generated_titles = [
            "Software Engineer",
            "Python Developer", 
            "Java Developer",
            "Full Stack Developer",
            "Frontend Developer",
            "Backend Developer",
            "Web Developer",
            "Software Developer"
        ]
    
    # Use the AI-generated titles for job search
    job_titles_to_search = ai_generated_titles[:8]  # Limit to top 8 titles for efficiency
    logger.info(f"Searching for jobs with AI-generated titles: {job_titles_to_search}")
    
    # Get experience filters for filtering results
    experience_filters = get_experience_based_search_filters(experience_data)
    
    # Define search configurations for different job boards (updated)
    search_configs = [
        {
            "name": "Naukri",
            "scraper": scrape_naukri_jobs,
            "locations": [location_filter]
        },
        {
            "name": "Indeed", 
            "scraper": scrape_indeed_jobs,
            "locations": [location_filter]
        },
        {
            "name": "LinkedIn",
            "scraper": scrape_linkedin_jobs,
            "locations": [location_filter]
        },
        {
            "name": "JSearch",
            "scraper": scrape_jsearch_jobs,
            "locations": [location_filter]
        }
    ]
    
    # Process each scraper sequentially for better reliability
    for title in job_titles_to_search[:4]:  # Limit to top 4 AI-generated job titles
        for config in search_configs:
            try:
                for location in config["locations"]:
                    logger.info(f"Scraping {config['name']} for '{title}' in {location}")
                    jobs = config["scraper"](title, location, experience_filters)
                    
                    for job in jobs:
                        if job and is_recent_job(job, date_filter) and not is_duplicate_job(job, all_jobs):
                            all_jobs.append(job)
                    
                    # Small delay between requests to be respectful
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing {config['name']} for '{title}': {e}")
                continue
    
    # Enhance jobs with apply links (limit to avoid overwhelming)
    enhanced_jobs = []
    for job in all_jobs[:30]:  # Limit to first 30 jobs for apply link enhancement
        enhanced_job = enhance_job_with_apply_links(job)
        enhanced_jobs.append(enhanced_job)
        time.sleep(0.5)  # Reduced rate limiting
    
    # Add remaining jobs without enhancement
    enhanced_jobs.extend(all_jobs[30:])
    
    logger.info(f"Total jobs discovered: {len(enhanced_jobs)}")
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

def clean_job_data_updated(job: dict, source: str = "Unknown") -> dict:
    """Updated job data cleaning function for alternative scrapers"""
    try:
        # Create a meaningful description if none exists
        description = job.get('description', '')
        if not description:
            # Create description from available fields
            desc_parts = []
            if job.get('title'):
                desc_parts.append(f"Position: {job.get('title')}")
            if job.get('experience'):
                desc_parts.append(f"Experience: {job.get('experience')}")
            if job.get('salary'):
                desc_parts.append(f"Salary: {job.get('salary')}")
            if job.get('job_type'):
                desc_parts.append(f"Type: {job.get('job_type')}")
            description = '. '.join(desc_parts) if desc_parts else f"{job.get('title', '')} position at {job.get('company_name', '')}"
        
        # Ensure apply_url is properly formatted
        apply_url = job.get('apply_url', '')
        apply_options = []
        
        if apply_url:
            apply_options.append({
                'title': f"Apply on {source}",
                'link': apply_url
            })
        
        cleaned = {
            'title': job.get('title', ''),
            'company_name': job.get('company_name', ''),
            'location': job.get('location', ''),
            'description': description,
            'job_id': job.get('job_id', f"{source}_{abs(hash(job.get('title', '') + job.get('company_name', '')))}"),
            'posted_at': job.get('posted_at', ''),
            'salary': job.get('salary', ''),
            'job_type': job.get('job_type', ''),
            'apply_options': apply_options,
            'related_links': job.get('related_links', []),
            'source': source,
            'career_page': None,
            'apply_links': [],
            'has_direct_apply': bool(apply_url)
        }
        
        # Ensure we have at least a title and company
        if not cleaned['title'] or not cleaned['company_name']:
            return None
            
        return cleaned
    except Exception as e:
        logger.error(f"Error cleaning job data: {e}")
        return None

def calculate_tfidf_similarity(resume_text: str, job_descriptions: list) -> list:
    """Calculate TF-IDF based cosine similarity between resume and job descriptions."""
    if not resume_text or not job_descriptions:
        return [0.0] * len(job_descriptions)
    
    try:
        # Combine resume and all job descriptions for TF-IDF vectorization
        documents = [resume_text] + job_descriptions
        
        # Create TF-IDF vectorizer with optimized parameters for job matching
        vectorizer = TfidfVectorizer(
            max_features=5000,  # Limit vocabulary size
            stop_words='english',  # Remove common English stop words
            ngram_range=(1, 2),  # Include both unigrams and bigrams
            min_df=1,  # Minimum document frequency
            max_df=0.95,  # Maximum document frequency (ignore very common words)
            lowercase=True,
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9+#\.]*\b'  # Include tech terms like C++, C#, .NET
        )
        
        # Fit and transform documents
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Calculate cosine similarity between resume (first document) and each job description
        resume_vector = tfidf_matrix[0:1]  # First row (resume)
        job_vectors = tfidf_matrix[1:]  # Remaining rows (job descriptions)
        
        # Calculate cosine similarities
        similarities = cosine_similarity(resume_vector, job_vectors).flatten()
        
        return similarities.tolist()
        
    except Exception as e:
        logger.error(f"Error in TF-IDF similarity calculation: {e}")
        # Fallback to simple similarity
        return [simple_jaccard_similarity(resume_text, desc) for desc in job_descriptions]

def simple_jaccard_similarity(text1: str, text2: str) -> float:
    """Fallback simple text similarity using Jaccard similarity."""
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
    words1 = words1 - stop_words
    words2 = words2 - stop_words
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def rank_jobs_by_similarity(resume_text: str, jobs: list, experience_data: dict) -> list:
    """Ranks jobs based on TF-IDF cosine similarity between resume and job description, with experience bonus."""
    if not jobs:
        return []
    
    # Enhance job descriptions for better matching
    enhanced_jobs = []
    job_descriptions = []
    
    for job in jobs:
        enhanced_job = job.copy()
        description = job.get('description', '')
        
        # If description is too short, enhance it
        if len(description) < 50:
            enhanced_desc_parts = [description] if description else []
            enhanced_desc_parts.extend([
                f"Job Title: {job.get('title', '')}",
                f"Company: {job.get('company_name', '')}",
                f"Location: {job.get('location', '')}",
            ])
            if job.get('salary'):
                enhanced_desc_parts.append(f"Salary: {job.get('salary')}")
            if job.get('experience'):
                enhanced_desc_parts.append(f"Experience: {job.get('experience')}")
            if job.get('job_type'):
                enhanced_desc_parts.append(f"Job Type: {job.get('job_type')}")
            
            enhanced_job['description'] = '. '.join(filter(None, enhanced_desc_parts))
        
        enhanced_jobs.append(enhanced_job)
        job_descriptions.append(enhanced_job['description'])
    
    try:
        # Calculate TF-IDF similarities for all jobs at once
        similarities = calculate_tfidf_similarity(resume_text, job_descriptions)
        
        # Apply similarity scores and experience bonuses
        for i, job in enumerate(enhanced_jobs):
            # Convert similarity to percentage (0-1 -> 0-100)
            base_score = similarities[i] * 100
            
            # Add experience level bonus
            experience_bonus = get_experience_bonus(job, experience_data)
            
            # Add skills matching bonus
            skills_bonus = get_skills_matching_bonus(job, experience_data)
            
            # Calculate final score with bonuses
            final_score = min(100, max(5, base_score + experience_bonus + skills_bonus))
            
            job['match_score'] = round(final_score, 2)
            
            # Add debug info for top matches
            if final_score > 70:
                logger.info(f"High match: {job.get('title', 'Unknown')} - Base: {base_score:.1f}, Exp: {experience_bonus:.1f}, Skills: {skills_bonus:.1f}, Final: {final_score:.1f}")
            
    except Exception as e:
        logger.error(f"Error in TF-IDF similarity calculation: {e}")
        # Fallback scoring with some randomization for variety
        for i, job in enumerate(enhanced_jobs):
            base_score = 40 + (i % 30) + np.random.randint(0, 20)  # Scores between 40-90
            experience_bonus = get_experience_bonus(job, experience_data)
            skills_bonus = get_skills_matching_bonus(job, experience_data)
            job['match_score'] = round(min(100, base_score + experience_bonus + skills_bonus), 2)
        
    # Sort jobs by score in descending order
    sorted_jobs = sorted(enhanced_jobs, key=lambda x: x['match_score'], reverse=True)
    return sorted_jobs

def get_skills_matching_bonus(job: dict, experience_data: dict) -> float:
    """Calculate bonus based on skills matching between resume and job."""
    user_skills = experience_data.get('skills', [])
    if not user_skills:
        return 0.0
    
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    
    # Count how many user skills are mentioned in the job
    skills_found = 0
    for skill in user_skills:
        if skill.lower() in job_text:
            skills_found += 1
    
    # Calculate bonus: up to 15 points based on skill match percentage
    if len(user_skills) > 0:
        skill_match_ratio = skills_found / len(user_skills)
        skills_bonus = skill_match_ratio * 15  # Max 15 points
        return skills_bonus
    
    return 0.0

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

        # Get filters from request
        date_filter = request.form.get('date_filter', 'all')
        location_filter = request.form.get('location_filter', 'India')

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
        discovered_jobs = discover_jobs_enhanced(experience_data, date_filter, location_filter)
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

# Server-side job saving routes removed - now using localStorage
# These routes are no longer needed as we're using browser localStorage

# @app.route('/save-jobs', methods=['POST'])
# def save_jobs():
#     """Save jobs to local storage."""
#     # Deprecated - using localStorage instead
#     pass

# @app.route('/get-saved-jobs', methods=['GET'])
# def get_saved_jobs():
#     """Retrieve saved jobs from local storage."""
#     # Deprecated - using localStorage instead
#     pass

# @app.route('/clear-saved-jobs', methods=['POST'])
# def clear_saved_jobs():
#     """Clear saved jobs from local storage."""
#     # Deprecated - using localStorage instead
#     pass

if __name__ == '__main__':
    app.run(debug=True)
