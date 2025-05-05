document.addEventListener("DOMContentLoaded", () => {
  const usernameField = document.querySelector("#usernameField");
  const feedBackArea = document.querySelector(".invalid_feedback");
  const emailField = document.querySelector("#emailField");
  const emailFeedBackArea = document.querySelector(".emailFeedBackArea");
  const usernameSuccessOutput = document.querySelector(".usernameSuccessOutput");
  const showPasswordToggle = document.querySelector(".showPasswordToggle");
  const passwordField = document.querySelector("#passwordField");
  const submitBtn = document.querySelector(".submit-btn");

  // Kiểm tra sự tồn tại của các phần tử trước khi gắn sự kiện
  if (showPasswordToggle && passwordField) {
    const handleToggleInput = (e) => {
      if (showPasswordToggle.textContent === "SHOW") {
        showPasswordToggle.textContent = "HIDE";
        passwordField.setAttribute("type", "text");
      } else {
        showPasswordToggle.textContent = "SHOW";
        passwordField.setAttribute("type", "password");
      }
    };
    showPasswordToggle.addEventListener("click", handleToggleInput);
  }

  if (emailField && emailFeedBackArea && submitBtn) {
    emailField.addEventListener("keyup", (e) => {
      const emailVal = e.target.value;
      emailField.classList.remove("is-invalid");
      emailFeedBackArea.style.display = "none";

      if (emailVal.length > 0) {
        fetch("/authentication/validate-email", {
          body: JSON.stringify({ email: emailVal }),
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          }
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.emailerror) {
              submitBtn.disabled = true;
              emailField.classList.add("is-invalid");
              emailFeedBackArea.style.display = "block";
              emailFeedBackArea.innerHTML = `<p>${data.emailerror}</p>`;
            } else {
              submitBtn.removeAttribute("disabled");
            }
          });
      }
    });
  }

  if (usernameField && feedBackArea && usernameSuccessOutput && submitBtn) {
    usernameField.addEventListener("keyup", (e) => {
      const usernameVal = e.target.value;
      usernameSuccessOutput.style.display = "block";
      usernameSuccessOutput.textContent = `Checking ${usernameVal}`;
      usernameField.classList.remove("is-invalid");
      feedBackArea.style.display = "none";

      if (usernameVal.length > 0) {
        fetch("/authentication/validate-username", {
          body: JSON.stringify({ username: usernameVal }),
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          }
        })
          .then((res) => res.json())
          .then((data) => {
            usernameSuccessOutput.style.display = "none";
            if (data.usernameerror) {
              usernameField.classList.add("is-invalid");
              feedBackArea.style.display = "block";
              feedBackArea.innerHTML = `<p>${data.usernameerror}</p>`;
              submitBtn.disabled = true;
            } else {
              submitBtn.removeAttribute("disabled");
            }
          });
      }
    });
  }
});
