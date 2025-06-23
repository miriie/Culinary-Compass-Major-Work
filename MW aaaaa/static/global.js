// Timer JS
const timerArea = document.getElementById("timer-area");
const startBtn = document.getElementById("start-timer");
const resetBtn = document.getElementById("reset-timer");
const timerPopup = document.getElementById("timer-popup");
const timerBtn = document.querySelector(".timer-button");
const closeTimerBtn = document.getElementById("close-timer");
const header = document.getElementById("timer-header");

let countdown = null;
let startTime = null;  // timestamp ms when timer started or resumed
let duration = 0;      // total seconds duration
let pausedTimeLeft = null; // seconds remaining when paused
let isPaused = false;

// Show/hide popup when timer button clicked
timerBtn && (timerBtn.onclick = () => {
  if (timerPopup.style.display === "block") {
    timerPopup.style.display = "none";
    localStorage.setItem('timerVisible', 'false');
  } else {
    timerPopup.style.display = "block";
    localStorage.setItem('timerVisible', 'true');
  }
});

// Close popup button
closeTimerBtn.onclick = () => {
  timerPopup.style.display = "none";
  localStorage.setItem('timerVisible', 'false');
};

// Start or resume the countdown
function startTimer(totalSeconds) {
  clearInterval(countdown);
  isPaused = false;
  pausedTimeLeft = null;

  duration = totalSeconds;
  startTime = Date.now();

  // Save to localStorage
  localStorage.setItem('timerStart', startTime.toString());
  localStorage.setItem('timerDuration', duration.toString());
  localStorage.setItem('timerVisible', 'true');
  localStorage.removeItem('timerPaused');
  localStorage.removeItem('timerPausedTimeLeft');

  timerPopup.style.display = "block";

  timerArea.innerHTML = `<p id="timer-display"></p>`;
  updateDisplay(totalSeconds);

  countdown = setInterval(tick, 200);
}

function tick() {
  let elapsedSeconds;
  if (isPaused && pausedTimeLeft !== null) {
    updateDisplay(pausedTimeLeft);
    return;
  } else {
    elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
  }

  const timeLeft = duration - elapsedSeconds;

  if (timeLeft <= 0) {
    clearInterval(countdown);
    countdown = null;
    localStorage.removeItem('timerStart');
    localStorage.removeItem('timerDuration');
    localStorage.removeItem('timerPaused');
    localStorage.removeItem('timerPausedTimeLeft');
    updateDisplay(0);
    alert("Time's up!");
    startBtn.textContent = "Start";
    return;
  }

  updateDisplay(timeLeft);
}

// Update timer display text
function updateDisplay(seconds) {
  const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
  const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  const display = document.getElementById("timer-display");
  if (display) display.textContent = `${h}:${m}:${s}`;
}

// Reset inputs area
function resetToInputFields() {
  clearInterval(countdown);
  countdown = null;
  startTime = null;
  duration = 0;
  pausedTimeLeft = null;
  isPaused = false;
  localStorage.removeItem('timerStart');
  localStorage.removeItem('timerDuration');
  localStorage.removeItem('timerPaused');
  localStorage.removeItem('timerPausedTimeLeft');
  startBtn.textContent = "Start";

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

// Start/Pause/Resume
startBtn.onclick = () => {
  if (countdown && !isPaused) {
    // Pause
    clearInterval(countdown);
    countdown = null;
    isPaused = true;

    const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
    pausedTimeLeft = duration - elapsedSeconds;

    localStorage.setItem('timerPaused', 'true');
    localStorage.setItem('timerPausedTimeLeft', pausedTimeLeft.toString());

    startBtn.textContent = "Resume";
  } else if (isPaused) {
    // Resume
    isPaused = false;
    startTime = Date.now();
    duration = pausedTimeLeft;

    localStorage.setItem('timerStart', startTime.toString());
    localStorage.setItem('timerDuration', duration.toString());
    localStorage.removeItem('timerPaused');
    localStorage.removeItem('timerPausedTimeLeft');

    startBtn.textContent = "Pause";

    countdown = setInterval(tick, 200);
  } else {
    // Start new timer
    const hours = parseInt(document.getElementById("hours-input").value) || 0;
    const minutes = parseInt(document.getElementById("minutes-input").value) || 0;
    const seconds = parseInt(document.getElementById("seconds-input").value) || 0;

    if (minutes > 59 || seconds > 59) {
      alert("Minutes and seconds must be between 0 and 59.");
      return;
    }

    const totalSeconds = hours * 3600 + minutes * 60 + seconds;
    if (totalSeconds <= 0) {
      alert("Please enter a time greater than 0.");
      return;
    }

    startBtn.textContent = "Pause";
    startTimer(totalSeconds);
  }
};

// Reset button
resetBtn.onclick = () => {
  resetToInputFields();
};

// Save timer data on reload
window.addEventListener('load', () => {
  const savedStart = parseInt(localStorage.getItem('timerStart'));
  const savedDuration = parseInt(localStorage.getItem('timerDuration'));
  const shouldShow = localStorage.getItem('timerVisible') === 'true';
  const savedPaused = localStorage.getItem('timerPaused') === 'true';
  const savedPausedTimeLeft = parseInt(localStorage.getItem('timerPausedTimeLeft'));
  const savedTop = localStorage.getItem('timerTop');
  const savedLeft = localStorage.getItem('timerLeft');

  if (shouldShow) {
    timerPopup.style.display = "block";
  }

  if (savedPaused) {
    // Timer is paused
    isPaused = true;
    pausedTimeLeft = savedPausedTimeLeft;
    startBtn.textContent = "Resume";
    timerArea.innerHTML = `<p id="timer-display"></p>`;
    updateDisplay(pausedTimeLeft);
  } else if (savedStart && savedDuration) {
    const elapsed = Math.floor((Date.now() - savedStart) / 1000);
    const timeLeft = savedDuration - elapsed;

    if (timeLeft > 0) {
      startTime = savedStart;
      duration = savedDuration;
      isPaused = false;
      startBtn.textContent = "Pause";

      timerArea.innerHTML = `<p id="timer-display"></p>`;
      updateDisplay(timeLeft);

      countdown = setInterval(() => {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        const currentLeft = duration - elapsedSeconds;

        if (currentLeft <= 0) {
          clearInterval(countdown);
          countdown = null;
          localStorage.removeItem('timerStart');
          localStorage.removeItem('timerDuration');
          updateDisplay(0);
          alert("Time's up!");
          startBtn.textContent = "Start";
          return;
        }

        updateDisplay(currentLeft);
      }, 200);
    } else {
      resetToInputFields();
    }
  } else {
    resetToInputFields();
  }

  // Restore popup position
  if (savedTop && savedLeft) {
    timerPopup.style.top = savedTop;
    timerPopup.style.left = savedLeft;
    timerPopup.style.right = "auto";
    timerPopup.style.bottom = "auto";
  }
});

// Draggable popup logic
let offsetX = 0, offsetY = 0, isDragging = false;

header.addEventListener("mousedown", (e) => {
  isDragging = true;
  offsetX = e.clientX - timerPopup.offsetLeft;
  offsetY = e.clientY - timerPopup.offsetTop;
  header.style.cursor = "grabbing";
});

document.addEventListener("mouseup", () => {
  if (isDragging) {
    localStorage.setItem('timerTop', timerPopup.style.top);
    localStorage.setItem('timerLeft', timerPopup.style.left);
  }
  isDragging = false;
  header.style.cursor = "move";
});

document.addEventListener("mousemove", (e) => {
  if (!isDragging) return;

  const minLeft = 0;
  const minTop = document.getElementById('top-division').offsetHeight;
  const maxLeft = window.innerWidth - timerPopup.offsetWidth;
  const maxTop = window.innerHeight - timerPopup.offsetHeight;

  let newLeft = e.clientX - offsetX;
  let newTop = e.clientY - offsetY;

  newLeft = Math.min(Math.max(newLeft, minLeft), maxLeft);
  newTop = Math.min(Math.max(newTop, minTop), maxTop);

  timerPopup.style.left = `${newLeft}px`;
  timerPopup.style.top = `${newTop}px`;
  timerPopup.style.right = "auto";
  timerPopup.style.bottom = "auto";
});



// Dropdown JS
function toggleDropdown(dropdownId, iconElement) {
  const dropdown = document.getElementById(dropdownId);
  const icon = iconElement;

  if (!dropdown || !icon) return;

  const isOpen = dropdown.classList.contains('open');

  if (isOpen) {
    dropdown.classList.remove('open');
    icon.textContent = "⮟";
  } else {
    dropdown.classList.add('open');
    icon.textContent = "⮝";
  }
}