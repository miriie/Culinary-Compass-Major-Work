// Timer JS
    const timerArea = document.getElementById("timer-area");
    const startBtn = document.getElementById("start-timer");
    const resetBtn = document.getElementById("reset-timer");

    const timerPopup = document.getElementById("timer-popup");
    const timerBtn = document.querySelector(".timer-button");
    const closeTimerBtn = document.getElementById("close-timer");

    let countdown = null;
    let timeLeft = 0;

    // Show the popup when Timer button is clicked
    timerBtn.onclick = () => {
        timerPopup.style.display = "block";
    };

    // Hide the popup when the close button is clicked
    closeTimerBtn.onclick = () => {
        timerPopup.style.display = "none";
        clearInterval(countdown);
        countdown = null;
        timeLeft = 0;
        resetToInputFields();
    };

    startBtn.onclick = () => {
        if (countdown) return;

        const hours = parseInt(document.getElementById("hours-input").value) || 0;
        const minutes = parseInt(document.getElementById("minutes-input").value) || 0;
        const seconds = parseInt(document.getElementById("seconds-input").value) || 0;

        if (minutes > 59 || seconds > 59) {
        alert("Minutes and seconds must be between 0 and 59.");
        return;
        }

        timeLeft = hours * 3600 + minutes * 60 + seconds;

        if (timeLeft <= 0) {
        alert("Please enter a time greater than 0.");
        return;
        }

        // Replace input fields with countdown display
        timerArea.innerHTML = `<p id="timer-display"></p>`;
        updateDisplay();

        countdown = setInterval(() => {
        timeLeft--;
        updateDisplay();

        if (timeLeft <= 0) {
            clearInterval(countdown);
            countdown = null;
            alert("Time's up!");
        }
        }, 1000);
    };

    resetBtn.onclick = () => {
        clearInterval(countdown);
        countdown = null;
        timeLeft = 0;
        resetToInputFields();
    };

    function updateDisplay() {
        const h = String(Math.floor(timeLeft / 3600)).padStart(2, '0');
        const m = String(Math.floor((timeLeft % 3600) / 60)).padStart(2, '0');
        const s = String(timeLeft % 60).padStart(2, '0');
        const display = document.getElementById("timer-display");
        if (display) display.textContent = `${h}:${m}:${s}`;
    }

    function resetToInputFields() {
        timerArea.innerHTML = `
        <div class="time-inputs">
            <input type="number" id="hours-input" placeholder="00" min="0" max="23">
            <span>:</span>
            <input type="number" id="minutes-input" placeholder="00" min="0" max="59">
            <span>:</span>
            <input type="number" id="seconds-input" placeholder="00" min="0" max="59">
        </div>
        `;
    }
    // Make the timer popup draggable
    const header = document.getElementById("timer-header");
    let offsetX = 0, offsetY = 0, isDragging = false;

    header.addEventListener("mousedown", (e) => {
        isDragging = true;
        offsetX = e.clientX - timerPopup.offsetLeft;
        offsetY = e.clientY - timerPopup.offsetTop;
        header.style.cursor = "grabbing";
    });

    document.addEventListener("mouseup", () => {
        isDragging = false;
        header.style.cursor = "move";
    });

    document.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        timerPopup.style.left = `${e.clientX - offsetX}px`;
        timerPopup.style.top = `${e.clientY - offsetY}px`;
        timerPopup.style.right = "auto";
        timerPopup.style.bottom = "auto";
    });

// Dropdown JS
    function toggleDropdown(id = "tagDropdown", iconId = "dropdown-icon") {
    const dropdown = document.getElementById(id);
    const icon = document.getElementById(iconId);

    if (!dropdown || !icon) return;

    const isOpen = dropdown.style.maxHeight && dropdown.style.maxHeight !== "0px";

    if (isOpen) {
        dropdown.style.maxHeight = "0px";
        icon.textContent = "⮟";
    } else {
        dropdown.style.maxHeight = dropdown.scrollHeight + "px";
        icon.textContent = "⮝";
    }
    }

// Annotation JS
document.addEventListener('DOMContentLoaded', function () {
    const showBtn = document.getElementById('show-annotation-btn');
    const annotationForm = document.getElementById('annotation-form');
    const highlightedTextInput = document.getElementById('highlighted-text');
    const annotationTextarea = document.getElementById('annotation');

    document.addEventListener('mouseup', function (event) {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        showBtn.style.display = 'none';

        const anchorNode = selection.anchorNode;
        const parent = anchorNode && anchorNode.parentElement;

        if (
            text.length > 0 &&
            parent &&
            document.getElementById('instructions-text').contains(parent)
        ) {
            highlightedTextInput.value = text;

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            showBtn.style.top = `${window.scrollY + rect.top - 30}px`;
            showBtn.style.left = `${window.scrollX + rect.left}px`;
            showBtn.style.display = 'inline-block';
        }
    });

    showBtn.addEventListener('click', function () {
        showBtn.style.display = 'none';
        annotationForm.style.display = 'block';
        annotationTextarea.focus();
    });
});
