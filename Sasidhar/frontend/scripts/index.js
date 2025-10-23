

const HOST = "http://localhost:5000/"

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



const fetch_all_interviews = () => {
    $.ajax({
        type: "GET",
        url: `${HOST}get-all-interviews/`,
        success: (response) => {
            // console.log(response);

            renderInterviews(response);

        },
        error: (error) => {
            console.error(error);
        }
    });
}

$(document).ready(() => {
    fetch_all_interviews();
});

// Sanitizes the data
const escapeHtml = (unsafe) => {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// slices the text to maximum of 180 characters.
const snippet = (text, maxLen = 180) => {
    if (!text) return '';
    const cleaned = text.replace(/\s+/g, ' ').trim();
    if (cleaned.length <= maxLen) return cleaned;
    return cleaned.substring(0, maxLen).trim() + '…';
}

const renderInterviews = (list) => {
    // Remove existing list if present
    $('#interviewsList').remove();

    const container = $('<div id="interviewsList" class="mt-4"></div>');

    if (!Array.isArray(list) || list.length === 0) {
        container.append('<p class="text-muted">No interviews available at the moment.</p>');
        $('.main-card').append(container);
        return;
    }

    // display all the available interviews
    list.forEach(item => {
        const card = $('<div class="card mb-3"></div>');
        const cardBody = $('<div class="card-body"></div>');

        const title = $('<h5 class="card-title"></h5>').text(item.job_role || 'Untitled Role');
        const desc = $('<p class="card-text text-muted"></p>').text(snippet(item.job_description || 'No description'));
        const totalQuestions = $('<p class="mb-2"></p>').html('<strong>Questions:</strong> ' + (item.max_questions || '-'));

        const technicalBtn = $(`<button class="btn btn-primary start-btn" data-id="${escapeHtml(item.id)}" data-type="technical"><i class="bi bi-play-circle"></i> Start Technical Interview</button>`);
        const hrBtn = $(`<button class="btn btn-primary start-btn" data-id="${escapeHtml(item.id)}" data-type="hr"><i class="bi bi-play-circle"></i> Start HR Interview</button>`);

        const btnDiv = $(`
            <div class="d-flex gap-3 mt-3">
                ${technicalBtn.prop('outerHTML')}
                ${hrBtn.prop('outerHTML')}
            </div>
        `);

        cardBody.append(title, desc, totalQuestions, btnDiv);
        card.append(cardBody);
        container.append(card);
    });

    $('.main-card').append(container);


    $(".start-btn").click((event) => { 
        event.preventDefault();
        const selectedInterviewId = $(event.currentTarget).data('id');
        const interviewType = $(event.currentTarget).data('type');

        // Store selected interview details in cookies for 1 day
        setCookie('selectedInterviewId', selectedInterviewId, 1);
        setCookie('interviewType', interviewType, 1);

        window.location.href = `interview.html`; // redirect to interview page
    });
}