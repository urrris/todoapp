"use strict";

let form = document.querySelector('.main__form');
let showPasswordButton = document.getElementById('show');
let passwordField = document.getElementById('password');

form.addEventListener('change', function (event) {
    let emailField = form.elements.email;
    let submitButton = form.elements.submit;

    if (!emailField.value || !passwordField.value) {
        submitButton.style.backgroundColor = 'rgba(17, 17, 17, 0.25)';
    } else {
        submitButton.style.backgroundColor = 'rgba(0, 140, 255, 0.75)';
    }
});

showPasswordButton.addEventListener('click', function (event) {
    if (showPasswordButton.checked) {
        passwordField.type = 'text';
    } else {
        passwordField.type = 'password';
    }
});