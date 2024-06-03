
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
    const popup = document.getElementById('purchase-adopt');
    const confirmText = document.getElementById('confirm-text-adopt');
    const yesButton = document.getElementById('yesButton');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const petName = button.getAttribute('data-name');
            const petPrice = button.getAttribute('data-price');
            confirmText.textContent = `Would you like to buy ${petName} for $${petPrice}?`;
            popup.style.display = 'block';

            const petElement = button.closest('.item');
            document.querySelectorAll('.item.active').forEach(item => item.classList.remove('active'));
            petElement.classList.add('active');

            document.querySelector('#pet-id').value = petElement.id;
        });
    });

    const initialPetElement = document.querySelector('.item.active');
    if (initialPetElement) {
        initialPetElement.classList.add('active');
    }

    yesButton.addEventListener('click', function() {
        const petSpecies = document.querySelector('.item.active').id;

        fetch('/adopt_pet/' + petSpecies, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                closeModalAdopt();
                alert('Adoption Successful!');
                setTimeout(() => {
                    location.reload();
                }, 500);

            } else {
                alert('Adoption Unsuccessful');
            }
        })
        .catch(error => {
            console.error(error);
        });
    });

});

function closeModalAdopt() {
    document.getElementById('purchase-adopt').style.display = 'none';
    document.querySelector('.item.active').classList.remove('active');
}
