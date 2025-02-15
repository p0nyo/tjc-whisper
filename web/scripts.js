eel.expose(on_receive_message);
function on_receive_message(message) {
  addText(message);
}

function startTranscription() {
  eel.start_transcription()
}

function stopTranscription() {
  eel.stop_transcription()
}

function addText(message) {
  const transArea = document.getElementById("transcription");

  const newel = document.createElement("div");
  const blank = document.createElement("div");
  newel.classList.add("transcript-container");
  blank.classList.add("transcript-container");
  newel.textContent = message;
  blank.style.height = "10px";
  
  transArea.appendChild(newel);
  transArea.appendChild(blank);

  // Makes sure the message box scrolls as new messages come in
  transArea.scrollTop = transArea.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function() {
  const startButton = document.getElementById("start-button");
  const stopButton = document.getElementById("stop-button");
  const statusBar = document.getElementById("status");
  const statusArea = document.getElementById("status-area");

  // Check if the buttons exist
  startButton.addEventListener('click', () => {
    statusBar.innerHTML = "Transcription Started . . .";
    statusArea.style.backgroundColor = "green";
    startTranscription();
  })

  stopButton.addEventListener('click', () => {
    statusBar.innerHTML = "Transcription Stopped.";
    statusArea.style.backgroundColor = "red";
    stopTranscription();
  })
}); 

