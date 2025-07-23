


// let clickedTestIds = new Set();

function findAndClickButton() {
    const conversationTurns = document.querySelectorAll('[data-testid^="conversation-turn-"]');
    let maxTestIdElement = null;
    let maxTestId = -1;
    conversationTurns.forEach(element => {
        const testId = parseInt(element.getAttribute('data-testid').split('-').pop());
        if (testId > maxTestId && !clickedTestIds.has(testId)) {
            maxTestId = testId;
            maxTestIdElement = element;
        }
    });

    if (maxTestIdElement) {
        const button = maxTestIdElement.querySelector('span[data-state="closed"] > button[aria-label="Read Aloud"]');
        if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
            button.click();
            clickedTestIds.add(maxTestId);
        }
    }
}

setInterval(findAndClickButton, 2000);






let clickedTestIds = new Set();
let queue = [];
let isPlaying = false;

function findAndClickButton() {
    const conversationTurns = document.querySelectorAll('[data-testid^="conversation-turn-"]');
    conversationTurns.forEach(element => {
        const testId = parseInt(element.getAttribute('data-testid').split('-').pop());
        if (!clickedTestIds.has(testId)) {
            const button = element.querySelector('span[data-state="closed"] > button[aria-label="Read Aloud"]');
            if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
                queue.push({ testId, button });
                clickedTestIds.add(testId);
            }
        }
    });

    if (!isPlaying) {
        playNextInQueue();
    }
}

function playNextInQueue() {
    if (queue.length === 0) {
        isPlaying = false;
        return;
    }

    isPlaying = true;
    const { testId, button } = queue.shift();
    button.click();

    const intervalId = setInterval(() => {
        const stopButton = document.querySelector(`[data-testid="conversation-turn-${testId}"] button[aria-label="Stop"]`);
        if (!stopButton || stopButton.offsetParent === null) { // Check if the stop button is hidden
            clearInterval(intervalId);
            playNextInQueue();
        }
    }, 1000);
}

setInterval(findAndClickButton, 2000);