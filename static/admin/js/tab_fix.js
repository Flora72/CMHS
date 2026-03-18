document.addEventListener("DOMContentLoaded", function() {
    const tabs = document.querySelectorAll('.nav-tabs a');
    tabs.forEach(tab => {
        tab.addEventListener('click', function (e) {
            $(this).tab('show');
        });
    });
});