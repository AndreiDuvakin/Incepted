function add_link()
{
    document.getElementById('add_link_button').style = 'display: none;';
    document.getElementById('repeal_link_button').style = 'display: block;';
    document.getElementById('form_link').style = 'display: block;';
}
function repeal_link()
{
    document.getElementById('add_link_button').style = 'display: block;';
    document.getElementById('repeal_link_button').style = 'display: none;';
    document.getElementById('form_link').style = 'display: none;';
}