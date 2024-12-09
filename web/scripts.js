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
  newel.classList.add("transcript-container");
  newel.textContent = message;

  transArea.appendChild(newel);

  // Makes sure the message box scrolls as new messages come in
  transArea.scrollTop = transArea.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function() {
  const startButton = document.getElementById("start-button");
  const stopButton = document.getElementById("stop-button");

  // Check if the buttons exist
  startButton.addEventListener('click', () => {
    // alert('on click works');
    // addText("Transcription box works.")
    startTranscription();
  })

  stopButton.addEventListener('click', () => {
    stopTranscription();
  })
}); 

