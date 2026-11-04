
let usedSlots = 18;
const maxSlots = 27;

const transferButton = document.getElementById("transfer-button");
const capacityText = document.getElementById("capacity-text");
const capacityFill = document.getElementById("capacity-fill");
const transferMessage = document.getElementById("transfer-message");


const craftButton = document.getElementById("craft-button");
const craftMessage = document.getElementById("craft-message");
let wood = 32;
let stone = 64;
let pickaxes = 1;

craftButton.addEventListener("click", function() {
    if (wood >= 1 && stone >= 1) {
        wood--;
        stone--;
        pickaxes++;
        updateInventory();

        craftMessage.textContent =
            "⛏️ Pickaxe crafted! Wood: " + wood +
            " | Stone: " + stone +
            " | Pickaxes: " + pickaxes;

        craftMessage.style.color = "#a8d878";
    } else {
        craftMessage.textContent =
            "Not enough materials to craft a pickaxe!";
        craftMessage.style.color = "#ff7777";
    }
});

function updateInventory() {
    document.getElementById("wood-count").textContent = wood;
    document.getElementById("stone-count").textContent = stone;
    document.getElementById("pickaxe-count").textContent = pickaxes;
}

const woodCount = document.getElementById("wood-count");

function updateInventory() {
    woodCount.textContent = wood;
}

updateInventory();

let chestWood = 0;

/*
transferButton.addEventListener("click", function () {
    if (wood > 0 && usedSlots < maxSlots) {
        wood--;
        chestWood++;

usedSlots++;

capacityText.textContent =
    "Storage Capacity: " + usedSlots + " / " + maxSlots + " slots";

capacityFill.style.width =
    (usedSlots / maxSlots * 100) + "%";


        updateInventory();

        transferMessage.textContent =
            "Wood transferred! Inventory: " + wood +
            " | Chest: " + chestWood;
    } else {
        transferMessage.textContent =
            "Cannot transfer more wood!";
    }
});
*/



