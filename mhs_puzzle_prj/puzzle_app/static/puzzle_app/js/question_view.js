document.addEventListener("DOMContentLoaded", () => {
    // Select all answer buttons
    const answerButtons = document.querySelectorAll(".answer_button");
    const nextButton = document.getElementById("next");

    answerButtons.forEach(button => {
        // Add click event listener for each button
        button.addEventListener("click", () => {
            // Get the question ID associated with this button
            let questionId = button.getAttribute("data-question-id");
            console.log("this button's question id is " + questionId);

            // Find the corresponding hidden input for this question's score
            const selectedScoreInput = document.getElementById(`selectedScore_${questionId}`);

            // Remove "selected" class and reset color for all answer buttons of this question
            document.querySelectorAll(`.answer_button[data-question-id='${questionId}']`).forEach(btn => {
                btn.classList.remove("selected");
                btn.style.backgroundColor = ""; // Reset color to default
            });

            // Add "selected" class to the clicked button and update its color
            button.classList.add("selected");
            button.style.backgroundColor = "#ff7a6e"; // Highlight color for selected answer

            // Set the hidden input's value to the selected answer's score
            selectedScoreInput.value = button.getAttribute("data-score");
            console.log("the value of the form's score input is " + selectedScoreInput.value)
        });
    });

    // Validate that each question has a selected answer before allowing form submission
    nextButton.addEventListener("click", (event) => {
        let allQuestionsAnswered = true;

        document.querySelectorAll("input[type='hidden'][id^='selectedScore_']").forEach(input => {
            if (!input.value) {
                allQuestionsAnswered = false;
                const questionId = input.id.split('_')[1];
                document.getElementById(`question-view-${questionId}`).classList.add("unanswered");
            } else {
                const questionId = input.id.split('_')[1];
                document.getElementById(`question-view-${questionId}`).classList.remove("unanswered");
            }
        });


        if (!allQuestionsAnswered) {
            event.preventDefault();
            alert("Please select an answer for each question before proceeding.");
        }
    });
});