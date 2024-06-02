function changeBackgroundColor(color) {
    const background = document.getElementById('background');
    background.style.backgroundColor = color;
}

function changePet(petImageUrl) {
    // Get all pet images
    const petImages = document.getElementsByClassName('pet');

    // Reset display property of all pet images to "none"
    for (let i = 0; i < petImages.length; i++) {
        petImages[i].style.display = 'none';
    }

    // Update URL and set display property of clicked pet image to "block"
    const petImage = document.getElementById('pet');
    petImage.src = petImageUrl;
    petImage.style.display = 'block';
}

function hidePet() {
    const petElement = document.getElementById('pet');
    petElement.style.display = 'none';
}

function saveCanvas() {
    const background = document.getElementById('background');
    const backgroundColor = getComputedStyle(background).backgroundColor;

    // Check if the background color is chosen
    if (backgroundColor !== 'rgba(0, 0, 0, 0)') { // Transparent background
        // Proceed with saving canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const photobooth = document.getElementById('photobooth');
        const avatar = document.getElementById('avatar');
        const pet = document.getElementById('pet');

        const photoboothWidth = photobooth.offsetWidth;
        const photoboothHeight = photobooth.offsetHeight;

        canvas.width = photoboothWidth;
        canvas.height = photoboothHeight;

        // Draw the background color
        context.fillStyle = backgroundColor;
        context.fillRect(0, 0, photoboothWidth, photoboothHeight);

        // Calculate the center position for the avatar
        const avatarX = (photoboothWidth - avatar.width) / 2;
        const avatarY = (photoboothHeight - avatar.height) / 2;

        // Draw the avatar image
        context.drawImage(avatar, avatarX, avatarY, avatar.width, avatar.height);

        // Draw the pet image if it exists
        if (pet && pet.src) {
            const petX = (photoboothWidth - pet.width); 
            const petY = (photoboothHeight - pet.height) - 2;
            context.drawImage(pet, petX, petY, pet.width, pet.height);
        }

        // Convert canvas to image and trigger download
        const image = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = image;
        link.download = 'photobooth.png';
        link.click();
    } else {
        // Show warning message
        alert('Please choose a background color before saving!');
    }
}



window.onload = function() {
    const avatar = document.getElementById('avatar');
    const photobooth = document.getElementById('photobooth');
    const background = document.getElementById('background');

    const avatarWidth = avatar.clientWidth;
    const avatarHeight = avatar.clientHeight;

    photobooth.style.width = avatarWidth + 'px';
    photobooth.style.height = avatarHeight + 'px';
    background.style.width = avatarWidth + 'px';
    background.style.height = avatarHeight + 'px';

    // Adjust the position of the background to match the avatar
    background.style.top = avatar.offsetTop + 'px';
    background.style.left = avatar.offsetLeft + 'px';
};