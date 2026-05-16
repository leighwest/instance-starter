const appPollingIntervals = {};

function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return 'Less than 1 minute';
    }
    const minutes = Math.floor(seconds / 60);
    return minutes === 1 ? '1 minute' : minutes + ' minutes';
}

function updateTimeRemainingComponent(instanceName, timeRemaining) {
    const timeRemainingWrapper = $("#" + instanceName + "-time-remaining-wrapper");
    if (timeRemaining != null) {
        const timeRemainingSpan = $("#" + instanceName + "-time-remaining");
        timeRemainingSpan.text(formatTimeRemaining(timeRemaining));
        timeRemainingWrapper.removeClass('hidden');
    } else {
        timeRemainingWrapper.addClass('hidden');
    }
}

function pollApplicationStatus(instanceName, publicIp, timeRemaining) {
    if (appPollingIntervals[instanceName]) return;

    const appStatusWrapper = $("#" + instanceName + "-app-status-wrapper");
    const appStatus = $("#" + instanceName + "-app-status");

    if (appStatus.text().trim() === 'Running') {
        appStatus.attr('class', 'status-running');
        updateTimeRemainingComponent(instanceName, timeRemaining);
        return;
    }

    appStatusWrapper.removeClass('hidden');
    appStatus.text('Checking...');
    appStatus.attr('class', 'status-pending');

    appPollingIntervals[instanceName] = setInterval(function () {
        fetch('/check_health/?ip=' + publicIp)
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.healthy) {
                    appStatus.text('Running');
                    appStatus.attr('class', 'status-running');
                    clearInterval(appPollingIntervals[instanceName]);
                    delete appPollingIntervals[instanceName];

                    const viewSiteButton = $("#" + instanceName + "-view-site");
                    viewSiteButton.attr('data-url', 'http://' + publicIp);
                    viewSiteButton.removeClass('hidden');
                    updateTimeRemainingComponent(instanceName, timeRemaining);
                } else {
                    appStatus.text('Checking...');
                }
            })
            .catch(function () {
                appStatus.text('Checking...');
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
    appStatus.text('Checking...');
    appStatus.attr('class', 'status-pending');
    appStatusWrapper.addClass('hidden');

    const viewSiteButton = $("#" + instanceName + "-view-site");
    viewSiteButton.attr('data-url', '');
    viewSiteButton.addClass('hidden');

    updateTimeRemainingComponent(instanceName, null);
}

function updateStatus(instanceName, instanceStatus, timeRemaining, publicIp) {
    const statusSpan = $("#" + instanceName + "-status");
    statusSpan.text(instanceStatus.charAt(0).toUpperCase() + instanceStatus.slice(1));
    statusSpan.removeClass();
    statusSpan.addClass('status-' + instanceStatus);

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