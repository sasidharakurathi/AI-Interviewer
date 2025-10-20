
const HOST = "http://localhost:8000/"


const setCookie = (name, value, days) => {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000)); // days * hours * minutes * seconds * milliseconds
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

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

const deleteCookie = (name) => {
    document.cookie = name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}


let interviewId = null;

let currentQuestion = null;
let totalQuestions = null;

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

let allAnalysis = [];

// Start interview when page loads
$(document).ready(function() {
    startInterviewSession();
});

function startInterviewSession() {

    const selectedInterviewId = getCookie('selectedInterviewId');
    const interviewType = getCookie('interviewType');
    // console.log(selectedInterviewId);

    if (!selectedInterviewId || !interviewType) {
        showAlert('Interview details not found. Please select an interview from the home page.', 'danger');
        setTimeout(() => window.location.href = 'index.html', 3000);
        return;
    }

    
    // generate correct API url
    let url = '';
    if (interviewType === 'technical') {
        $("#interviewTypeHeading").text('Technical Interview');
        url = `${HOST}start-technical-interview/${selectedInterviewId}/`;
    } else if (interviewType === 'hr') {
        $("#interviewTypeHeading").text('HR Interview');
        url = `${HOST}start-hr-interview/${selectedInterviewId}/`;
    } else {
        showAlert('Invalid interview type.', 'danger');
        return;
    }

    $.ajax({
        url: url,
        type: 'POST',
        success: function(response) {
            // console.log('Interview started:', response);
            
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
    const selectedInterviewId = getCookie('selectedInterviewId');
    formData.append('audio_file', audioBlob, 'answer.wav'); // key, value (blob), filename

    const urlWithQuery = `${HOST}submit-answer/${interviewId}?selected_interview_id=${selectedInterviewId}`;

    $.ajax({
        url: urlWithQuery,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // console.log('Answer submitted:', response);

            if (response.message.includes('completed')) {
                // Set the final interviewId for the results page
                setCookie('interviewId', interviewId, 1);

                // Clean up selection cookies
                deleteCookie('selectedInterviewId');
                deleteCookie('interviewType');


                // Redirect to results page.
                setTimeout(() => {
                    window.location.href = 'results.html';
                }, 1000);
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
        error: function(error) {
            console.error('Error submitting answer:', error);
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

// helper function to display errors
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('#alertContainer').html(alertHtml);
}