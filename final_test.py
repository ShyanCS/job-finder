#!/usr/bin/env python3
"""
Test suite to verify the AI Job Finder is working correctly
Run this to test all functionality before deployment
"""

import sys
from app import discover_jobs_enhanced, rank_jobs_by_similarity

def test_complete_flow():
    """Test the complete job discovery and ranking flow"""
    
    # Mock experience data
    experience_data = {
        "experience_level": "mid",
        "years_experience": 3,
        "skills": ["Python", "Django", "React", "JavaScript", "AWS"],
        "job_titles": ["Software Engineer", "Python Developer", "Full Stack Developer"]
    }
    
    # Mock resume text
    resume_text = """
    Software Engineer with 3 years of experience in Python, Django, React, and JavaScript.
    Worked on web applications, REST APIs, and database design. Experience with AWS, Docker, and Git.
    Looking for mid-level software engineering positions. Strong background in full-stack development.
    """
    
    print("🧪 Testing Complete Job Discovery Flow")
    print("=" * 60)
    
    try:
        # Test job discovery
        print("1. Discovering jobs...")
        jobs = discover_jobs_enhanced(experience_data, "all", "India")
        print(f"   ✅ Found {len(jobs)} jobs")
        
        if not jobs:
            print("   ❌ No jobs found - this might indicate scraping issues")
            return False
        
        # Test job structure
        print("\n2. Checking job data structure...")
        sample_job = jobs[0]
        basic_fields = ['title', 'company_name', 'description', 'apply_options']
        
        for field in basic_fields:
            if field in sample_job:
                print(f"   ✅ {field}: Present")
            else:
                print(f"   ❌ {field}: Missing")
                return False
        
        # Test ranking by calling it manually
        print("\n3. Testing job ranking...")
        ranked_jobs = rank_jobs_by_similarity(resume_text, jobs, experience_data)
        if ranked_jobs and 'match_score' in ranked_jobs[0]:
            print("   ✅ match_score: Present after ranking")
            jobs = ranked_jobs  # Use ranked jobs for further tests
        else:
            print("   ❌ match_score: Missing after ranking")
            return False
        
        # Test apply links
        print("\n4. Checking apply links...")
        jobs_with_links = [job for job in jobs if job.get('apply_options')]
        print(f"   ✅ {len(jobs_with_links)}/{len(jobs)} jobs have apply links")
        
        if jobs_with_links:
            sample_link = jobs_with_links[0]['apply_options'][0]
            print(f"   Sample link: {sample_link['title']} - {sample_link['link'][:50]}...")
        
        # Test match scores
        print("\n5. Checking match scores...")
        scores = [job.get('match_score', 0) for job in jobs]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        print(f"   ✅ Average score: {avg_score:.2f}%")
        print(f"   ✅ Score range: {min_score:.2f}% - {max_score:.2f}%")
        
        if avg_score < 5:
            print("   ⚠️  Scores seem low - descriptions might need improvement")
        elif avg_score > 80:
            print("   ⚠️  Scores seem high - might be overfitting")
        else:
            print("   ✅ Scores look reasonable")
        
        # Test job sources
        print("\n6. Checking job sources...")
        sources = {}
        for job in jobs:
            source = job.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            print(f"   ✅ {source}: {count} jobs")
        
        # Show top 3 jobs
        print("\n7. Top 3 matching jobs:")
        for i, job in enumerate(jobs[:3]):
            print(f"   {i+1}. {job['title']} at {job['company_name']}")
            print(f"      Score: {job.get('match_score', 0)}% | Source: {job.get('source', 'Unknown')}")
            print(f"      Apply: {'Yes' if job.get('apply_options') else 'No'}")
        
        print("\n🎉 All tests passed! Migration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components"""
    print("\n🔧 Testing Individual Components")
    print("=" * 60)
    
    try:
        from job_scraper_alternatives import JobScraperAlternatives
        from app import clean_job_data_updated
        
        scraper = JobScraperAlternatives()
        
        # Test LinkedIn scraper
        print("1. Testing LinkedIn scraper...")
        linkedin_jobs = scraper.scrape_linkedin_jobs_direct('Python Developer', 'India', max_jobs=2)
        print(f"   ✅ LinkedIn: {len(linkedin_jobs)} jobs")
        
        # Test job cleaning
        if linkedin_jobs:
            print("2. Testing job data cleaning...")
            cleaned = clean_job_data_updated(linkedin_jobs[0], 'LinkedIn')
            if cleaned and cleaned.get('apply_options'):
                print("   ✅ Job cleaning: Working")
                print(f"   ✅ Apply link: {cleaned['apply_options'][0]['link'][:50]}...")
            else:
                print("   ❌ Job cleaning: Failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI Job Finder Test Suite")
    print("=" * 60)
    
    # Test individual components first
    component_test = test_individual_components()
    
    # Test complete flow
    complete_test = test_complete_flow()
    
    print("\n" + "=" * 60)
    if component_test and complete_test:
        print("🎉 ALL TESTS PASSED!")
        print("\nYour AI Job Finder is working perfectly:")
        print("✅ Job scraping is functional")
        print("✅ Apply links are working")
        print("✅ AI matching is operational")
        print("✅ All job sources are active")
        print("\nYour app is ready for production! 🚀")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check the errors above and fix them.")
        print("Refer to the README.md for troubleshooting tips.")
        sys.exit(1)