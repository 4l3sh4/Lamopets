document.getElementById('saveButton').addEventListener('click', function() {
    var avatarParts = ['gender', 'eyes', 'mouth', 'misc', 'pants', 'shirt', 'hair', 'shoes'];
    var avatarContainer = document.getElementById('avatar');

    // Create a main canvas
    var mainCanvas = document.createElement('canvas');
    mainCanvas.width = avatarContainer.offsetWidth;
    mainCanvas.height = avatarContainer.offsetHeight;
    var mainContext = mainCanvas.getContext('2d');

    // Function to load image
    function loadImage(partElement) {
        return new Promise((resolve, reject) => {
            var img = new Image();
            img.crossOrigin = "Anonymous";
            img.src = partElement.style.backgroundImage.slice(5, -2); // Extract URL from backgroundImage style
            img.onload = function() {
                resolve(img);
            };
            img.onerror = reject;
        });
    }

    // Function to draw image
    function drawImage(partElement, img) {
        var partCanvas = document.createElement('canvas');
        partCanvas.width = partElement.offsetWidth;
        partCanvas.height = partElement.offsetHeight;
        var partContext = partCanvas.getContext('2d');

        // Apply the filter and draw the image
        partContext.filter = window.getComputedStyle(partElement).getPropertyValue('filter');
        partContext.drawImage(img, 0, 0, partElement.offsetWidth, partElement.offsetHeight);

        // Draw the part canvas onto the main canvas
        mainContext.drawImage(partCanvas, partElement.offsetLeft, partElement.offsetTop);
    }

    // Load all images
    var promises = avatarParts.map(part => {
        var partElement = document.getElementById(part);
        if (partElement.style.backgroundImage) {
            return loadImage(partElement).then(img => ({ partElement, img }));
        } else {
            return Promise.resolve(null);
        }
    });

    // Draw all images in order
    Promise.all(promises).then(results => {
        results.forEach(result => {
            if (result) {
                drawImage(result.partElement, result.img);
            }
        });
        var imgData = mainCanvas.toDataURL('image/png');
        saveAvatar(imgData);
    }).catch(error => {
        console.error('Error capturing avatar:', error);
        alert('Error capturing avatar: ' + error);
    });
});

function saveAvatar(imgData) {
    var requiredParts = ['gender', 'eyes', 'mouth', 'shirt', 'pants', 'hair'];
    var missingParts = [];
    
    requiredParts.forEach(part => {
        var partElement = document.getElementById(part);
        if (partElement.style.backgroundImage === '') {
            missingParts.push(part);
        }
    });

    if (missingParts.length > 0) {
        var missingPartsMessage = "Please select " + missingParts.join(", ") + " before saving :)" ;
        alert(missingPartsMessage);
        return;
    }

    fetch('/save-avatar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imgData }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to save avatar'); });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Avatar saved successfully!');
        } else {
            alert('Failed to save avatar: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving avatar:', error);
        alert('Error saving avatar: ' + error);
    });
}

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

function changeGender(gender) {
    selectedGender = gender;
    console.log('Selected gender:', gender);
    var genderImageUrl = "{{ url_for('static', filename='assets/customization_assets/gender/') }}" + gender + ".png";
    updateAvatarPart('gender', genderImageUrl);
    resetCustomItems(); 
    setDefaultClothing();
    filterOptions();
}

function resetCustomItems() {
    var customParts = ['eyes', 'mouth', 'misc', 'pants', 'shirt', 'hair', 'shoes'];
    customParts.forEach(part => {
        if (part !== 'gender') {
            var partElement = document.getElementById(part);
            partElement.style.backgroundImage = '';
            partElement.style.filter = '';
        }
    });
}

document.querySelectorAll('#genderType .option').forEach(button => {
    button.addEventListener('click', function() {
        changeGender(button.getAttribute('data-gender'));
    });
});

document.querySelectorAll('.options .option').forEach(button => {
    button.addEventListener('click', function() {
        // Check if gender has been selected
        if (!selectedGender) {
            alert('Please select a gender first!');
            return;
        }

        var part = this.getAttribute('data-part');
        var imageUrl = this.getAttribute('data-image');
        console.log('Part:', part, 'Image URL:', imageUrl);
        updateAvatarPart(part, imageUrl);

        this.querySelectorAll('.color-btn').forEach(colorButton => {
            colorButton.setAttribute('data-part', part);
        });

        const defaultColorButton = this.querySelector('.default-color');
        if (defaultColorButton) {
            defaultColorButton.click();
        }
    });
});

document.querySelectorAll('#miscType .option').forEach(button => {
    button.addEventListener('click', function() {
        var part = this.getAttribute('data-part');
        var imageUrl = this.getAttribute('data-image');
        console.log('Part:', part, 'Image URL:', imageUrl);
        
        if (part === 'misc') {
            var miscElement = document.getElementById('misc');
            miscElement.style.backgroundImage = '';
            miscElement.style.filter = '';
        } else {
            updateAvatarPart(part, imageUrl);
        }

        this.querySelectorAll('.color-btn').forEach(colorButton => {
            colorButton.setAttribute('data-part', part);
        });

        const defaultColorButton = this.querySelector('.default-color');
        if (defaultColorButton) {
            defaultColorButton.click();
        }
    });
});

document.querySelectorAll('.color-btn').forEach(button => {
    button.addEventListener('click', function(event) {
        event.stopPropagation();
        var part = this.getAttribute('data-part'); 
        var filter = this.getAttribute('data-filter');
        console.log('Changing color for part:', part, 'with filter:', filter);
        
        var option = this.closest('.option');
        if (option) {
            var imageUrl = option.getAttribute('data-image');
            console.log('Updating part:', part, 'with image URL:', imageUrl);
            
            updateAvatarPart(part, imageUrl);
            changeColor(part, filter);
        } else {
            console.error('Parent option not found for color button:', this);
        }
    });
});

function changeColor(partId, filter) {
    var partElement = document.getElementById(partId);
    partElement.style.filter = filter;
}

function setDefaultClothing() {
    console.log('Setting default clothing for gender:', selectedGender);
    if (selectedGender === 'Male') {
        console.log('Default Male clothing URLs:', defaultMaleShirtUrl, defaultMalePantsUrl);
        updateAvatarPart('shirt', defaultMaleShirtUrl);
        updateAvatarPart('pants', defaultMalePantsUrl);
    } else if (selectedGender === 'Female') {
        console.log('Default Female clothing URLs:', defaultFemaleShirtUrl, defaultFemalePantsUrl);
        updateAvatarPart('shirt', defaultFemaleShirtUrl);
        updateAvatarPart('pants', defaultFemalePantsUrl);
    }
}