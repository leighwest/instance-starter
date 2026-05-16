const appPollingIntervals = {};
const countdownIntervals = {};
const TOTAL_SECONDS = 250;

function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return 'Less than 1 minute';
    }
    const minutes = Math.floor(seconds / 60);
    return minutes === 1 ? '1 minute' : minutes + ' minutes';
}

function updateProgressBar(instanceName, secondsRemaining) {
    const fill = $("#" + instanceName + "-progress-fill");
    const percent = Math.min((secondsRemaining / TOTAL_SECONDS) * 100, 100);
    fill.css('width', Math.max(percent, 0) + '%');
}

function startCountdown(instanceName, initialSeconds) {
    if (countdownIntervals[instanceName]) {
        clearInterval(countdownIntervals[instanceName]);
    }

    let endTime = Date.now() + (initialSeconds * 1000);

    countdownIntervals[instanceName] = setInterval(function () {
        const secondsRemaining = Math.max((endTime - Date.now()) / 1000, 0);
        const timeRemainingSpan = $("#" + instanceName + "-time-remaining");
        timeRemainingSpan.text(formatTimeRemaining(secondsRemaining));
        updateProgressBar(instanceName, secondsRemaining);

        if (secondsRemaining <= 0) {
            clearInterval(countdownIntervals[instanceName]);
            delete countdownIntervals[instanceName];
        }
    }, 1000);
}

function stopCountdown(instanceName) {
    if (countdownIntervals[instanceName]) {
        clearInterval(countdownIntervals[instanceName]);
        delete countdownIntervals[instanceName];
    }
}

function updateTimeRemainingComponent(instanceName, timeRemaining) {
    const timeRemainingWrapper = $("#" + instanceName + "-time-remaining-wrapper");
    if (timeRemaining != null) {
        timeRemainingWrapper.removeClass('hidden');
        startCountdown(instanceName, timeRemaining);
    } else {
        timeRemainingWrapper.addClass('hidden');
        stopCountdown(instanceName);
        updateProgressBar(instanceName, 0);
    }
}

function setBadge(element, statusClass, text) {
    element.attr('class', 'badge ' + statusClass);
    element.html('<span class="badge-dot"></span>' + text);
}

function pollApplicationStatus(instanceName, publicIp, timeRemaining) {
    if (appPollingIntervals[instanceName]) return;

    const appStatusWrapper = $("#" + instanceName + "-app-status-wrapper");
    const appStatus = $("#" + instanceName + "-app-status");

    if (appStatus.text().trim() === 'Running') {
        updateTimeRemainingComponent(instanceName, timeRemaining);
        const viewSiteButton = $("#" + instanceName + "-view-site");
        viewSiteButton.attr('data-url', 'http://' + publicIp);
        viewSiteButton.removeClass('hidden');
        return;
    }

    appStatusWrapper.removeClass('hidden');
    setBadge(appStatus, 'status-pending', 'Checking...');

    appPollingIntervals[instanceName] = setInterval(function () {
        fetch('/check_health/?ip=' + publicIp)
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.healthy) {
                    setBadge(appStatus, 'status-running', 'Running');
                    clearInterval(appPollingIntervals[instanceName]);
                    delete appPollingIntervals[instanceName];

                    const viewSiteButton = $("#" + instanceName + "-view-site");
                    viewSiteButton.attr('data-url', 'http://' + publicIp);
                    viewSiteButton.removeClass('hidden');
                    updateTimeRemainingComponent(instanceName, timeRemaining);
                } else {
                    setBadge(appStatus, 'status-pending', 'Checking...');
                }
            })
            .catch(function () {
                setBadge(appStatus, 'status-pending', 'Checking...');
            });
    }, 2000);
}

function clearApplicationStatus(instanceName) {
    if (appPollingIntervals[instanceName]) {
        clearInterval(appPollingIntervals[instanceName]);
        delete appPollingIntervals[instanceName];
    }

    const appStatusWrapper = $("#" + instanceName + "-app-status-wrapper");
    const appStatus = $("#" + instanceName + "-app-status");
    setBadge(appStatus, 'status-pending', 'Checking...');
    appStatusWrapper.addClass('hidden');

    const viewSiteButton = $("#" + instanceName + "-view-site");
    viewSiteButton.attr('data-url', '');
    viewSiteButton.addClass('hidden');

    updateTimeRemainingComponent(instanceName, null);
}

function updateStatus(instanceName, instanceStatus, timeRemaining, publicIp) {
    const statusSpan = $("#" + instanceName + "-status");
    const statusText = instanceStatus === 'pending' ? 'Starting...' :
                       instanceStatus === 'stopping' ? 'Stopping...' :
                       instanceStatus.charAt(0).toUpperCase() + instanceStatus.slice(1);
    setBadge(statusSpan, 'badge ' + 'status-' + instanceStatus, statusText);

    if (instanceStatus === 'running' && publicIp) {
        pollApplicationStatus(instanceName, publicIp, timeRemaining);
    } else {
        clearApplicationStatus(instanceName);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.instance-item').forEach(function (el) {
        const instanceName = el.dataset.instanceName;
        const status = el.dataset.status;
        const publicIp = el.dataset.publicIp;
        const timeRemaining = el.dataset.timeRemaining ? parseFloat(el.dataset.timeRemaining) : null;

        if (status === 'running' && publicIp) {
            pollApplicationStatus(instanceName, publicIp, timeRemaining);
        }
    });
});