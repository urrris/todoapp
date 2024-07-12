"use strict";

/**
 * Окрашивает кнопку отправки данных формы в зависимости от заполнения полей формы.
 * @param {Event} event 
 */
export function checkFormFields(event) {
    // Здесь this instanceof HTMLFormElement
    let submitButton = this.querySelector('input[class$="submit-button"]');
    for (let field of this.elements) {
        if (!'hidden/file/button/select/txtarea/flag'.includes(field.getAttribute('type'))) {
            if (field.value == '' || !field.value) {
                submitButton.style.backgroundColor = 'rgba(17, 17, 17, 0.25)';
                return;
            }
        }
    }
    submitButton.style.backgroundColor = 'rgba(0, 140, 255, 0.75)';
}

/**
 * @param {Event} event 
 */
export function showPasswordFieldsData(event) {
    let form = this.closest('form');
    for (let field of form.querySelectorAll('input[id$="password"]')) {
        if (this.checked) {
            field.type = 'text';
        } else {
            field.type = 'password';
        }
    }
}
