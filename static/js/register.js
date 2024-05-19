"use strict";

let passwordField = document.getElementById('password');
let confirmPasswordField = document.getElementById('confirm_password');
let showPasswordButton = document.getElementById('show');
let uploadFileField = document.querySelector('.main__upload-file');
let photoField = document.getElementById('photo');
let form = document.querySelector('.main__form');

form.addEventListener('change', function (event) {
    let usernameField = form.elements.username;
    let emailField = form.elements.email;
    let submitButton = form.elements.submit;

    if (!usernameField.value || !emailField.value || !passwordField.value || !confirmPasswordField.value) {
        submitButton.style.backgroundColor = 'rgba(17, 17, 17, 0.25)';
    } else {
        submitButton.style.backgroundColor = 'rgba(0, 140, 255, 0.75)';
    }
});

showPasswordButton.addEventListener('click', function (event) {
    if (showPasswordButton.checked) {
        passwordField.type = 'text';
        confirmPasswordField.type = 'text';
    } else {
        passwordField.type = 'password';
        confirmPasswordField.type = 'password';
    }
});

photoField.addEventListener('change', function (event) {
    uploadFileField.textContent = photoField.value;
});
