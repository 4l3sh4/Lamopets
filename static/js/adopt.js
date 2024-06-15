
document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll('.adopt');
    const navLinks = document.querySelectorAll('.nav-adopt a');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const activeLink = document.querySelector(`.nav-adopt a[href="#${entry.target.id}"]`);
                navLinks.forEach(link => link.classList.remove('active'));
                activeLink.classList.add('active');
            }
        });
    }, { rootMargin: '0px', threshold: 0.5 });

    sections.forEach(section => {
        observer.observe(section);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.price-adopt');

    const purchasePopup = document.getElementById('purchase-adopt');
    const confirmText = document.getElementById('confirm-text-adopt');
    const purchaseEggImg = document.getElementById('purchase-egg-img');
    const yesButton = document.getElementById('yesButton');

    const namePopup = document.getElementById('name-adopt');
    const confirmNameButton = document.getElementById('confirmNameButton');
    const petNameInput = document.getElementById('pet-name-input');
    const nameEggImg = document.getElementById('name-egg-img');

    const successPopup = document.getElementById('success-adopt');
    const successMessage = document.getElementById('success-message-adopt');
    const successPetImg = document.getElementById('success-pet-img');
    const yayButton = document.getElementById('yayButton');
    
    let selectedPetSpecies;

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const petName = button.getAttribute('data-name');
            const petPrice = button.getAttribute('data-price');
            const petImage = button.getAttribute('data-pet-img');
            const petElement = button.closest('.item');
            const eggImgUrl = petElement.querySelector('img').src;

            confirmText.textContent = `Would you like to buy ${petName} for ${petPrice} Lamocoins?`;
            purchaseEggImg.src = eggImgUrl;
            purchasePopup.style.display = 'block';

            document.querySelectorAll('.item.active').forEach(item => item.classList.remove('active'));
            petElement.classList.add('active');

            selectedPetSpecies = petElement.id;
            selectedPetImage = petImage; 
        });
    });

    yesButton.addEventListener('click', function() {
        purchasePopup.style.display = 'none';
        namePopup.style.display = 'block';

        const activePetElement = document.querySelector('.item.active');
        const eggImgUrl = activePetElement.querySelector('img').src;
        nameEggImg.src = eggImgUrl;
    });

    confirmNameButton.addEventListener('click', async () => {
        const petName = petNameInput.value.trim();

        if (petName.length < 4 || petName.length > 20) {
            alert('Pet name must be between 4 and 20 characters.');
            return;
        }

        try {
            const response = await fetch(`/adopt_pet/${selectedPetSpecies}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pet_name: petName })
            });

            if (response.ok) {
                closeModalAdopt();
                successMessage.textContent = `You have successfully adopted ${petName}!`;
                successPetImg.src = selectedPetImage;
                successPopup.style.display = 'block';
            } else {
                alert('Adoption Unsuccessful');
            }
        } catch (error) {
            console.error('Fetch error:', error);
        }
    });

    yayButton.addEventListener('click', () => {
        successPopup.style.display = 'none';
        location.reload(); 
    });

    function closeModalAdopt() {
        purchasePopup.style.display = 'none';
        namePopup.style.display = 'none';
        document.querySelectorAll('.item.active').forEach(item => item.classList.remove('active'));
    }
});

function closeModalAdopt() {
    document.getElementById('purchase-adopt').style.display = 'none';
    document.getElementById('name-adopt').style.display = 'none';
    document.querySelector('.item.active').classList.remove('active');
}
