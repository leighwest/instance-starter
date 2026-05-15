function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return 'Less than 1 minute'
    }
    const minutes = Math.floor(seconds / 60)
    return minutes === 1 ? minutes + ' ' + 'minute' : minutes + ' ' + 'minutes'
}

function updateTimeRemainingComponent(instanceName, timeRemaining, instanceStatus) {
    const timeRemainingWrapper = $("#" + instanceName + "-time-remaining-wrapper");
    if (timeRemaining != null && instanceStatus === 'running') {
        const timeRemainingSpan = $("#" + instanceName + "-time-remaining");
        timeRemainingSpan.text(formatTimeRemaining(timeRemaining));
        timeRemainingWrapper.removeClass('hidden');
    } else {
        timeRemainingWrapper.addClass('hidden');
    }
}

function updateStatus(instanceName, instanceStatus, timeRemaining, publicIp) {
    const statusSpan = $("#" + instanceName + "-status");
    statusSpan.text(instanceStatus.charAt(0).toUpperCase() + instanceStatus.slice(1));
    statusSpan.removeClass();
    statusSpan.addClass(`status-${instanceStatus}`);

    const viewSiteButton = $("#" + instanceName + "-view-site");
    if (publicIp) {
        viewSiteButton.attr('data-url', 'http://' + publicIp);
        viewSiteButton.removeClass('hidden');
    } else {
        viewSiteButton.attr('data-url', '');
        viewSiteButton.addClass('hidden');
    }

    updateTimeRemainingComponent(instanceName, timeRemaining, instanceStatus);
}