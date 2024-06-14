document.addEventListener('DOMContentLoaded', function () {

    var tab = document.getElementById("setting-tab");
    tab.addEventListener("click", openPopup);

    const popupOverlay = document.getElementById('popupOverlay');

    const popup = document.getElementById('popup-settings');

    const closePopup = document.getElementById('closePopup');

    const emailInput = document.getElementById('emailInput');

    // Function to open the popup

    function openPopup() {

        popupOverlay.style.display = 'block';

    }

    // Function to close the popup

    function closePopupFunc() {

        popupOverlay.style.display = 'none';

    }
    // Event listeners

    // Close the popup when the close button is clicked

    closePopup.addEventListener('click', closePopupFunc);

    // Close the popup when clicking outside the popup content

    popupOverlay.addEventListener('click', function (event) {

        if (event.target === popupOverlay) {

            closePopupFunc();

        }

    });

    // You can customize and expand these functions based on your specific requirements.

});