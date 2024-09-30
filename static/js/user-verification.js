"use strict";
import { checkFormFields, showPasswordFieldsData } from "./base.mjs";

let form = document.querySelector('.main__form');
form.addEventListener('change', checkFormFields);

let showPasswordButton = document.getElementById('show');
showPasswordButton.addEventListener('click', showPasswordFieldsData);
