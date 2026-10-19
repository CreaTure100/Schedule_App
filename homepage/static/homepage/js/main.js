/*
 * Скрипт Roomly: подставляет текущий год в подвал страницы.
 * Если JavaScript отключён, год уже выведен сервером ({% now "Y" %}).
 */
(function () {
  'use strict';

  function showCurrentYear() {
    var target = document.getElementById('current-year');
    if (target) {
      target.textContent = new Date().getFullYear();
    }
  }

  document.addEventListener('DOMContentLoaded', showCurrentYear);
})();
