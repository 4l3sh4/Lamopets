function toggleSanctuary() {
    var sanctuary = document.getElementById("sanctuary");
    var closet = document.getElementById("closet");
    var backButton = document.querySelector(".back-button");
    var deleteButton = document.querySelector(".delete-button");
    var petsButton = document.querySelector("#pets-button"); 
    var closetButton = document.querySelector("#wardrobe-button"); 

    sanctuary.style.display = "block";
    closet.style.display = "none";
    
    var profileDisplay = document.getElementById("profile-display");
    profileDisplay.style.flexDirection = "column";
    profileDisplay.style.justifyContent = "flex-start";
    sanctuary.style.flexDirection = "column";

    backButton.style.display = "block";
    deleteButton.style.display = "block";
    petsButton.style.display = "none";
    closetButton.style.display = "none";
}

function toggleCloset() {
    var sanctuary = document.getElementById("sanctuary");
    var closet = document.getElementById("closet");
    var backButton = document.querySelector(".back-button"); 
    var deleteButton = document.querySelector(".delete-button"); 
    var petsButton = document.querySelector("#pets-button"); 
    var closetButton = document.querySelector("#wardrobe-button"); 

    sanctuary.style.display = "none";
    closet.style.display = "block";

    var profileDisplay = document.getElementById("profile-display");
    profileDisplay.style.flexDirection = "column";
    profileDisplay.style.justifyContent = "flex-start";
    closet.style.flexDirection = "column";

    backButton.style.display = "block";
    deleteButton.style.display = "block";
    petsButton.style.display = "none";
    closetButton.style.display = "none";
}

function goBack() {
    var sanctuary = document.getElementById("sanctuary");
    var closet = document.getElementById("closet");
    var backButton = document.querySelector(".back-button");
    var deleteButton = document.querySelector(".delete-button"); 
    var petsButton = document.querySelector("#pets-button"); 
    var closetButton = document.querySelector("#wardrobe-button"); 

    sanctuary.style.display = "none";
    closet.style.display = "none";

    var profileDisplay = document.getElementById("profile-display");
    profileDisplay.style.justifyContent = "center";
    profileDisplay.style.flexDirection = "row";

    backButton.style.display = "none";
    deleteButton.style.display = "none";
    petsButton.style.display = "inline";
    closetButton.style.display = "inline";
}

function displayDelete() {
    var deleteButtons = document.querySelectorAll(".delete-item-button");
    if (deleteButtons.length > 0) {
        var currentDisplay = deleteButtons[0].style.display;
        var newDisplay = (currentDisplay === "none" || currentDisplay === "") ? "block" : "none";
        deleteButtons.forEach(button => {
            button.style.display = newDisplay;
        });
    }
}

document.addEventListener("DOMContentLoaded", function() {
    var modal = document.getElementById("release-pet");
    var confirmButton = document.getElementById("yesButton");
    var closeButton = document.getElementById("noButton");
    var clickCount = 0;
    var adoptIdGlobal;
    var deduct_price;

    function showReleasePopup(adoptName, petImage, adoptId, price) {
        document.getElementById("confirm-text-pet").innerText = `Would you like to release ${adoptName}?`;
        document.getElementById("release-pet-img").src = petImage;
        deduct_price = price / 2;
        clickCount = 0; 
        adoptIdGlobal = adoptId; 

        confirmButton.onclick = function() {
            if (clickCount === 0) {
                document.getElementById("confirm-text-pet").innerText = `Are you sure?`;
                clickCount++;
            } else if (clickCount === 1) {
                releasePet(adoptIdGlobal);
                document.getElementById("confirm-text-pet").innerText = `How could you release ${adoptName}?! Your dearest pet has stolen ${deduct_price} Lamocoins before leaving for the wild...`;
                confirmButton.style.display = 'none';
                closeButton.style.width = '140px';
                closeButton.innerText = 'Goodbye';
                closeButton.onclick = function() {
                    closeModalRelease();
                    location.reload();
                };
            }
        };

        modal.style.display = "block";
    }

    function closeModalRelease() {
        modal.style.display = "none";
    }

    async function releasePet(adoptId) {
        try {
            const response = await fetch(`/release_pet/${adoptId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log ("Pet released successfully.");
            } else {
                console.log ("Failed to release pet.");
            }
        } catch (error) {
            console.error('Error:', error);
            console.log ("An error occurred while releasing the pet.");
        }
    }

    window.showReleasePopup = showReleasePopup;
    window.closeModalRelease = closeModalRelease;
});

document.addEventListener("DOMContentLoaded", function() {
    var modal = document.getElementById("delete-item");
    var confirmButton = document.getElementById("yes-item");
    var closeButton = document.getElementById("no-item");
    var refund_price;

    function showDeletePopup(itemImage, itemFilter, itemId, price) {
        refund_price = price / 2;
        document.getElementById("confirm-text-item").innerText = `Would you like to recycle this item for ${refund_price} Lamocoins?`;
        document.getElementById("delete-item-img").src = itemImage;
        document.getElementById("delete-item-img").style.filter = itemFilter;

        confirmButton.onclick = function() {
            console.log("Attempting to delete item with ID:", itemId);
            deleteItem(itemId);
            document.getElementById("confirm-text-item").innerText = `Your item has been successfully recycled for ${refund_price} Lamocoins!`;
            closeButton.style.display = 'none';
            confirmButton.innerText = 'Nice!';
            confirmButton.onclick = function() {
                closeModalDelete();
                location.reload();
            };
        };

        modal.style.display = "block";
    }

    function closeModalDelete() {
        modal.style.display = "none";
    }

    async function deleteItem(itemId) {
        try {
            const response = await fetch(`/delete_item/${itemId}`, {
                method: 'DELETE'
            });
            console.log("Server response status:", response.status);
            if (response.ok) {
                console.log("Item recycled successfully.");
            } else {
                const errorText = await response.text();
                console.error("Failed to recycle item. Response:", errorText);
                console.log("Failed to recycle item: " + errorText);
            }
        } catch (error) {
            console.error('Error:', error);
            alert("An error occurred while recycling the item.");
        }
    }

    window.showDeletePopup = showDeletePopup;
    window.closeModalDelete = closeModalDelete;
});

async function downloadImage(imageSrc) {
    const image = await fetch(imageSrc)
    const imageBlog = await image.blob()
    const imageURL = URL.createObjectURL(imageBlog)

    const link = document.createElement('a')
    link.href = imageURL
    link.download = 'Congratulations on your very cool pet!'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    }