document.addEventListener('DOMContentLoaded', () => {
    const authSection = document.getElementById('auth-section');
    const recruiterSection = document.getElementById('recruiter-section');
    const seekerSection = document.getElementById('seeker-section');
    const navButtons = document.getElementById('navButtons');
    const homeLink = document.getElementById('homeLink');

    const loginModal = document.getElementById('loginModal');
    const signupModal = document.getElementById('signupModal');
    const heroSignupBtn = document.getElementById('heroSignupBtn');

    const recruiterProfileImage = document.getElementById('recruiterProfileImage');
    const recruiterUsername = document.getElementById('recruiterUsername');
    const recruiterBio = document.getElementById('recruiterBio');
    const seekerProfileImage = document.getElementById('seekerProfileImage');
    const seekerUsername = document.getElementById('seekerUsername');
    const seekerBio = document.getElementById('seekerBio');

    const searchJobType = document.getElementById('search-job-type');
    const searchLocation = document.getElementById('search-location');
    const searchJobLevel = document.getElementById('search-job-level');
    const searchEmploymentType = document.getElementById('search-employment-type');
    const searchJobsBtn = document.getElementById('search-jobs-btn');

    let currentUser = initialUserData;

    function showMessage(elementId, message, type) {
        const msgBox = document.getElementById(elementId);
        if (msgBox) {
            msgBox.textContent = message;
            msgBox.className = `message-box ${type}`;
            msgBox.style.display = 'block';
            setTimeout(() => {
                msgBox.style.display = 'none';
                msgBox.textContent = '';
            }, 5000);
        }
    }

    function updateHeaderAndDisplaySections() {
        navButtons.innerHTML = '';

        if (currentUser && currentUser.user_id) {
            const welcomeSpan = document.createElement('span');
            welcomeSpan.textContent = `Welcome, ${currentUser.username} (${currentUser.user_type === 'recruiter' ? 'Recruiter' : 'Seeker'})`;
            navButtons.appendChild(welcomeSpan);

            const logoutButton = document.createElement('button');
            logoutButton.textContent = 'Logout';
            logoutButton.addEventListener('click', handleLogout);
            navButtons.appendChild(logoutButton);

            if (currentUser.user_type === 'recruiter') {
                recruiterProfileImage.src = currentUser.profile_image_url || 'https://placehold.co/80x80/4A90E2/FFFFFF?text=R';
                recruiterUsername.textContent = currentUser.username;
                recruiterBio.textContent = currentUser.bio || 'No bio provided.';
            } else if (currentUser.user_type === 'seeker') {
                seekerProfileImage.src = currentUser.profile_image_url || 'https://placehold.co/80x80/7D4AE2/FFFFFF?text=S';
                seekerUsername.textContent = currentUser.username;
                seekerBio.textContent = currentUser.bio || 'No bio provided.';
            }

            authSection.classList.add('hidden');
            if (currentUser.user_type === 'recruiter') {
                recruiterSection.classList.remove('hidden');
                seekerSection.classList.add('hidden');
                fetchPostedJobs();
            } else if (currentUser.user_type === 'seeker') {
                seekerSection.classList.remove('hidden');
                recruiterSection.classList.add('hidden');
                fetchAvailableJobs();
                fetchAppliedJobs();
            }
        } else {
            const loginButton = document.createElement('button');
            loginButton.textContent = 'Login';
            loginButton.addEventListener('click', () => openModal('loginModal'));

            const signupButton = document.createElement('button');
            signupButton.textContent = 'Sign Up';
            signupButton.addEventListener('click', () => openModal('signupModal'));

            navButtons.appendChild(loginButton);
            navButtons.appendChild(signupButton);

            authSection.classList.remove('hidden');
            recruiterSection.classList.add('hidden');
            seekerSection.classList.add('hidden');
        }
    }

    homeLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentUser && currentUser.user_id) {
            if (currentUser.user_type === 'recruiter') {
                recruiterSection.classList.remove('hidden');
                seekerSection.classList.add('hidden');
                authSection.classList.add('hidden');
                fetchPostedJobs();
            } else if (currentUser.user_type === 'seeker') {
                seekerSection.classList.remove('hidden');
                recruiterSection.classList.add('hidden');
                authSection.classList.add('hidden');
                fetchAvailableJobs();
                fetchAppliedJobs();
            }
        } else {
            authSection.classList.remove('hidden');
            recruiterSection.classList.add('hidden');
            seekerSection.classList.add('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    if (heroSignupBtn) {
        heroSignupBtn.addEventListener('click', () => {
            openModal('signupModal');
            document.getElementById('user_type_seeker').checked = true;
        });
    }

    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(signupForm);
            const response = await fetch('/api/signup', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.success) {
                showMessage('signupMessage', result.message, 'success');
                signupForm.reset();
                closeModal('signupModal');
                openModal('loginModal');
            } else {
                showMessage('signupMessage', result.message, 'error');
            }
        });
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(loginForm);
            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.success) {
                showMessage('loginMessage', 'Login successful!', 'success');
                currentUser = result.user;
                closeModal('loginModal');
                updateHeaderAndDisplaySections();
            } else {
                showMessage('loginMessage', result.message, 'error');
            }
        });
    }

    async function handleLogout() {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            currentUser = null;
            updateHeaderAndDisplaySections();
        } else {
            console.error('Logout failed:', result.message);
        }
    }

    const postJobForm = document.getElementById('postJobForm');
    if (postJobForm) {
        postJobForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(postJobForm);
            const response = await fetch('/api/post_job', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.success) {
                showMessage('postJobMessage', result.message, 'success');
                postJobForm.reset();
                fetchPostedJobs();
            } else {
                showMessage('postJobMessage', result.message, 'error');
            }
        });
    }

    async function fetchPostedJobs() {
        const jobListContainer = document.getElementById('recruiterJobList');
        if (!jobListContainer || !currentUser || currentUser.user_type !== 'recruiter') return;

        try {
            const response = await fetch('/api/recruiter_jobs');
            const data = await response.json();

            if (data.success && data.jobs) {
                jobListContainer.innerHTML = '';
                if (data.jobs.length === 0) {
                    jobListContainer.innerHTML = '<p>No jobs posted yet.</p>';
                } else {
                    data.jobs.forEach(job => {
                        const jobDiv = document.createElement('div');
                        jobDiv.classList.add('job-item');
                        jobDiv.innerHTML = `
                            <h3>${job.title} at ${job.company}</h3>
                            <p class="location"><strong>Location:</strong> ${job.location}</p>
                            <p><strong>Description:</strong> ${job.description}</p>
                            <p class="salary"><strong>Salary:</strong> ${job.salary || 'Not specified'}</p>
                            <p><strong>Posted On:</strong> ${new Date(job.posted_at).toLocaleDateString()}</p>
                        `;
                        jobListContainer.appendChild(jobDiv);
                    });
                }
            } else {
                jobListContainer.innerHTML = `<p class="error-message">${data.message || 'Error loading jobs.'}</p>`;
            }
        } catch (error) {
            console.error('Error fetching posted jobs:', error);
            jobListContainer.innerHTML = '<p class="error-message">Could not load jobs.</p>';
        }
    }

    async function fetchAvailableJobs(filters = {}) {
        const availableJobsContainer = document.getElementById('availableJobsList');
        if (!availableJobsContainer || !currentUser || currentUser.user_type !== 'seeker') return;

        try {
            const queryParams = new URLSearchParams(filters).toString();
            const url = `/api/jobs${queryParams ? `?${queryParams}` : ''}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.jobs) {
                availableJobsContainer.innerHTML = '';
                if (data.jobs.length === 0) {
                    availableJobsContainer.innerHTML = '<p>No jobs available at the moment matching your criteria.</p>';
                } else {
                    data.jobs.forEach(job => {
                        const jobDiv = document.createElement('div');
                        jobDiv.classList.add('job-item');
                        jobDiv.innerHTML = `
                            <h3>${job.title} at ${job.company}</h3>
                            <p class="location"><strong>Location:</strong> ${job.location}</p>
                            <p><strong>Description:</strong> ${job.description}</p>
                            <p><strong>Job Type:</strong> ${job.job_type || 'N/A'}</p>
                            <p><strong>Job Level:</strong> ${job.job_level || 'N/A'}</p>
                            <p><strong>Employment Type:</strong> ${job.employment_type || 'N/A'}</p>
                            <p class="salary"><strong>Salary:</strong> ${job.salary || 'Not specified'}</p>
                            <p><strong>Posted On:</strong> ${new Date(job.posted_at).toLocaleDateString()}</p>
                            <div class="job-actions">
                                <button class="apply-btn" data-job-id="${job.id}">Apply Now</button>
                            </div>
                        `;
                        availableJobsContainer.appendChild(jobDiv);
                    });

                    document.querySelectorAll('.apply-btn').forEach(button => {
                        button.addEventListener('click', async (e) => {
                            const jobId = e.target.dataset.jobId;
                            const formData = new FormData();
                            formData.append('job_id', jobId);

                            const response = await fetch('/api/apply_job', {
                                method: 'POST',
                                body: formData
                            });
                            const result = await response.json();

                            if (result.success) {
                                showMessage('applyJobMessage', result.message, 'success');
                                fetchAppliedJobs();
                                e.target.textContent = 'Applied';
                                e.target.disabled = true;
                                e.target.style.backgroundColor = '#6c757d';
                            } else {
                                showMessage('applyJobMessage', result.message, 'error');
                            }
                        });
                    });
                }
            } else {
                availableJobsContainer.innerHTML = `<p class="error-message">${data.message || 'Error loading available jobs.'}</p>`;
            }
        } catch (error) {
            console.error('Error fetching available jobs:', error);
            availableJobsContainer.innerHTML = '<p class="error-message">Could not load available jobs.</p>';
        }
    }

    if (searchJobsBtn) {
        searchJobsBtn.addEventListener('click', () => {
            const filters = {
                job_type: searchJobType.value,
                location: searchLocation.value,
                job_level: searchJobLevel.value,
                employment_type: searchEmploymentType.value
            };
            fetchAvailableJobs(filters);
        });
    }

    async function fetchAppliedJobs() {
        const appliedJobsContainer = document.getElementById('appliedJobsList');
        if (!appliedJobsContainer || !currentUser || currentUser.user_type !== 'seeker') return;

        try {
            const response = await fetch('/api/seeker_applications');
            const data = await response.json();

            if (data.success && data.applications) {
                appliedJobsContainer.innerHTML = '';
                if (data.applications.length === 0) {
                    appliedJobsContainer.innerHTML = '<p>No jobs applied yet.</p>';
                } else {
                    data.applications.forEach(app => {
                        const appDiv = document.createElement('div');
                        appDiv.classList.add('applied-job-item');
                        appDiv.innerHTML = `
                            <h3>${app.title} at ${app.company}</h3>
                            <p class="location"><strong>Location:</strong> ${app.location}</p>
                            <p><strong>Job Type:</strong> ${app.job_type || 'N/A'}</p>
                            <p><strong>Job Level:</strong> ${app.job_level || 'N/A'}</p>
                            <p><strong>Employment Type:</strong> ${app.employment_type || 'N/A'}</p>
                            <p><strong>Applied On:</strong> ${new Date(app.application_date).toLocaleDateString()}</p>
                            <p><strong>Status:</strong> <span style="text-transform: capitalize; color: ${app.status === 'accepted' ? 'green' : (app.status === 'rejected' ? 'red' : '#ffc107')}">${app.status}</span></p>
                        `;
                        appliedJobsContainer.appendChild(appDiv);
                    });
                }
            } else {
                appliedJobsContainer.innerHTML = `<p class="error-message">${data.message || 'Error loading applied jobs.'}</p>`;
            }
        } catch (error) {
            console.error('Error fetching applied jobs:', error);
            appliedJobsContainer.innerHTML = '<p class="error-message">Could not load applied jobs.</p>';
        }
    }

    updateHeaderAndDisplaySections();
});