"use strict";
import { checkFormFields } from './base.mjs';

/**
 * Аналог функции fullmatch из python-библиотеки re.
 * @param {RegExp} pattern 
 * @param {string} str 
 * @returns {Boolean}
 */
function fullMatch(pattern, str) {
    var match = str?.match(pattern);
    return match && match[0] === str ? match : null;
}
/**
 * Изменяет видимость элементов списка (проектов / задач).
 */
function showHideListItems() {
    let itemsList = new Set;  // Множество элементов, хранящих данные о проектах / задачах
    let categoriesList = new Set;  // Множество элементов, хранящих типы категорий задач (todo / in progress / done)

    for (let child of this.closest('.block-title').parentElement.children) {
        if (child.tagName == 'UL') {
            for (let cchild of child.children) {
                if (cchild.tagName == 'LI' && cchild.classList.length == 2) {
                    itemsList.add(cchild);
                } else {
                    categoriesList.add(cchild);
                }
            }
        }
    }

    // Здесь this - label, привязанный к input:checkbox
    // this.nextElementSibling - иконка стрелки, информирующая об изменении видимости элементов списка
    if (this.checked) {
        for (let item of itemsList) {
            item.style.display = 'flex';
        }
        for (let categorie of categoriesList) {
            categorie.style.display = 'initial';
        }
        this.nextElementSibling.setAttribute('transformed', true);
    } else {
        for (let item of itemsList) {
            item.style.display = 'none';
        }
        for (let categorie of categoriesList) {
            categorie.style.display = 'none';
        }
        this.nextElementSibling.setAttribute('transformed', false);
    }
}
/**
 * Асинхронно подгружает задачи по выбранному проекту.
 */
function getTasksByProject() {
    let projectName = this.firstElementChild.textContent;
    let projectType = this.firstElementChild.getAttribute('p-type');
    let xhr = new XMLHttpRequest();

    xhr.open('GET', '/get-tasks/');
    xhr.setRequestHeader('project-name', projectName);
    xhr.setRequestHeader('project-type', projectType);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            let tasksTodo = document.querySelector('.tasks-list__tasks-todo-list');
            tasksTodo.innerHTML = '';
            let tasksProgress = document.querySelector('.tasks-list__tasks-progress-list');
            tasksProgress.innerHTML = '';
            let tasksDone = document.querySelector('.tasks-list__tasks-done-list');
            tasksDone.innerHTML = '';

            let response = JSON.parse(xhr.responseText);

            for (let task of response['tasks']) {
                let li = document.createElement('li');
                li.className = 'tasks-section__tasks-list-item list-item';
                li.addEventListener('click', showTask);

                let span = document.createElement('span');
                span.textContent = task[0];

                let link = document.createElement('a');
                link.setAttribute('class', 'tasks-list-item__edit-task-button');
                link.setAttribute('p-name', projectName);
                link.setAttribute('p-type', projectType);
                link.addEventListener('click', changeTaskForm);
                link.addEventListener('click', editTask);

                let img = document.createElement('img');
                img.setAttribute('alt', '...');
                if (response['theme']) {
                    img.setAttribute('src', '/static/img/workspace/three-dots-light.svg');
                } else {
                    img.setAttribute('src', '/static/img/workspace/three-dots.svg');
                }

                link.appendChild(img);
                li.appendChild(span);
                li.appendChild(link);
                if (task[1] == 'Todo') {
                    tasksTodo.appendChild(li);
                } else if (task[1] == 'InProgress') {
                    tasksProgress.appendChild(li);
                } else {
                    tasksDone.appendChild(li);
                }
            }

            // Цикличный вызов функции изменения отображения элементов списков - необходимо!
            for (let button of showItemsButtons) {
                showHideListItems.call(button);
            }
        }
    }

    xhr.send();
}
/**
 * Асинхронно подгружает в форму создания / редактирования задачи исполнителей по выбранному проекту.
 */
function getExecutorsByProject() {
    let projectName, projectType;
    if (this instanceof HTMLSelectElement) {
        if (this.value == '') { // При отсутствии проектов у пользователя
            return;
        } 
        projectName = this.value;
        projectType = this.options[this.selectedIndex].getAttribute('p-type');
    } else {
        projectName = this.textContent;
        projectType = this.firstElementChild.getAttribute('p-type');
    }
    let xhr = new XMLHttpRequest();

    xhr.open('GET', '/get-task-executors/');
    xhr.setRequestHeader('project-name', projectName);
    xhr.setRequestHeader('project-type', projectType);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            let response = JSON.parse(xhr.responseText)
            let executorsField = document.getElementById('task-executors');
            let option;

            executorsField.innerHTML = '';
            for (let executor of Object.keys(response['executors'])) {
                option = document.createElement('option');
                option.value = executor;
                option.textContent = executor;

                executorsField.appendChild(option);
            }
        }
    }

    xhr.send();
}
/**
 * Асинхронно осуществялет поиск пользователей по их имени / почте и подгружает результаты в модальное окно поиска.
 * @param {KeyboardEvent} event 
 */
function searchForUsers(event) {
    // Проверка на ввод допустимого для email-адреса символа
    let keyRegex = new RegExp('[a-z0-9@\\.]');
    if (!fullMatch(keyRegex, event.key) && event.key != 'Backspace') {
        return;
    }

    // Очистка поисковой выдачи при пустом запросе
    let data = this.value;
    let regex = new RegExp("[~`=\\.\\-!@'#№|\\$;%:&,<>/\\\\\^\\?\\*\\(\\)\\[\\]\\{\\}\\+ ]+"); 
    if (data.replace(regex, '') == '') {
        this.parentElement.nextElementSibling.innerHTML = '';
        return;
    }

    let xhr = new XMLHttpRequest();
    xhr.open('GET', '/search-for-users/');
    xhr.setRequestHeader('data', data);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            let response = JSON.parse(xhr.responseText);
            let searchModalWindow = document.querySelector('.search-modal-window');
            let searchResultsBlock = searchModalWindow.querySelector('ul');
            let li, userPhoto, userName, userEmail, addFriendButton, deleteFriendButton;

            searchResultsBlock.innerHTML = '';
            for (let key of Object.keys(response['users'])) {
                li = document.createElement('li');
                li.className = 'search-results__search-result-item';
                
                userPhoto = document.createElement('img');
                userPhoto.className = 'search-result-item__item-photo';
                userPhoto.setAttribute('src', response['users'][key][1]);
                userPhoto.setAttribute('alt', '...');

                userName = document.createElement('span');
                userName.className = 'search-result-item__item-name';
                userName.textContent = response['users'][key][0];

                userEmail = document.createElement('span');
                userEmail.className = 'search-result-item__item-email';
                userEmail.textContent = key;

                li.appendChild(userPhoto);
                li.appendChild(userName);
                li.appendChild(userEmail);
                
                if (response['users'][key][2]) {
                    deleteFriendButton = document.createElement('img');
                    deleteFriendButton.className = 'search-result-item__control-item-button';
                    if (response['theme']) {
                        deleteFriendButton.setAttribute('src', '/static/img/workspace/delete-friend-light.png');
                    } else {
                        deleteFriendButton.setAttribute('src', '/static/img/workspace/delete-friend.svg');
                    }
                    li.appendChild(deleteFriendButton);
                } else {
                    addFriendButton = document.createElement('img');
                    addFriendButton.className = 'search-result-item__control-item-button';
                    if (response['theme']) {
                        addFriendButton.setAttribute('src', '/static/img/workspace/add-friend-light.svg');
                    } else {
                        addFriendButton.setAttribute('src', '/static/img/workspace/add-friend.svg');
                    }
                    li.appendChild(addFriendButton);

                }
                
                
                searchResultsBlock.appendChild(li);
            }
        }
    }

    xhr.send();
}

function changeTheme() {
    let lightThemeBlock = document.querySelector('.switch-block__light-theme');
    let darkThemeBlock = document.querySelector('.switch-block__dark-theme');
    let styles = document.querySelector('link:last-of-type');
    let images = document.querySelectorAll('img');
    let xhr = new XMLHttpRequest();

    xhr.open('GET', '/change-theme/');

    // Здесь this - input:checkbox
    if (this.checked) {
        lightThemeBlock.setAttribute('state', '');
        darkThemeBlock.setAttribute('state', 'active');

        styles.setAttribute('href', '/static/css/workspace-black.css')
        for (let image of images) {
            let path = image.getAttribute('src');
            path = path.replace('.svg', '-light.svg');
            image.setAttribute('src', path);
        }

        xhr.setRequestHeader('theme', 'True');
    } else {
        lightThemeBlock.setAttribute('state', 'active');
        darkThemeBlock.setAttribute('state', '');

        styles.setAttribute('href', '/static/css/workspace-white.css')
        for (let image of images) {
            let path = image.getAttribute('src');
            path = path.replace('-light.svg', '.svg');
            image.setAttribute('src', path);
        }

        xhr.setRequestHeader('theme', 'False');
    }

    xhr.send();
}
/**
 * Проверяет поля формы в зависимости от её типа, после чего отправляет данные на сервер.
 */
function validateForm() {
    let form = this.closest('form');
    let taskNewTaskProjectType, taskOldTaskProjectType;

    if (form.className.startsWith('project')) {  // Форма проекта
        let projectNameField = form.querySelector('.project-modal-window__input-project-name > input');
        let regex = new RegExp('[a-zA-Z -]{5,50}');

        if (!fullMatch(regex, projectNameField.value)) {
            projectNameField.value = '';
            projectNameField.setAttribute('placeholder', 'Название должно содержать от 5 до 50 символов и использовать английские буквы!');
            return;
        }
    } else if (form.className.startsWith('task')) {  // Форма задачи
        let taskNameField = form.querySelector('.task-modal-window__input-task-name > input');
        let taskDeadlineField = form.querySelector('#task-deadline');
        let regex = new RegExp('[a-zA-Z -]{5,50}');

        if (!fullMatch(regex, taskNameField.value)) {
            taskNameField.value = '';
            taskNameField.setAttribute('placeholder', 'Название должно содержать от 5 до 50 символов и использовать английские буквы!');
            return;
        }
        if (!taskDeadlineField.value) {
            return;
        }
        
        // Получение типов проектов, которым принадлежала и будет принадлежать задача - необходимо!
        let taskProjectField = form.querySelector('#task-project');
        taskNewTaskProjectType = taskProjectField.options[taskProjectField.selectedIndex].getAttribute('p-type');
        if (form.querySelector('input:nth-of-type(2)').getAttribute('name') == 'edit-task') {
            taskOldTaskProjectType = form.lastElementChild.getAttribute('p-type');
        }
    }

    let formData = new FormData(form);
    let xhr = new XMLHttpRequest();

    xhr.open('POST', '/workspace/');
    xhr.setRequestHeader('project-type', taskNewTaskProjectType);
    xhr.setRequestHeader('old-project-type', taskOldTaskProjectType);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            location.reload();
        }
    }

    xhr.send(formData);
}
/**
 * Включает / отключает поля формы.
 * @param {HTMLFormElement} form 
 * @param {string} flag 
 */
function controlFormFields(form, flag) {
    if (flag == 'disable') {
        for (let field of form.elements) {
            field.setAttribute('disabled', 'true');
        }
    } else {
        for (let field of form.elements) {
            field.removeAttribute('disabled');
        }
    }
}

function closeModalWindow() {
    let modalWindow = this.closest('div[class$="-modal-window"]');
    modalWindow.style.display = 'none';
    modalBackground.style.display = 'none';
}
/**
 * Закрывает модальное окно при нажатии клавиши Esc.
 * @param {Event} event 
 * @param {HTMLDivElement} modalWindow 
 */
function controlVisibilityOfModalWindows(event, modalWindow) {
    if (event.key == 'Escape') {
        closeModalWindow.call(modalWindow);
    }
}
/**
 * Настраивает и отображает модальное окно выбора создания (проекта / задачи).
 */
function createSmth() {
    let createSmthModalWindow = document.querySelector('.create-smth-modal-window');
    modalBackground.style.display = 'block';
    createSmthModalWindow.style.display = 'grid';
    window.onkeyup = (event) => controlVisibilityOfModalWindows(event, createSmthModalWindow);

    let createProjectButton = document.querySelector('.form__create-project-button');
    createProjectButton.addEventListener('click', closeModalWindow);
    createProjectButton.addEventListener('click', changeProjectForm);
    createProjectButton.addEventListener('click', createProject);

    let createTaskButton = document.querySelector('.form__create-task-button');
    createTaskButton.addEventListener('click', closeModalWindow);
    createTaskButton.addEventListener('click', changeTaskForm);
    createTaskButton.addEventListener('click', createTask);
}
/**
 * Настраивает модальное окно проекта в зависимости от типа взаимодействия с ним (создание / редактирование / просмотр).
 */
function changeProjectForm() {
    let projectModalWindow = document.querySelector('.project-modal-window');
    let formTitle = projectModalWindow.querySelector('.form-title span');
    let form = projectModalWindow.querySelector('form');
    let projectNameField = form.elements['project-name'];
    let projectActionType = projectModalWindow.querySelector('.project-modal-window__form input:nth-of-type(2)');
    let projectSubmitButton = projectModalWindow.querySelector('input.project-modal-window__submit-button');
    let deleteProjectButton = projectModalWindow.querySelector('input.project-modal-window__delete-button');

    if (this.classList[0] == 'form__create-project-button') {
        formTitle.textContent = 'Создать проект';
        projectActionType.setAttribute('name', 'create-project');
        projectNameField.setAttribute('title', 'Название должно содержать от 5 до 50 символов и использовать английские буквы.');
        projectSubmitButton.setAttribute('value', 'Создать');
        projectSubmitButton.style.display = 'initial';
        deleteProjectButton.style.display = 'none';
        controlFormFields(form, 'activate');
    } else if (this.className == 'projects-list-item__edit-project-button') {
        formTitle.textContent = 'Редактировать проект';
        projectActionType.setAttribute('name', 'edit-project');
        projectNameField.setAttribute('title', 'Название должно содержать от 5 до 50 символов и использовать английские буквы.');
        projectSubmitButton.setAttribute('value', 'Сохранить');
        projectSubmitButton.style.display = 'initial';
        deleteProjectButton.style.display = 'initial';
        controlFormFields(form, 'activate');
    } else {
        formTitle.textContent = 'Просмотр проекта';
        projectNameField.removeAttribute('title');
        // Скрытие неактивных сотрудников проекта
        for (let option of form.elements['project-coworkers'].options) {
            if (!option.selected) {
                option.style.display = 'none';
            }
        }
        projectSubmitButton.style.display = 'none';
        deleteProjectButton.style.display = 'none';
        controlFormFields(form, 'disable');
    }
}
/**
 * Настраивает и отображает модальное окно создания проекта.
 */
function createProject() {
    let projectModalWindow = document.querySelector('.project-modal-window');
    let form = projectModalWindow.querySelector('form.project-modal-window__form');

    // "Обнуление" полей формы
    form.elements['project-name'].value = '';
    for (let option of form.elements['project-coworkers']) {
        option.selected = false;
    }

    modalBackground.style.display = 'block';
    projectModalWindow.style.display = 'grid';
    window.onkeyup = (event) => controlVisibilityOfModalWindows(event, projectModalWindow);
}
/**
 * Настраивает и отображает модальное окно редактирования проекта.
 */
function editProject() {
    let projectModalWindow = document.querySelector('.project-modal-window');
    let projectName = this.parentElement.firstElementChild.textContent;
    let projectType = this.getAttribute('p-type') || this.parentElement.firstElementChild.getAttribute('p-type');
    let xhr = new XMLHttpRequest();

    xhr.open('GET', '/get-project-info/');
    xhr.setRequestHeader('project-name', projectName);
    xhr.setRequestHeader('project-type', projectType);

    // Асинхронная подгрузка полей формы
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            let form = projectModalWindow.querySelector('form.project-modal-window__form');
            let coworkersField = form.elements['project-coworkers'];
            let response = JSON.parse(xhr.responseText);
            let coworkersList = response['coworkers'];
            let option;

            form.elements['project-name'].value = projectName;
            coworkersField.innerHTML = '';
            for (let coworker of Object.keys(coworkersList)) {
                option = document.createElement('option');
                option.value = coworker;
                option.textContent = coworker;
                if (coworkersList[coworker] == true) {
                    option.selected = true;
                }

                coworkersField.appendChild(option);
            }

            let oldProjectName = document.createElement('input');
            oldProjectName.style.display = 'none';
            oldProjectName.name = 'old-project-name';
            oldProjectName.value = projectName;
            form.appendChild(oldProjectName);

            modalBackground.style.display = 'block';
            projectModalWindow.style.display = 'grid';
            window.onkeyup = (event) => controlVisibilityOfModalWindows(event, projectModalWindow);
        }
    }

    xhr.send();
}

function deleteProject() {
    let projectName = document.querySelector('input#project-name').value;
    let xhr = new XMLHttpRequest();
    let deleteProjectButton = this;

    xhr.open('GET', '/delete-project/');
    xhr.setRequestHeader('project-name', projectName);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            closeModalWindow.call(deleteProjectButton);
            location.reload();
        }
    }

    xhr.send();
}
/**
 * @param {Event} event 
 */
function showProject(event) {
    if (event.target instanceof HTMLImageElement) {  // Целевой объект нажатия - кнопка редактирования проекта
        editProject.call(event.target.parentElement);
    } else {
        editProject.call(this.firstElementChild);
        setTimeout(() => changeProjectForm.call(this), 50);
    }
}
/**
 * Настраивает модальное окно задачи в зависимости от типа взаимодействия с ней (создание / редактирование / просмотр).
 */
function changeTaskForm() {
    let taskModalWindow = document.querySelector('.task-modal-window');
    let formTitle = taskModalWindow.querySelector('.form-title span');
    let form = taskModalWindow.querySelector('form');
    let taskNameField = form.elements['task-name'];
    let taskActionType = taskModalWindow.querySelector('.task-modal-window__form input:nth-of-type(2)');
    let taskSubmitButton = taskModalWindow.querySelector('input.task-modal-window__submit-button');
    let deleteTaskButton = taskModalWindow.querySelector('input.task-modal-window__delete-button');

    if (this.classList[0] == 'form__create-task-button') {
        formTitle.textContent = 'Создать задачу';
        taskActionType.setAttribute('name', 'create-task');
        taskNameField.setAttribute('title', 'Название должно содержать от 5 до 50 символов и использовать английские буквы.');
        taskSubmitButton.setAttribute('value', 'Создать');
        taskSubmitButton.style.display = 'initial';
        deleteTaskButton.style.display = 'none';
        controlFormFields(form, 'activate');
    } else if (this.className == 'tasks-list-item__edit-task-button') {
        formTitle.textContent = 'Редактировать задачу';
        taskActionType.setAttribute('name', 'edit-task');
        taskNameField.setAttribute('title', 'Название должно содержать от 5 до 50 символов и использовать английские буквы.');
        taskSubmitButton.setAttribute('value', 'Сохранить');
        taskSubmitButton.style.display = 'initial';
        deleteTaskButton.style.display = 'initial';
        controlFormFields(form, 'activate');
    } else {
        formTitle.textContent = 'Просмотр задачи';
        taskNameField.removeAttribute('title');
        // Скрытие неактивных исполнителей задачи
        for (let option of form.elements['task-executors'].options) {
            if (!option.selected) {
                option.style.display = 'none';
            }
        }
        taskSubmitButton.style.display = 'none';
        deleteTaskButton.style.display = 'none';
        controlFormFields(form, 'disable');
    }
}
/**
 * Настраивает и отображает модальное окно создания задачи.
 */
function createTask() {
    let taskModalWindow = document.querySelector('.task-modal-window');
    let form = taskModalWindow.querySelector('form.task-modal-window__form');

    // "Обнуление" полей формы
    form.elements['task-name'].value = '';
    form.elements['task-description'].value = '';
    form.elements['task-project'].value = form.elements['task-project'].firstElementChild.textContent;
    form.elements['task-deadline'].value = '';
    form.elements['task-priority'].value = 1;
    form.elements['task-status'].value = 'Todo';
    for (let executor of form.elements['task-executors']) {
        executor.selected = false;
    }

    modalBackground.style.display = 'block';
    taskModalWindow.style.display = 'grid';
    window.onkeyup = (event) => controlVisibilityOfModalWindows(event, taskModalWindow);
}
/**
 * Настраивает и отображает модальное окно редактирования задачи.
 */
function editTask() {
    let taskModalWindow = document.querySelector('.task-modal-window');
    let projectName = this.getAttribute('p-name');
    let projectType = this.getAttribute('p-type');
    let taskName = this.parentElement.firstElementChild.textContent;
    let xhr = new XMLHttpRequest();

    xhr.open('GET', '/get-task-info/');
    xhr.setRequestHeader('project-name', projectName);
    xhr.setRequestHeader('project-type', projectType);
    xhr.setRequestHeader('task-name', taskName);

    // Асинхронная подгрузка полей формы
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            let form = taskModalWindow.querySelector('form.task-modal-window__form');
            let executorsField = document.getElementById('task-executors');
            let response = JSON.parse(xhr.responseText);
            let executorsList = response['executors'];
            let option;

            form.elements['task-name'].value = taskName;
            form.elements['task-description'].value = response['description'];
            form.elements['task-project'].value = projectName;
            form.elements['task-deadline'].value = response['deadline'];
            form.elements['task-priority'].value = response['priority'];
            form.elements['task-status'].value = response['status'];
            executorsField.innerHTML = '';
            for (let executor of Object.keys(executorsList)) {
                option = document.createElement('option');
                option.value = executor;
                option.textContent = executor;
                if (executorsList[executor] == true) {
                    console.log(executor);
                    option.selected = true;
                }

                executorsField.appendChild(option);
            }

            let oldTaskName = document.createElement('input');
            oldTaskName.style.display = 'none';
            oldTaskName.name = 'old-task-name';
            oldTaskName.value = taskName;
            form.appendChild(oldTaskName);

            let oldProjectName = document.createElement('input');
            oldProjectName.style.display = 'none';
            oldProjectName.name = 'old-project-name';
            oldProjectName.value = projectName;
            oldProjectName.setAttribute('p-type', projectType);
            form.appendChild(oldProjectName);

            modalBackground.style.display = 'block';
            taskModalWindow.style.display = 'grid';
            window.onkeyup = (event) => controlVisibilityOfModalWindows(event, taskModalWindow);
        }
    }

    xhr.send()
}

function deleteTask() {
    let taskName = document.getElementById('task-name').value;
    let projectField = document.getElementById('task-project');
    let projectType = projectField.options[projectField.selectedIndex].getAttribute('p-type');
    let xhr = new XMLHttpRequest();
    let deleteTaskButton = this;

    xhr.open('GET', '/delete-task/');
    xhr.setRequestHeader('task-name', taskName);
    xhr.setRequestHeader('project-name', projectField.value);
    xhr.setRequestHeader('project-type', projectType);

    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            closeModalWindow.call(deleteTaskButton);
            location.reload();
        }
    }

    xhr.send();
}
/**
 * @param {Event} event 
 */
function showTask(event) {
    if (event.target instanceof HTMLImageElement) {  // Целевой объект нажатия - кнопка редактирования задачи
        editTask.call(event.target.parentElement);
    } else {
        editTask.call(this.lastElementChild);
        setTimeout(() => changeTaskForm.call(this), 50);
    }
}

function showSearchModalWindow() {
    let searchModalWindow = document.querySelector('.search-modal-window');
    let searchField = document.getElementById('search-field');
    let searchResultsBlock = searchModalWindow.querySelector('ul');

    searchField.value = '';
    searchResultsBlock.innerHTML = '';

    window.onkeyup = (event) => controlVisibilityOfModalWindows(event, searchModalWindow);
    modalBackground.style.display = 'block';
    searchModalWindow.style.display = 'grid';
    searchField.addEventListener('keyup', searchForUsers);
}


let showItemsButtons = document.querySelectorAll('.show-items-button input');
for (let button of showItemsButtons) {
    button.addEventListener('change', showHideListItems);
}

let projects = document.querySelectorAll('.projects-list__item');
for (let project of projects) {
    project.addEventListener('click', getTasksByProject);
    project.addEventListener('click', showProject);
}

let changeThemeButton = document.getElementById('change-theme');
changeThemeButton.addEventListener('click', changeTheme);

let createSmthButton = document.querySelector('.workspace__create-smth-button');
createSmthButton.addEventListener('click', createSmth);

let editProjectsButtons = document.querySelectorAll('.projects-list-item__edit-project-button');
for (let editProjectButton of editProjectsButtons) {
    editProjectButton.addEventListener('click', changeProjectForm);
    editProjectButton.addEventListener('click', editProject);
}

let closeModalWindowButtons = document.querySelectorAll('.close-modal-window-button');
for (let button of closeModalWindowButtons) {
    button.addEventListener('click', closeModalWindow);
}

let forms = document.querySelectorAll('form[class$="modal-window__form"]');
for (let form of forms) {
    form.addEventListener('change', checkFormFields);
}

let submitButtons = document.querySelectorAll('input[class$="modal-window__submit-button"]');
for (let submitButton of submitButtons) {
    submitButton.addEventListener('click', validateForm);
}

let deleteProjectButton = document.querySelector('input.project-modal-window__delete-button');
deleteProjectButton.addEventListener('click', deleteProject);

let deleteTaskButton = document.querySelector('input.task-modal-window__delete-button');
deleteTaskButton.addEventListener('click', deleteTask);

let modalBackground = document.querySelector('#modal-background');

let taskProjectField = document.getElementById('task-project');
taskProjectField.addEventListener('change', getExecutorsByProject);
getExecutorsByProject.call(taskProjectField);

let searchButton = document.querySelector('.user-function-icons__search-icon');
searchButton.addEventListener('click', showSearchModalWindow);
