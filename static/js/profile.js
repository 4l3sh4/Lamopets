function toggleSanctuary() {
    var sanctuary = document.getElementById("sanctuary");
    var closet = document.getElementById("closet");
    var backButton = document.querySelector(".back-button"); 
    var deleteButton = document.querySelector(".delete-button"); 
    var petsButton = document.querySelector("#petsButton"); 
    var closetButton = document.querySelector("#closetButton"); 

    sanctuary.style.display = "block";
    closet.style.display = "none";
    
    var profileDisplay = document.getElementById("profile-display");
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
    var petsButton = document.querySelector("#petsButton"); 
    var closetButton = document.querySelector("#closetButton"); 

    sanctuary.style.display = "none";
    closet.style.display = "block";

    var profileDisplay = document.getElementById("profile-display");
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
    var petsButton = document.querySelector("#petsButton"); 
    var closetButton = document.querySelector("#closetButton"); 

    sanctuary.style.display = "none";
    closet.style.display = "none";

    var profileDisplay = document.getElementById("profile-display");
    profileDisplay.style.justifyContent = "center";

    backButton.style.display = "none";
    deleteButton.style.display = "none";
    petsButton.style.display = "block";
    closetButton.style.display = "block";
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
async function deleteItem(itemId) {
    if (confirm("Would you like to recycle this item?")) {
        try {
            const response = await fetch(`/delete_item/${itemId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                alert("Item recycled successfully.");
                location.reload();
            } else {
                alert("Failed to recycle item.");
            }
        } catch (error) {
            console.error('Error:', error);
            alert("An error occurred while deleting the item.");
        }
    }
}
async function releasePet(adopt_id) {
    if (confirm("Are you sure you want to release this pet?")) {
        if (confirm("Are you REALLY REALLY sure you want to release this pet?")) {
            try {
                const response = await fetch(`/release_pet/${adopt_id}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    alert("Pet released to the wild successfully.");
                    location.reload();
                } else {
                    alert("Failed to release pet.");
                }
            } catch (error) {
                console.error('Error:', error);
                alert("An error occurred while releasing the pet.");
            }
        }
    }
}

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