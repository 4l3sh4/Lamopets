document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll('.store');
    const navLinks = document.querySelectorAll('.nav-store a');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const activeLink = document.querySelector(`.nav-store a[href="#${entry.target.id}"]`);
                navLinks.forEach(link => link.classList.remove('active'));
                activeLink.classList.add('active');
            }
        });
    }, { rootMargin: '0px', threshold: 0.5 });

    sections.forEach(section => {
        observer.observe(section);
    });

    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            const targetId = this.getAttribute('href').substring(1); // Get the target id without the #
            const targetSection = document.getElementById(targetId);

            targetSection.scrollIntoView({ behavior: 'smooth' });

            sections.forEach(section => {
                if (section.id === targetId) {
                    section.style.display = 'inline-block';
                } else {
                    section.style.display = 'none';
                }
            });

            navLinks.forEach(link => link.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

function closeModalStore() {
    document.getElementById('purchase-store').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function () {
    const colorButtons = document.querySelectorAll('.colour-options');

    colorButtons.forEach(button => {
        button.addEventListener('click', function () {
            const filter = button.getAttribute('data-filter') || 'none';  
            const price = button.getAttribute('data-price');
            const itemId = button.getAttribute('data-item-id');
            const img = button.closest('.item').querySelector('img');
            const activePriceButton = button.closest('.item').querySelector('#active-price');

            console.log(`Applying filter: ${filter}`);
            console.log(`Updating price: ${price}`);
            console.log(`Updating item ID: ${itemId}`);

            img.style.filter = filter;

            activePriceButton.setAttribute('data-price', price);
            activePriceButton.setAttribute('data-item-id', itemId);
            activePriceButton.textContent = `$${price}`;
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.price');
    const popup = document.getElementById('purchase-store');
    const confirmText = document.getElementById('confirm-text-store');
    const yesButton = document.getElementById('yesButton');
    let activePriceButton;  // Declare a variable to store the active price button

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const itemPrice = button.getAttribute('data-price');
            confirmText.textContent = `Would you like to buy this item for $${itemPrice}?`;
            popup.style.display = 'block';
            activePriceButton = button;  // Store the clicked button in the variable
        });
    });

    yesButton.addEventListener('click', function() {
        if (!activePriceButton) return;

        // Retrieve itemId from the stored activePriceButton
        const itemId = activePriceButton.getAttribute('data-item-id');
        console.log("Active Price Button:", activePriceButton);
        console.log("Item ID:", itemId);
    
        fetch('/purchase_item/' + itemId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json().then(data => ({
            status: response.status,
            body: data
        })))
        .then(({status, body}) => {
            if (status === 200 && body.success) {
                closeModalStore();
                alert('Purchase Successful!');
                setTimeout(() => {
                    location.reload();
                }, 700);
            } else {
                console.error('Error:', body);
                alert(`Purchase Unsuccessful: ${body.error}`);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('An error occurred while making the purchase. Please try again.');
        });
    });

    function closeModalStore() {
        document.getElementById('purchase-store').style.display = 'none';
        if (activePriceButton) {
            activePriceButton.closest('.item').classList.remove('active');
        }
        activePriceButton = null;  // Reset the activePriceButton variable
    }
});
