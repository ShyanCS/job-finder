// DOM Elements
const fileUploadArea = document.getElementById('file-upload-area');
const fileInput = document.getElementById('resume-file');
const submitBtn = document.getElementById('submit-btn');
const loadingSection = document.getElementById('loading');
const resultsSection = document.getElementById('results-section');
const resultsCount = document.getElementById('results-count');
const jobsGrid = document.getElementById('jobs-grid');
const resultsFilters = document.getElementById('results-filters');
const dateFilterOptions = document.getElementById('date-filter-options');
const statsSection = document.getElementById('stats-section');
const statsGrid = document.getElementById('stats-grid');

// Global variables
let currentDateFilter = 'all';
let currentJobs = [];

// File upload handling
fileUploadArea.addEventListener('click', () => {
    fileInput.click();
});

fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelection();
    }
});

fileInput.addEventListener('change', handleFileSelection);

// Date filter handling
dateFilterOptions.addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-option')) {
        // Remove active class from all options
        dateFilterOptions.querySelectorAll('.filter-option').forEach(option => {
            option.classList.remove('active');
        });
        
        // Add active class to clicked option
        e.target.classList.add('active');
        
        // Update current filter
        currentDateFilter = e.target.dataset.value;
    }
});

function handleFileSelection() {
    const file = fileInput.files[0];
    if (file) {
        // Update UI to show selected file
        const uploadText = fileUploadArea.querySelector('.upload-text');
        const uploadHint = fileUploadArea.querySelector('.upload-hint');
        
        uploadText.textContent = `Selected: ${file.name}`;
        uploadHint.textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        
        // Enable submit button
        submitBtn.disabled = false;
    }
}

// Form submission
submitBtn.addEventListener('click', async function(event) {
    event.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        showError('Please select a resume file.');
        return;
    }

    // Check file type
    if (!file.type.includes('pdf')) {
        showError('Please upload a PDF file.');
        return;
    }

    // Show loading state
    showLoading();
    hideResults();
    hideError();

    // Prepare form data
    const formData = new FormData();
    formData.append('resume', file);
    formData.append('date_filter', currentDateFilter);

    try {
        const response = await fetch('/find-jobs', {
            method: 'POST',
            body: formData
        });

        hideLoading();

        if (!response.ok) {
            const errorData = await response.json();
            showError(errorData.error || 'Something went wrong. Please try again.');
            return;
        }

        const jobs = await response.json();

        if (jobs.length === 0) {
            showNoResults();
            return;
        }

        currentJobs = jobs;
        displayJobs(jobs);

    } catch (error) {
        hideLoading();
        showError('Network error. Please check your connection and try again.');
        console.error('Fetch error:', error);
    }
});

function displayJobs(jobs) {
    // Update results count
    resultsCount.textContent = `Found ${jobs.length} job${jobs.length !== 1 ? 's' : ''} for you`;
    
    // Update filters display
    updateResultsFilters();
    
    // Update statistics
    updateStatistics(jobs);
    
    // Clear previous results
    jobsGrid.innerHTML = '';
    
    // Create job cards
    jobs.forEach(job => {
        const jobCard = createJobCard(job);
        jobsGrid.appendChild(jobCard);
    });
    
    // Show results section
    showResults();
}

function updateStatistics(jobs) {
    const stats = {
        totalJobs: jobs.length,
        directApply: jobs.filter(job => job.has_direct_apply).length,
        linkedinJobs: jobs.filter(job => job.source === 'LinkedIn').length,
        indeedJobs: jobs.filter(job => job.source === 'Indeed').length,
        googleJobs: jobs.filter(job => job.source === 'Google Jobs').length,
        naukriJobs: jobs.filter(job => job.source === 'Naukri').length
    };

    statsGrid.innerHTML = `
        <div class="stat-item">
            <div class="stat-number">${stats.totalJobs}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.directApply}</div>
            <div class="stat-label">Direct Apply</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.linkedinJobs}</div>
            <div class="stat-label">LinkedIn</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.indeedJobs}</div>
            <div class="stat-label">Indeed</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.googleJobs}</div>
            <div class="stat-label">Google Jobs</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.naukriJobs}</div>
            <div class="stat-label">Naukri</div>
        </div>
    `;

    statsSection.style.display = 'block';
}

function updateResultsFilters() {
    resultsFilters.innerHTML = '';
    
    // Add date filter badge
    const dateFilterText = getDateFilterText(currentDateFilter);
    const dateBadge = document.createElement('div');
    dateBadge.className = 'filter-badge';
    dateBadge.innerHTML = `<i class="fas fa-calendar"></i> ${dateFilterText}`;
    resultsFilters.appendChild(dateBadge);
}

function getDateFilterText(filter) {
    const filterTexts = {
        'all': 'All Time',
        '24h': 'Last 24 Hours',
        'week': 'Last Week',
        'month': 'Last Month',
        '3months': 'Last 3 Months'
    };
    return filterTexts[filter] || 'All Time';
}

function createJobCard(job) {
    const jobCard = document.createElement('div');
    jobCard.className = 'job-card';

    // Job title
    const title = document.createElement('h3');
    title.className = 'job-title';
    title.textContent = job.title || 'Job Title Not Available';
    jobCard.appendChild(title);

    // Job source badge
    if (job.source) {
        const source = document.createElement('div');
        source.className = 'job-source';
        source.textContent = job.source;
        jobCard.appendChild(source);
    }

    // Company name
    if (job.company_name) {
        const company = document.createElement('div');
        company.className = 'job-company';
        company.textContent = job.company_name;
        jobCard.appendChild(company);
    }

    // Location
    if (job.location) {
        const location = document.createElement('div');
        location.className = 'job-location';
        location.innerHTML = `<i class="fas fa-map-marker-alt"></i> ${job.location}`;
        jobCard.appendChild(location);
    }

    // Posted date
    if (job.posted_at) {
        const posted = document.createElement('div');
        posted.className = 'job-posted';
        posted.innerHTML = `<i class="fas fa-clock"></i> Posted: ${formatPostedDate(job.posted_at)}`;
        jobCard.appendChild(posted);
    }

    // Description
    if (job.description) {
        const description = document.createElement('div');
        description.className = 'job-description';
        description.textContent = job.description;
        jobCard.appendChild(description);
    }

    // Meta section (match score and actions)
    const meta = document.createElement('div');
    meta.className = 'job-meta';

    // Match score
    if (job.match_score !== undefined) {
        const score = document.createElement('div');
        score.className = 'match-score';
        score.textContent = `${job.match_score}% Match`;
        meta.appendChild(score);
    }

    // Actions
    const actions = document.createElement('div');
    actions.className = 'job-actions';

    // Apply button
    const applyBtn = document.createElement('a');
    applyBtn.className = 'btn btn-primary';
    applyBtn.innerHTML = '<i class="fas fa-external-link-alt"></i> Apply Now';
    applyBtn.target = '_blank';

    // Check if apply link exists
    if (job.apply_options && job.apply_options.length > 0 && job.apply_options[0].link) {
        applyBtn.href = job.apply_options[0].link;
        applyBtn.title = 'Apply for this position';
    } else {
        // No apply link available
        applyBtn.className = 'btn btn-disabled';
        applyBtn.textContent = 'No Apply Link';
        applyBtn.style.pointerEvents = 'none';
        applyBtn.title = 'No application link available for this position';
    }

    actions.appendChild(applyBtn);

    // Direct Apply button (if available)
    if (job.has_direct_apply && job.apply_links && job.apply_links.length > 0) {
        const directApplyBtn = document.createElement('a');
        directApplyBtn.className = 'btn btn-success';
        directApplyBtn.innerHTML = '<i class="fas fa-rocket"></i> Direct Apply';
        directApplyBtn.href = job.apply_links[0].url;
        directApplyBtn.target = '_blank';
        directApplyBtn.title = 'Apply directly on company website';
        actions.appendChild(directApplyBtn);
    }

    // Career Page button
    if (job.career_page) {
        const careerBtn = document.createElement('a');
        careerBtn.className = 'btn btn-secondary';
        careerBtn.innerHTML = '<i class="fas fa-building"></i> Career Page';
        careerBtn.href = job.career_page;
        careerBtn.target = '_blank';
        careerBtn.title = 'Visit company career page';
        actions.appendChild(careerBtn);
    }

    // View Details button (if we have more info)
    if (job.job_id || job.related_links || job.salary || job.job_type) {
        const detailsBtn = document.createElement('button');
        detailsBtn.className = 'btn btn-secondary';
        detailsBtn.innerHTML = '<i class="fas fa-info-circle"></i> Details';
        detailsBtn.onclick = () => showJobDetails(job);
        actions.appendChild(detailsBtn);
    }

    meta.appendChild(actions);
    jobCard.appendChild(meta);

    // Apply links section (if available)
    if (job.apply_links && job.apply_links.length > 0) {
        const applyLinksSection = document.createElement('div');
        applyLinksSection.className = 'apply-links';
        
        const applyLinksTitle = document.createElement('h4');
        applyLinksTitle.innerHTML = '<i class="fas fa-link"></i> Direct Apply Links';
        applyLinksSection.appendChild(applyLinksTitle);
        
        job.apply_links.forEach(link => {
            const linkItem = document.createElement('div');
            linkItem.className = 'apply-link-item';
            
            const linkText = document.createElement('div');
            linkText.className = 'apply-link-text';
            linkText.textContent = link.text || 'Apply';
            
            const linkBtn = document.createElement('a');
            linkBtn.className = 'apply-link-btn';
            linkBtn.href = link.url;
            linkBtn.target = '_blank';
            linkBtn.textContent = 'Apply';
            
            linkItem.appendChild(linkText);
            linkItem.appendChild(linkBtn);
            applyLinksSection.appendChild(linkItem);
        });
        
        jobCard.appendChild(applyLinksSection);
    }

    return jobCard;
}

function formatPostedDate(dateStr) {
    if (!dateStr) return 'Date not available';
    
    try {
        // Try to parse the date string
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) {
            return dateStr; // Return original if parsing fails
        }
        
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        
        return date.toLocaleDateString();
    } catch {
        return dateStr;
    }
}

function showJobDetails(job) {
    // Create a modal or expand the card to show more details
    const details = [];
    
    if (job.job_id) details.push(`Job ID: ${job.job_id}`);
    if (job.posted_at) details.push(`Posted: ${job.posted_at}`);
    if (job.salary) details.push(`Salary: ${job.salary}`);
    if (job.job_type) details.push(`Type: ${job.job_type}`);
    if (job.source) details.push(`Source: ${job.source}`);
    if (job.career_page) details.push(`Career Page: ${job.career_page}`);
    
    if (job.related_links && job.related_links.length > 0) {
        details.push('Related Links:');
        job.related_links.forEach(link => {
            details.push(`- ${link.link} (${link.text})`);
        });
    }
    
    if (job.apply_links && job.apply_links.length > 0) {
        details.push('Direct Apply Links:');
        job.apply_links.forEach(link => {
            details.push(`- ${link.url} (${link.text})`);
        });
    }
    
    if (details.length > 0) {
        alert(`Job Details:\n\n${details.join('\n')}`);
    } else {
        alert('No additional details available for this position.');
    }
}

// UI Helper Functions
function showLoading() {
    loadingSection.style.display = 'block';
    submitBtn.disabled = true;
}

function hideLoading() {
    loadingSection.style.display = 'none';
    submitBtn.disabled = false;
}

function showResults() {
    resultsSection.style.display = 'block';
}

function hideResults() {
    resultsSection.style.display = 'none';
    statsSection.style.display = 'none';
}

function showError(message) {
    // Remove existing error messages
    hideError();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    
    // Insert after upload section
    const uploadSection = document.querySelector('.upload-section');
    uploadSection.parentNode.insertBefore(errorDiv, uploadSection.nextSibling);
}

function hideError() {
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

function showNoResults() {
    hideResults();
    
    const noResultsDiv = document.createElement('div');
    noResultsDiv.className = 'no-results';
    noResultsDiv.innerHTML = `
        <i class="fas fa-search"></i>
        <h3>No matching jobs found</h3>
        <p>We couldn't find any jobs that match your profile right now. Try updating your resume or checking back later.</p>
    `;
    
    // Insert after upload section
    const uploadSection = document.querySelector('.upload-section');
    uploadSection.parentNode.insertBefore(noResultsDiv, uploadSection.nextSibling);
}