function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return 'Less than 1 minute'
    }
    const minutes = Math.floor(seconds / 60)
    return minutes === 1 ? minutes + ' ' + 'minute' : minutes + ' ' + 'minutes'
}

function updateTimeRemainingComponent(instanceName, timeRemaining) {
    const viewSiteButton = $("#" + instanceName + "-view-site");
    viewSiteButton.removeClass('hidden')

    const timeRemainingWrapper = $("#" + instanceName + "-time-remaining-wrapper");
    if (timeRemaining != null) {
        const timeRemainingSpan = $("#" + instanceName + "-time-remaining");
        timeRemainingSpan.text(formatTimeRemaining(timeRemaining));
        timeRemainingWrapper.removeClass('hidden');
    } else {
        viewSiteButton.addClass('hidden')
        timeRemainingWrapper.addClass('hidden');
    }
}

function updateStatus(instanceName, instanceStatus, timeRemaining) {
    const statusSpan = $("#" + instanceName + "-status");
    statusSpan.text(instanceStatus.charAt(0).toUpperCase() + instanceStatus.slice(1));
    statusSpan.removeClass();
    statusSpan.addClass(`status-${instanceStatus}`);

    updateTimeRemainingComponent(instanceName, timeRemaining)
}