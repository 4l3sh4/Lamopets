function openNav() {
    document.getElementById("sidenav").style.width = "250px";
    document.getElementById("content").style.transform = "translateX(250px)";
    document.querySelector(".logo").style.transform = "translateX(250px)";
    document.getElementById("navicon").style.display = "none"; 
}

function closeNav() {
    document.getElementById("sidenav").style.width = "0";
    document.getElementById("content").style.transform = "translateX(0)";
    document.querySelector(".logo").style.transform = "translateX(0)";
    document.getElementById("navicon").style.display = "block"; 
}

window.addEventListener('resize', function() {
    if (window.innerWidth > 600) {
        closeNav(); 
        document.getElementById("navicon").style.display = "none"; 
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth < 600) {
        document.getElementById("navicon").style.display = "block"; 
    }
});

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

document.addEventListener("DOMContentLoaded", function() {
    const colourButtons = document.querySelectorAll('.colour-options');
    const item = document.getElementById('head1');
    colourButtons.forEach(button => {
        button.addEventListener('click', function() {
            const colour = this.getAttribute('data-filter');
            switch(colour) {
                case 'black':
                    item.style.filter = 'grayscale(50%) brightness(40%) saturate(400%)';
                    break;
                case 'blue':
                    item.style.filter = 'saturate(150%) sepia(70%) hue-rotate(180deg)';
                    break;
                case 'green':
                    item.style.filter = 'saturate(200%) sepia(50%) hue-rotate(90deg)';
                    break;
            }
        });
    });
}); 

document.addEventListener('DOMContentLoaded', function() {
    var priceButtons = document.querySelectorAll('.price');
    var popup = document.getElementById('purchase-popup');

    priceButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            popup.style.display = 'block';
        });
    });

    window.onclick = function(event) {
        if (event.target == popup) {
            popup.style.display = "none";
        }
    }

    document.getElementById('noButton').addEventListener('click', function() {
        popup.style.display = 'none';
    });
});
