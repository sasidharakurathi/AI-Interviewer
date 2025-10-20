const HOST = "http://localhost:8000/"

const getCookie = (name) => {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

$(document).ready(() => {
    // Hide the container until data is loaded.
    $('#analysisContainer').hide(); 
    loadResults();
});

const loadResults = () => {
    const interviewId = getCookie('interviewId');
    
    // Interview id is not in local storage
    if (!interviewId) {
        $('#analysisContainer').html(`
            <p class="text-center text-danger">
                Error: Interview ID not found in storage. Please start an interview first.
            </p>
        `).show();
        return;
    }

    let url = `${HOST}candidate-interview/${interviewId}/` 
    
    // Show a loading indicator
    $('#analysisContainer').html(`
        <div class="text-center p-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Analyzing results...</p>
        </div>
    `).show();

    // fetch and display the interview analysis
    $.ajax({
        type: "GET",
        url: url,
        success: (response) => {
            // console.log("API Response:", response);
            displayAnalysis(response);
            $('#analysisContainer').show();
        },
        error: (xhr, status, error) => {
            console.error("API Error:", error);
            $('#analysisContainer').html(`
                <div class="alert alert-danger text-center">
                    Failed to load analysis for ID: ${interviewId}. Status: ${status}
                </div>
            `).show();
        }
    });
}


const displayAnalysis = (analysisArray) => {

    if (!analysisArray || analysisArray.length === 0) {
        $('#analysisContainer').html('<p class="text-center text-muted p-5 border rounded bg-white">No analysis data available for this interview.</p>');
        return;
    }

    let totalScore = 0;
    let container = '';
    
    // returns progress bar color based on score (0-10)
    const getScoreColorClass = (score) => {
        if (score >= 8) return 'bg-success';
        if (score >= 6) return 'bg-info';
        if (score >= 4) return 'bg-warning';
        return 'bg-danger';
    };

    analysisArray.forEach((item, index) => {
        const questionNum = index + 1;
        const analysis = item.analysis || {};
        const overall = parseFloat(analysis.overall || 0.0);
        let subScores = null;
        totalScore += overall;

        if (item.interview_type === "technical") {
            $("#interviewAnalysisHeading").text('Technical Interview Analysis Complete');
            subScores = [
                { label: 'Technical Depth', key: 'technical_depth' },
                { label: 'Communication Clarity', key: 'communication_clarity' },
                { label: 'Problem Solving', key: 'problem_solving' },
                { label: 'Job Relevance', key: 'job_relevance' },
            ];
        } else if (item.interview_type === "hr") {
            $("#interviewAnalysisHeading").text('HR Interview Analysis Complete');
            subScores = [
                { label: 'Communication Clarity', key: 'communication_clarity' },
                { label: 'Problem Solving Approach', key: 'problem_solving_approach' },
                { label: 'Teamwork Collaboration', key: 'teamwork_collaboration' },
                { label: 'Alignment with values', key: 'alignment_with_values' },
            ];
        }

        // Collect all sub-scores for iteration
        
        let scoreItemsHtml = '';
        subScores.forEach(scoreItem => {
            const score = parseFloat(analysis[scoreItem.key] || 0.0);
            const scorePercent = score * 10;
            const scoreColor = getScoreColorClass(score);

            // contains all four scores
            scoreItemsHtml += `
                <div class="score-item">
                    <div class="score-label">
                        <span class="text-muted">${scoreItem.label}</span>
                        <span class="fw-bold text-dark">${score.toFixed(1)}/10.0</span>
                    </div>
                    <div class="progress" role="progressbar" aria-label="${scoreItem.label} score" aria-valuenow="${scorePercent}" aria-valuemin="0" aria-valuemax="100">
                        <div class="progress-bar ${scoreColor}" style="width: ${scorePercent}%"></div>
                    </div>
                </div>
            `;
        });


        // analysis card for each question
        const cardHtml = `
            <div class="question-card">
                <div class="d-flex align-items-center question-header">
                    <i class="bi bi-patch-question-fill text-primary me-2 fs-4"></i>
                    <div class="question-title">Question ${questionNum}</div>
                </div>

                <div class="question-body mb-3 p-3 bg-light rounded">
                    <p class="mb-1 text-dark"><strong>Question:</strong> ${item.question}</p>
                    <p class="mb-0 text-secondary small"><strong>Your Answer:</strong> ${item.answer || 'No answer provided.'}</p>
                </div>

                <div class="score-section border-top pt-3">
                    ${scoreItemsHtml}
                </div>

                <div class="overall-score my-4 bg-primary text-white">
                    <div class="small fw-light mb-1">FINAL OVERALL SCORE</div>
                    <div class="overall-score-value">${overall.toFixed(1)}/10</div>
                </div>

                <div class="feedback-section">
                    <div class="feedback-title">
                        <i class="bi bi-lightbulb-fill me-1"></i> Detailed Feedback
                    </div>
                    <div class="feedback-text">
                        ${analysis.feedback || 'No feedback available.'}
                    </div>
                </div>
            </div>
        `;

        container += cardHtml;
    });

    // display the anaylsis container
    $('#analysisContainer').html(container).show();

    const averageScore = (totalScore / analysisArray.length).toFixed(1);
    $('#totalQuestions').text(analysisArray.length);
    $('#averageScore').text(averageScore);
}
