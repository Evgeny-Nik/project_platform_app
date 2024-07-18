document.addEventListener('DOMContentLoaded', function () {
    var image_repositorySelect = document.getElementById('image_repository');
    var image_tagSelect = document.getElementById('image_tag');

    image_repositorySelect.addEventListener('change', function () {
        var image_repoName = image_repositorySelect.value;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/docker-images/' + image_repoName + '/tags', true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                update_image_TagsDropdown(data[image_repoName]);
            } else {
                console.error('Request failed.  Returned status of ' + xhr.status);
            }
        };
        xhr.send();
    });

    function update_image_TagsDropdown(image_tags) {
        image_tagSelect.innerHTML = ''; // Clear current options
        image_tags.forEach(function (image_tag) {
            var option = document.createElement('option');
            option.value = image_tag;
            option.textContent = image_tag;
            image_tagSelect.appendChild(option);
        });
    }
});

// Function to format age into human-readable format
function formatAge(iso8601Age) {
    var now = new Date();
    var ageDate = new Date(iso8601Age);
    var diff = now - ageDate;

    var seconds = Math.floor(diff / 1000);
    var minutes = Math.floor(seconds / 60);
    var hours = Math.floor(minutes / 60);
    var days = Math.floor(hours / 24);

    var formattedAge = "";
    if (days > 0) {
        formattedAge += days + " days ";
    }
    if (hours > 0) {
        formattedAge += (hours % 24) + " hours ";
    }
    if (minutes > 0) {
        formattedAge += (minutes % 60) + " minutes";
    }
    if (formattedAge === "") {
        formattedAge = "Just now";
    }
    return formattedAge;
}

// Wait for document to load
document.addEventListener("DOMContentLoaded", function() {
    // Iterate over each age cell and update the content
    var ageCells = document.querySelectorAll(".age");
    ageCells.forEach(function(cell) {
        var originalAge = cell.textContent.trim();
        var formattedAge = formatAge(originalAge);
        cell.textContent = formattedAge;
    });
});
