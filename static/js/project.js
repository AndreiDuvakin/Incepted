var edit_button = document.getElementById("edit_button"),
new_task_link = document.getElementById("new_task_link"),
quest_solve_link = document.getElementById("quest_solve_link"),
quest_solve_link_id = document.getElementById("quest_solve_link_id");

edit_button.href = String(window.location.href) + '/edit';
new_task_link.href = String(window.location.href) + '/quest/new';
quest_solve_link.href = String(window.location.href) + '/quest/' + quest_solve_link_id.className;