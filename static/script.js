// Initialize Lucide icons
lucide.createIcons();

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadSection = document.getElementById('upload-section');
    const uploadLoading = document.getElementById('upload-loading');
    const resultsContainer = document.getElementById('results-container');
    const previewImage = document.getElementById('preview-image');
    
    // Grading Elements
    const gradingResultsPanel = document.getElementById('grading-results-panel');
    const totalScore = document.getElementById('total-score');
    const maxScore = document.getElementById('max-score');
    const overallFeedback = document.getElementById('overall-feedback');
    const gradingStepsContainer = document.getElementById('grading-steps-container');
    
    // Customize loading text
    const loadingText = uploadLoading.querySelector('p');

    // --- UPLOAD LOGIC ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file.');
            return;
        }

        // UI updates
        dropZone.classList.add('hidden');
        uploadLoading.classList.remove('hidden');
        loadingText.textContent = "Running full pipeline (OCR + Grading). This may take a while...";

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Upload Success - Show UI Results
            uploadSection.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
            
            previewImage.src = data.image_url;
            
            // Render Grading Results
            if (data.result && data.result.grading) {
                renderGradingResults(data.result.grading);
            } else {
                overallFeedback.textContent = "No grading data found in the response.";
            }

            // Render MathJax
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetClear();
                window.MathJax.typesetPromise();
            }

        } catch (error) {
            console.error('Upload Error:', error);
            alert('Error processing image: ' + error.message);
            dropZone.classList.remove('hidden');
            uploadLoading.classList.add('hidden');
        }
    }

    function renderGradingResults(gradingData) {
        // Score
        const total = parseFloat(gradingData.total_score || 0);
        const max = parseFloat(gradingData.max_score || 10);
        
        totalScore.textContent = total;
        maxScore.textContent = max;

        // Color code score
        const percentage = total / max;
        if (percentage >= 0.8) totalScore.style.color = 'var(--success)';
        else if (percentage >= 0.5) totalScore.style.color = 'var(--warning)';
        else totalScore.style.color = 'var(--danger)';

        // Feedback
        overallFeedback.textContent = gradingData.overall_feedback || "No overall feedback provided.";

        // Steps
        gradingStepsContainer.innerHTML = '';
        if (gradingData.step_grading && gradingData.step_grading.length > 0) {
            gradingData.step_grading.forEach(step => {
                
                let gradeStatusClass = 'perfect';
                const fScore = parseFloat(step.final_score || 0);
                const bScore = parseFloat(step.base_score || 0);
                
                if (fScore === 0) {
                    gradeStatusClass = 'incorrect';
                } else if (fScore < bScore) {
                    gradeStatusClass = 'partial';
                }

                let latexContent = '';
                if (step.final_latex && step.final_latex.trim() !== '') {
                    latexContent = `$$ ${step.final_latex} $$`;
                } else {
                    latexContent = step.text || '';
                }

                const stepHtml = `
                    <div class="step-card grade-step-card ${gradeStatusClass}">
                        <div class="grade-indicator"></div>
                        <div class="step-header">
                            <span class="step-id">Step ${step.step_id}</span>
                            <span class="grade-step-score">${fScore} / ${bScore}</span>
                        </div>
                        <div class="step-latex" style="background: rgba(0,0,0,0.2); overflow-x: auto;">
                            ${latexContent}
                        </div>
                        <div class="step-feedback">
                            <i data-lucide="message-square" style="width:16px;height:16px;display:inline-block;vertical-align:middle;margin-right:4px;"></i>
                            ${step.feedback || 'No specific feedback.'}
                        </div>
                    </div>
                `;
                gradingStepsContainer.insertAdjacentHTML('beforeend', stepHtml);
            });
            lucide.createIcons();
        }
    }
});
