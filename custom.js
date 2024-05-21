// Function to save avatar as PNG
document.getElementById('saveButton').addEventListener('click', function() {
    html2canvas(document.getElementById('avatar'), {
        onrendered: function(canvas) {
            var link = document.createElement('a');
            link.href = canvas.toDataURL('image/png');
            link.download = 'avatar.png';
            link.click();
        }
    });
});

var selectedGender = '';

function filterOptions() {
    var gender = selectedGender;
    var parts = ['hair', 'shirt', 'pants', 'misc', 'shoes', 'eyes', 'mouth'];
    
    parts.forEach(part => {
        var options = document.querySelectorAll(`#${part}Type .option`);
        options.forEach(option => {
            var optionGender = option.getAttribute('data-gender');
            if (optionGender === gender || optionGender === 'unisex') {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });
    });
}

function updateAvatarPart(partId, imageUrl) {
    var partElement = document.getElementById(partId);
    partElement.style.backgroundImage = "url('" + imageUrl + "')";
    resetFilter(partId);
}

function resetFilter(partId) {
    var partElement = document.getElementById(partId);
    partElement.style.filter = '';
}

document.querySelectorAll('#genderType .option').forEach(button => {
    button.addEventListener('click', function() {
        selectedGender = button.getAttribute('data-gender');
        updateAvatarPart('gender', 'customization_assets/gender/' + selectedGender + '.png');
        filterOptions();
    });
});

document.querySelectorAll('.options .option').forEach(button => {
    button.addEventListener('click', function() {
        var part = button.getAttribute('data-part');
        var imageUrl = button.getAttribute('data-image');
        updateAvatarPart(part, imageUrl);
    });
});

document.querySelectorAll('.color-btn').forEach(button => {
    button.addEventListener('click', function(event) {
        event.stopPropagation();
        var part = button.getAttribute('data-part');
        var filter = button.getAttribute('data-filter');
        changeColor(part, filter);
    });
});

function changeColor(partId, filter) {
    var partElement = document.getElementById(partId);
    partElement.style.filter = filter;
}
