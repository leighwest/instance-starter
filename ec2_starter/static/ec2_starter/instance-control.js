$(document).ready(function () {
    $('.start-instance').click(function () {
        const instanceName = $(this).data('instance-name');

        $.ajax({
            url: window.START_INSTANCE_URL,
            type: 'POST',
            data: {
                'instance_name': instanceName,
                'csrfmiddlewaretoken': window.CSRF_TOKEN
            },
            success: function (response) {
                if (!response.success) {
                    alert('Error: ' + response.error);
                }
            },
            error: function () {
                alert('An error occurred while trying to start the instance.');
            }
        });
    });
});