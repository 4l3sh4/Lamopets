function openNav() {
    document.getElementById("sidenav").style.width = "250px";
    document.getElementById("content").style.transform = "translateX(250px)";
    document.getElementById("share-buttons").style.transform = "translateX(250px)";
    document.querySelector(".logo").style.transform = "translateX(250px)";
    document.querySelector(".currency-position").style.transform = "translateX(250px)";
    document.getElementById("navicon").style.display = "none"; 
}

function closeNav() {
    document.getElementById("sidenav").style.width = "0";
    document.getElementById("content").style.transform = "translateX(0)";
    document.getElementById("share-buttons").style.transform = "translateX(0)";
    document.querySelector(".logo").style.transform = "translateX(0)";
    document.querySelector(".currency-position").style.transform = "translateX(0px)";
    document.getElementById("navicon").style.display = "block"; 
}

window.addEventListener('resize', function() {
    if (window.innerWidth > 900) {
        closeNav(); 
        document.getElementById("navicon").style.display = "none"; 
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth < 900) {
        document.getElementById("navicon").style.display = "block"; 
    }
});
