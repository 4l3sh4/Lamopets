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
    }, { rootMargin: '0px', threshold: 0.1 });

    sections.forEach(section => {
        observer.observe(section);
    });
});

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

function closeModalStore() {
    document.getElementById('purchase-store').style.display = 'none';
    document.querySelector('.item.active').classList.remove('active');
}

