import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, quote
import logging

logger = logging.getLogger(__name__)

class JobScraperAlternatives:
    """Alternative job scraping methods to replace RapidAPI"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_naukri_direct(self, job_title: str, location: str = "India", max_jobs: int = 20) -> list:
        """Direct Naukri scraping without API"""
        jobs = []
        try:
            # Format search URL
            formatted_title = job_title.lower().replace(' ', '-')
            formatted_location = location.lower().replace(' ', '-')
            
            search_url = f"https://www.naukri.com/{formatted_title}-jobs-in-{formatted_location}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return jobs
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job cards (Naukri's current structure)
            job_cards = soup.find_all('div', class_='jobTuple')
            
            for card in job_cards[:max_jobs]:
                try:
                    # Extract job details
                    title_elem = card.find('a', class_='title')
                    company_elem = card.find('a', class_='subTitle')
                    location_elem = card.find('span', class_='locationsContainer')
                    experience_elem = card.find('span', class_='expwdth')
                    salary_elem = card.find('span', class_='salary')
                    
                    if title_elem and company_elem:
                        # Try to get job description or create one
                        desc_elem = card.find('span', class_='job-description')
                        description = desc_elem.text.strip() if desc_elem else ''
                        
                        # If no description, create enhanced one from available info
                        if not description:
                            title_text = title_elem.text.strip()
                            desc_parts = [f"Position: {title_text}"]
                            
                            if experience_elem:
                                desc_parts.append(f"Experience Required: {experience_elem.text.strip()}")
                            if salary_elem:
                                desc_parts.append(f"Salary: {salary_elem.text.strip()}")
                            
                            # Add relevant keywords based on job title for better matching
                            if 'python' in title_text.lower():
                                desc_parts.append("Skills: Python programming, Django, Flask, web development")
                            if 'java' in title_text.lower():
                                desc_parts.append("Skills: Java programming, Spring, enterprise applications")
                            if 'react' in title_text.lower():
                                desc_parts.append("Skills: React, JavaScript, frontend development")
                            if 'full stack' in title_text.lower():
                                desc_parts.append("Skills: Full stack development, frontend and backend")
                            if 'senior' in title_text.lower():
                                desc_parts.append("Level: Senior position with leadership responsibilities")
                            
                            description = '. '.join(desc_parts)
                        
                        job = {
                            'title': title_elem.text.strip(),
                            'company_name': company_elem.text.strip(),
                            'location': location_elem.text.strip() if location_elem else location,
                            'experience': experience_elem.text.strip() if experience_elem else '',
                            'salary': salary_elem.text.strip() if salary_elem else '',
                            'apply_url': urljoin('https://www.naukri.com', title_elem.get('href', '')),
                            'source': 'Naukri',
                            'description': description,
                            'posted_at': '',
                            'job_type': ''
                        }
                        jobs.append(job)
                        
                except Exception as e:
                    logger.error(f"Error parsing Naukri job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")
            
        return jobs
    
    def scrape_indeed_direct(self, job_title: str, location: str = "India", max_jobs: int = 20) -> list:
        """Direct Indeed scraping without API"""
        jobs = []
        try:
            # Format search parameters
            params = {
                'q': job_title,
                'l': location,
                'start': 0
            }
            
            search_url = "https://in.indeed.com/jobs"
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return jobs
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job cards (Indeed's structure)
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')
                    salary_elem = card.find('span', class_='salary-snippet')
                    
                    if title_elem and company_elem:
                        title_link = title_elem.find('a')
                        
                        # Try to get job description
                        desc_elem = card.find('div', class_='job-snippet')
                        description = desc_elem.text.strip() if desc_elem else ''
                        
                        # If no description, create enhanced one
                        if not description:
                            title_text = title_link.text.strip() if title_link else title_elem.text.strip()
                            desc_parts = [f"Position: {title_text}"]
                            
                            if salary_elem:
                                desc_parts.append(f"Salary: {salary_elem.text.strip()}")
                            
                            # Add relevant keywords based on job title for better matching
                            if 'python' in title_text.lower():
                                desc_parts.append("Skills: Python programming, web development, software engineering")
                            if 'java' in title_text.lower():
                                desc_parts.append("Skills: Java programming, enterprise development, backend systems")
                            if 'react' in title_text.lower():
                                desc_parts.append("Skills: React, JavaScript, frontend development, UI/UX")
                            if 'full stack' in title_text.lower():
                                desc_parts.append("Skills: Full stack development, both frontend and backend")
                            if 'senior' in title_text.lower():
                                desc_parts.append("Level: Senior role with advanced responsibilities")
                            
                            description = '. '.join(desc_parts)
                        
                        job = {
                            'title': title_link.text.strip() if title_link else title_elem.text.strip(),
                            'company_name': company_elem.text.strip(),
                            'location': location_elem.text.strip() if location_elem else location,
                            'salary': salary_elem.text.strip() if salary_elem else '',
                            'apply_url': urljoin('https://in.indeed.com', title_link.get('href', '')) if title_link else '',
                            'source': 'Indeed',
                            'description': description,
                            'posted_at': '',
                            'job_type': '',
                            'experience': ''
                        }
                        jobs.append(job)
                        
                except Exception as e:
                    logger.error(f"Error parsing Indeed job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
            
        return jobs
    
    def scrape_linkedin_jobs_direct(self, job_title: str, location: str = "India", max_jobs: int = 15) -> list:
        """Direct LinkedIn Jobs scraping (limited due to anti-bot measures)"""
        jobs = []
        try:
            # LinkedIn is heavily protected, but we can try basic scraping
            params = {
                'keywords': job_title,
                'location': location,
                'f_TPR': 'r86400'  # Past 24 hours
            }
            
            search_url = "https://www.linkedin.com/jobs/search"
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return jobs
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # LinkedIn job cards (structure may change frequently)
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    
                    if title_elem and company_elem:
                        # Try to get job link
                        job_link = card.find('a')
                        apply_url = urljoin('https://www.linkedin.com', job_link.get('href', '')) if job_link else ''
                        
                        # Create enhanced description with common job keywords
                        title_text = title_elem.text.strip()
                        company_text = company_elem.text.strip()
                        
                        # Enhanced description with relevant keywords for better matching
                        description_parts = [
                            f"Position: {title_text}",
                            f"Company: {company_text}",
                        ]
                        
                        if location_elem:
                            description_parts.append(f"Location: {location_elem.text.strip()}")
                        
                        # Add relevant keywords based on job title
                        if 'python' in title_text.lower():
                            description_parts.append("Skills: Python programming, software development, web applications")
                        if 'java' in title_text.lower():
                            description_parts.append("Skills: Java programming, enterprise applications, backend development")
                        if 'react' in title_text.lower():
                            description_parts.append("Skills: React, JavaScript, frontend development, web applications")
                        if 'full stack' in title_text.lower():
                            description_parts.append("Skills: Full stack development, frontend, backend, web technologies")
                        if 'senior' in title_text.lower():
                            description_parts.append("Experience: Senior level position, leadership, mentoring")
                        if 'engineer' in title_text.lower():
                            description_parts.append("Role: Software engineering, technical design, problem solving")
                        
                        description = '. '.join(description_parts)
                        
                        job = {
                            'title': title_text,
                            'company_name': company_text,
                            'location': location_elem.text.strip() if location_elem else location,
                            'source': 'LinkedIn',
                            'description': description,
                            'posted_at': '',
                            'job_type': '',
                            'salary': '',
                            'experience': '',
                            'apply_url': apply_url
                        }
                        jobs.append(job)
                        
                except Exception as e:
                    logger.error(f"Error parsing LinkedIn job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            
        return jobs
    
    def use_jsearch_api(self, job_title: str, location: str = "India", rapidapi_key: str = None) -> list:
        """Use JSearch API via RapidAPI (2500 free requests/month)"""
        if not rapidapi_key:
            return []
            
        jobs = []
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            params = {
                "query": f"{job_title} in {location}",
                "page": "1",
                "num_pages": "1"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for job_data in data.get('data', []):
                    # Ensure we have a good description
                    description = job_data.get('job_description', '')
                    if not description:
                        # Create description from available fields
                        desc_parts = [f"Job Title: {job_data.get('job_title', '')}"]
                        if job_data.get('job_employment_type'):
                            desc_parts.append(f"Employment Type: {job_data.get('job_employment_type')}")
                        if job_data.get('job_salary'):
                            desc_parts.append(f"Salary: {job_data.get('job_salary')}")
                        description = '. '.join(desc_parts)
                    
                    # Safely handle location concatenation
                    job_city = job_data.get('job_city') or ''
                    job_country = job_data.get('job_country') or ''
                    location = f"{job_city}, {job_country}".strip(', ') if job_city or job_country else location
                    
                    job = {
                        'title': job_data.get('job_title', ''),
                        'company_name': job_data.get('employer_name', ''),
                        'location': location,
                        'description': description,
                        'salary': job_data.get('job_salary', ''),
                        'job_type': job_data.get('job_employment_type', ''),
                        'apply_url': job_data.get('job_apply_link', ''),
                        'posted_at': job_data.get('job_posted_at_datetime_utc', ''),
                        'source': 'JSearch API',
                        'experience': ''
                    }
                    jobs.append(job)
                    
        except Exception as e:
            logger.error(f"Error using JSearch API: {e}")
            
        return jobs
    
    def scrape_all_sources(self, job_title: str, location: str = "India", rapidapi_key: str = None) -> list:
        """Scrape jobs from all available sources"""
        all_jobs = []
        
        # Direct scraping sources
        sources = [
            ('Naukri', self.scrape_naukri_direct),
            ('Indeed', self.scrape_indeed_direct),
            ('LinkedIn', self.scrape_linkedin_jobs_direct)
        ]
        
        for source_name, scraper_func in sources:
            try:
                logger.info(f"Scraping {source_name} for '{job_title}' in {location}")
                jobs = scraper_func(job_title, location)
                all_jobs.extend(jobs)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
        
        # API sources
        if rapidapi_key:
            try:
                logger.info(f"Using JSearch API for '{job_title}' in {location}")
                api_jobs = self.use_jsearch_api(job_title, location, rapidapi_key)
                all_jobs.extend(api_jobs)
            except Exception as e:
                logger.error(f"Error using JSearch API: {e}")
        
        return all_jobs

# Usage example
def get_jobs_without_serpapi(job_titles: list, location: str = "India", rapidapi_key: str = None) -> list:
    """Get jobs using alternative methods instead of SerpAPI"""
    scraper = JobScraperAlternatives()
    all_jobs = []
    
    for title in job_titles:
        jobs = scraper.scrape_all_sources(title, location, rapidapi_key)
        all_jobs.extend(jobs)
        time.sleep(3)  # Rate limiting between different job titles
    
    # Remove duplicates
    unique_jobs = []
    seen = set()
    
    for job in all_jobs:
        job_key = (job['title'].lower(), job['company_name'].lower())
        if job_key not in seen:
            seen.add(job_key)
            unique_jobs.append(job)
    
    return unique_jobs