var edit_button = document.getElementById("edit_button"),
new_task_link = document.getElementById("new_task_link"),
quest_solve_link = document.getElementById("quest_solve_link"),
quest_solve_link_id = document.getElementById("quest_solve_link_id"),
is_template = document.getElementById("is_template");

edit_button.href = String(window.location.href) + '/edit';
new_task_link.href = String(window.location.href) + '/quest/new';

function push_file()
{
    document.getElementById('selectedFile').click();
    document.getElementById('upload_button').style = 'display: block;';
    document.getElementById('select_file_button').style = 'display: none;';
}