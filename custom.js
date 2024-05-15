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
