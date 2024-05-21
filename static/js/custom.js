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
    console.log('Updating part:', partId, 'with image URL:', imageUrl);
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
        console.log('Selected gender:', selectedGender);
        var genderImageUrl = "{{ url_for('static', filename='assets/customization_assets/gender/') }}" + selectedGender + ".png";
        updateAvatarPart('gender', genderImageUrl);
        setDefaultClothing();
        filterOptions();
    });
});

document.querySelectorAll('.options .option').forEach(button => {
    button.addEventListener('click', function() {
        var part = button.getAttribute('data-part');
        var imageUrl = button.getAttribute('data-image');
        console.log('Part:', part, 'Image URL:', imageUrl);
        updateAvatarPart(part, imageUrl);
    });
});

document.querySelectorAll('.color-btn').forEach(button => {
    button.addEventListener('click', function(event) {
        event.stopPropagation();
        var part = button.getAttribute('data-part');
        var filter = button.getAttribute('data-filter');
        console.log('Changing color for part:', part, 'with filter:', filter);
        changeColor(part, filter);
    });
});

function changeColor(partId, filter) {
    var partElement = document.getElementById(partId);
    partElement.style.filter = filter;
}

function setDefaultClothing() {
    console.log('Setting default clothing for gender:', selectedGender);
    if (selectedGender === 'male') {
        console.log('Default male clothing URLs:', defaultMaleShirtUrl, defaultMalePantsUrl);
        updateAvatarPart('shirt', defaultMaleShirtUrl);
        updateAvatarPart('pants', defaultMalePantsUrl);
    } else if (selectedGender === 'female') {
        console.log('Default female clothing URLs:', defaultFemaleShirtUrl, defaultFemalePantsUrl);
        updateAvatarPart('shirt', defaultFemaleShirtUrl);
        updateAvatarPart('pants', defaultFemalePantsUrl);
    }
}
