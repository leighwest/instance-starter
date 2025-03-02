(function () {
    function updateDisplay() {
        console.log("In updateDisplay timeRemainingSeconds is")
        console.log(timeRemainingSeconds)

        if (timeRemainingSeconds < 60) {
            timeRemaining.textContent = 'Less than 1 minute'
        } else {
            const minutes = Math.floor(timeRemainingSeconds / 60)
            timeRemaining.textContent = minutes === 1 ? minutes + ' ' + 'minute' : minutes + ' ' + 'minutes'
        }
    }

    updateDisplay();

    // Calculate the delay until the next whole minute:
    const initialDelay = (timeRemainingSeconds % 60) * 1000;

    setTimeout(function () {
        // Adjust seconds to the nearest lower minute:
        let timeRemainingMinutes = Math.floor(timeRemainingSeconds / 60) * 60;
        updateDisplay();

        const interval = setInterval(function () {
            timeRemainingMinutes -= 1;
            if (timeRemainingMinutes <= 0) {
                clearInterval(interval);
                timeRemaining.textContent = "Less than 1 minute";
            } else {
                updateDisplay();
            }
        }, 60000);
    }, initialDelay);
})();