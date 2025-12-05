
const HOST = "http://localhost:5000/"


let currentQuestion = null;
let totalQuestions = null;

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

let allAnalysis = [];

let interviewId = null;

const params = new URLSearchParams(window.location.search);
const candidate_interview_id = params.get('candidate_interview_id');
const interviewType = params.get('interview_type');

console.log('Candidate Interview ID:', candidate_interview_id);
console.log('Interview Type:', interviewType);

// Start interview when page loads
$(document).ready(function() {
    startInterviewSession();
});

function startInterviewSession() {
    
    if (!candidate_interview_id || !interviewType) {
        showAlert('Interview details not found. Please contact support.', 'danger');
        return;
    }

    
    // generate correct API url
    let url = `${HOST}start-interview/${candidate_interview_id}/`;
    
    $.ajax({
        url: url,
        type: 'POST',
        success: function(response) {
            console.log('Interview started:', response);

            if (response.error) {
                showAlert(`${response.errorDescription}`, 'danger');
                return;
            }
            
            interviewId = response.interview_id;
            totalQuestions = response.total_questions;
            currentQuestion = response.question_number;

            // Hide loading and processing, show question
            $('#loadingSection').hide();
            $('#processingMessage').hide();
            $('#questionSection').show();

            // Display first question
            displayQuestion(response.question);
            updateProgress();
        },
        error: function(error) {
            console.error(`Error starting ${interviewType} interview:`, error);
            showAlert(`Failed to start ${interviewType} interview. Please try again.`, 'danger');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 3000);
        }
    });
}

function displayQuestion(questionText) {
    $('#questionText').text(questionText);
}

function updateProgress() {
    $('#questionNumber').text(`Question ${currentQuestion} of ${totalQuestions}`);
    const progressPercent = (currentQuestion / totalQuestions) * 100;
    $('#progressBar').css('width', progressPercent + '%');
}

async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

// record user audio via browser
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = []; // to store chunks (parts) of audio input

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' }); // Audio type Binary Large Object (used to handle binary format of files)
            submitAnswer(audioBlob); // sends audio file to backend

            // Stop all tracks of audio input
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI
        $('#recordBtn').removeClass('start').addClass('stop'); // replace start icon with stop icon
        $('#recordBtn').html('<i class="bi bi-stop-circle-fill"></i> Stop Recording'); // change text to 'Stop Recording'
        $('#recordingIndicator').addClass('active'); // show recording icon

    } catch (error) {
        console.error('Error accessing microphone:', error);
        showAlert('Could not access microphone. Please grant permission.', 'danger');
    }
}

// stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // Update UI
        $('#recordBtn').prop('disabled', true); // record button not clickable since answer is analysing
        $('#recordingIndicator').removeClass('active'); // hide recording icon
        $('#processingMessage').show(); // display processing message
    }
}

// send audio blob to backend
function submitAnswer(audioBlob) {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'answer.wav'); // key, value (blob), filename
    formData.append('candidate_interview_id', candidate_interview_id);

    const urlWithQuery = `${HOST}submit-answer/${interviewId}`;

    $.ajax({
        url: urlWithQuery,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // console.log('Answer submitted:', response);

            if (response.message.includes('completed')) {
                // Redirect to interview completed page.
                // alert("Interview successfully completed");
                window.location.href = 'interview-completed.html';
            }

            else {
                // display next question
                currentQuestion = response.question_number;
                displayQuestion(response.question);
                updateProgress();

                // hide processing message
                $('#processingMessage').hide();

                // display Start Recording Button
                $('#recordBtn').prop('disabled', false);
                $('#recordBtn').removeClass('stop').addClass('start');
                $('#recordBtn').html('<i class="bi bi-mic-fill"></i> Start Recording');
            }
        },
        error: function(xhr, status, err) {
            console.error('Submission error:', xhr.responseText || err);
            showAlert('Failed to submit answer. Please try again.', 'danger');

            // hide processing message
            $('#processingMessage').hide();

            // display Start Recording Button
            $('#recordBtn').prop('disabled', false);
            $('#recordBtn').removeClass('stop').addClass('start');
            $('#recordBtn').html('<i class="bi bi-mic-fill"></i> Start Recording');
        }
    });
}

// function to display errors
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('#alertContainer').html(alertHtml);
}