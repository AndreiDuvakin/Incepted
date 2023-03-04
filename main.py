import datetime
import os
import logging

from flask import Flask, render_template, request, url_for
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from flask_wtf import CSRFProtect
from flask_restful import abort
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import redirect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from sqlalchemy import or_
from json import loads

from functions import check_password, mail, init_db_default, get_projects_data, get_user_data, save_project_logo, \
    overdue_quest_project, save_proof_quest, find_files_answer, file_tree, delete_project_data, delete_quest_data
from forms.edit_profile import EditProfileForm
from forms.login import LoginForm
from forms.find_project import FindProjectForm
from forms.register import RegisterForm
from forms.project import ProjectForm, AddFileProject
from forms.recovery import RecoveryForm, NewPasswordForm
from forms.conf_delete_project import DeleteProjectForm
from forms.task import Task, AnswerTask

from data.users import User
from data.quests import Quests
from data.answer import Answer
from data.proof_file import FileProof
from data.files import Files
from data.projects import Projects
from data.staff_projects import StaffProjects
from waitress import serve
from data import db_session

app = Flask(__name__)
with open('incepted.config', 'r', encoding='utf-8') as file:
    file = file.read()
    file = loads(file)
key = file["encrypt_key"]
app.config['SECRET_KEY'] = key
logging.basicConfig(level=logging.INFO, filename="logfiles/main.log", format="%(asctime)s %(levelname)s %(message)s",
                    encoding='utf-8')
csrf = CSRFProtect(app)
s = URLSafeTimedSerializer(key)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def base():
    if not current_user.is_authenticated:
        return render_template('main.html', title='Главная')
    else:
        return redirect('/projects')


@app.route('/showcase', methods=['GET', 'POST'])
def showcase():
    if current_user.is_authenticated:
        return render_template('showcase.html', title='Витрина')
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>/quest/<int:id_task>/edit', methods=['GET', 'POST'])
def edit_quest(id_project, id_task):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        current_task = data_session.query(Quests).filter(Quests.id == id_task).first()
        if current_project and current_task and current_task.project == current_project.id and (
                current_task.creator == current_user.id or current_project.creator == current_user.id):
            form = Task()
            if request.method == 'GET':
                form.name.data = current_task.name
                form.description.data = current_task.description
                form.deadline_time.data = current_task.deadline.time()
                form.deadline_date.data = current_task.deadline.date()
            if form.delete.data:
                delete_quest_data(current_task, data_session)
                data_session.delete(current_task)
                data_session.commit()
                return redirect(f'/project/{str(current_project.id)}')
            if form.validate_on_submit():
                if form.deadline_date.data and form.deadline_time.data:
                    deadline = datetime.datetime.combine(form.deadline_date.data, form.deadline_time.data)
                else:
                    deadline = None
                current_task.name = form.name.data if form.name.data else None
                current_task.description = form.description.data if form.description.data else None
                current_task.deadline = deadline
                data_session.commit()
                return redirect(f'/project/{str(current_project.id)}/quest/{str(current_task.id)}')
            return render_template('edit_task.html', title='Редактирование задачи', form=form, porject=current_project,
                                   task=current_task)
        else:
            abort(403)
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>/file/<int:id_file>/delete')
def delete_file(id_project, id_file):
    if current_user.is_authenticated:
        from_path = request.args.get('from') if request.args.get('from') else ''
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        current_file = data_session.query(Files).filter(Files.id == id_file).first()
        if current_project and current_file:
            if current_user.id in map(lambda x: x[0], data_session.query(StaffProjects.user).filter(
                    StaffProjects.project == current_project.id).all()) or current_user.id == current_project.creator:
                current_proof = data_session.query(FileProof).filter(FileProof.file == id_file).all()
                os.remove(current_file.path)
                data_session.delete(current_file)
                if current_proof:
                    quest = data_session.query(Answer.quest).filter(Answer.id == current_proof[0].answer).first()
                    for i in current_proof:
                        data_session.delete(i)
                    data_session.commit()
                    if from_path == 'project':
                        return redirect(f'/project/{current_project.id}')
                    return redirect(f'/project/{current_project.id}/quest/{quest[0]}')
                data_session.commit()
                return redirect(f'/project/{current_project.id}')
            else:
                abort(403)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>/quest/<int:id_task>', methods=['GET', 'POST'])
def task_project(id_project, id_task):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        current_task = data_session.query(Quests).filter(Quests.id == id_task).first()
        if current_project and current_task and current_task.project == current_project.id:
            form = AnswerTask()
            current_answer = data_session.query(Answer).filter(Answer.quest == current_task.id).first()
            list_files = None
            if form.submit.data and request.method == 'POST':
                if current_answer:
                    current_answer.text = form.text.data
                    current_answer.date_edit = datetime.datetime.now()
                    current_task.realized = form.realized.data
                    data_session.commit()
                    if form.file.data[0].filename:
                        files = list(
                            map(lambda x: save_proof_quest(current_project, x, current_user.id), form.file.data))
                        for i in files:
                            if not data_session.query(FileProof).filter(FileProof.answer == current_answer.id,
                                                                        FileProof.file == i).first():
                                proof_file = FileProof(
                                    answer=current_answer.id,
                                    file=i
                                )
                                data_session.add(proof_file)
                                data_session.commit()
                else:
                    if form.file.data[0].filename:
                        files = list(
                            map(lambda x: save_proof_quest(current_project, x, current_user.id), form.file.data))
                    else:
                        files = False
                    current_task.realized = form.realized.data
                    current_answer = Answer(
                        quest=current_task.id,
                        text=form.text.data,
                        creator=current_user.id,
                        date_create=datetime.datetime.now(),
                        date_edit=datetime.datetime.now()
                    )
                    data_session.add(current_answer)
                    data_session.flush()
                    data_session.refresh(current_answer)
                    if files:
                        for i in files:
                            proof_file = FileProof(
                                answer=current_answer.id,
                                file=i
                            )
                            data_session.add(proof_file)
                    data_session.commit()
                return redirect(f'/project/{current_project.id}')
            if current_answer and request.method == 'GET':
                form.text.data = current_answer.text
                form.realized.data = current_task.realized
                files = data_session.query(FileProof).filter(FileProof.answer == current_answer.id).all()
                if files:
                    list_files = list(map(lambda x: find_files_answer(x.file), files))
            return render_template('answer.html', title='Решение', project=current_project, task=current_task,
                                   form=form, list_files=list_files)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>/quest/new', methods=['GET', 'POST'])
def new_task_project(id_project):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        if current_project:
            form = Task()
            if form.validate_on_submit():
                if form.deadline_date.data and form.deadline_time.data:
                    deadline = datetime.datetime.combine(form.deadline_date.data, form.deadline_time.data)
                else:
                    deadline = None
                quest = Quests(
                    project=current_project.id,
                    creator=current_user.id,
                    name=form.name.data if form.name.data else None,
                    description=form.description.data if form.description.data else None,
                    date_create=datetime.datetime.now(),
                    deadline=deadline,
                    realized=False
                )
                data_session.add(quest)
                data_session.commit()
                return redirect(f'/project/{str(current_project.id)}')
            return render_template('new_task.html', title='Новая задача', form=form, porject=current_project)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>/edit', methods=['GET', 'POST'])
def edit_project(id_project):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        if current_project:
            staff = data_session.query(StaffProjects).filter(StaffProjects.project == current_project.id).all()
            if current_user.id == current_project.creator:
                list_users = list(
                    map(lambda x: get_user_data(x),
                        data_session.query(User).filter(User.id != current_user.id, User.activated == 1).all()))
                staff = list(map(lambda x: get_user_data(x), data_session.query(User).filter(
                    User.id.in_(list(map(lambda x: x.user, staff)))).all())) if staff else []
                form = ProjectForm()
                if form.save.data:
                    new_staff = []
                    for i in list_users:
                        if request.form.getlist(f"choose_{i['login']}") and i['id'] != current_user.id:
                            new_staff.append(i)
                            if i not in staff:
                                new_staffer = StaffProjects(
                                    user=i['id'],
                                    project=current_project.id,
                                    role='user',
                                    permission=3
                                )
                                data_session.add(new_staffer)
                        data_session.commit()
                    if sorted(new_staff, key=lambda x: x['id']) != sorted(staff, key=lambda x: x['id']):
                        for i in staff:
                            if i not in new_staff:
                                data_session.delete(data_session.query(StaffProjects).filter(
                                    StaffProjects.user == i['id'], StaffProjects.project == current_project.id).first())
                        data_session.commit()
                    if form.logo.data:
                        current_project.photo = save_project_logo(form.logo.data)
                        data_session.commit()
                    current_project.name = form.name.data
                    current_project.description = form.description.data
                    data_session.commit()
                    return redirect(f'/project/{current_project.id}')
                if form.del_photo.data:
                    os.remove(current_project.photo)
                    current_project.photo = 'static/images/none_project.png'
                    data_session.commit()
                    return redirect(f'/project/{current_project.id}/edit')
                form.name.data = current_project.name
                form.description.data = current_project.description
                return render_template('edit_project.html', title='Изменение проекта', form=form, list_users=list_users,
                                       staff=staff, project=current_project)
            else:
                abort(403)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/project/<int:id_project>', methods=['POST', 'GET'])
def project(id_project):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        current_project = data_session.query(Projects).filter(Projects.id == id_project).first()
        if current_project:
            staff = data_session.query(StaffProjects).filter(StaffProjects.project == current_project.id).all()
            if current_user.id == current_project.creator or current_user.id in list(map(lambda x: x.user, staff)):
                staff = list(map(lambda x: get_user_data(x), data_session.query(User).filter(
                    User.id.in_(list(map(lambda x: x.user, staff)))).all())) if staff else []
                quests = data_session.query(Quests).filter(Quests.project == current_project.id).all()
                if quests:
                    quests_sort = sorted(list(filter(lambda x: x.deadline is not None, quests)),
                                         key=lambda x: (x.realized, x.deadline))
                    quests = list(filter(lambda x: x.realized == 0, quests_sort)) + list(
                        filter(lambda x: x.deadline is None, quests)) + list(
                        filter(lambda x: x.realized == 1, quests_sort))
                    quests = list(map(lambda x: overdue_quest_project(x), quests))
                files_list = file_tree(f'static/app_files/all_projects/{current_project.id}')
                form_file = AddFileProject()
                if form_file.validate_on_submit():
                    if form_file.file.data[0].filename:
                        files = list(
                            map(lambda x: save_proof_quest(current_project, x, current_user.id), form_file.file.data))
                    return redirect(f'/project/{str(current_project.id)}')
                return render_template('project.html',
                                       project=current_project,
                                       title=current_project.name,
                                       staff=staff,
                                       quests=quests,
                                       file_tree=files_list,
                                       form_file=form_file)
            else:
                abort(403)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/recovery/confirmation/<token>', methods=['GET', 'POST'])
def conf_recovery(token):
    try:
        user_email = s.loads(token, max_age=86400)
        data_session = db_session.create_session()
        user = data_session.query(User).filter(User.email == user_email).first()
        if user:
            form = NewPasswordForm()
            if form.validate_on_submit():
                if form.password.data != form.repeat_password.data:
                    return render_template('recovery.html', title='Восстановление', form=form, recovery=0,
                                           message='Пароли не совпадают')
                status_password = check_password(form.password.data)
                if status_password != 'OK':
                    return render_template('recovery.html', title='Восстановление', form=form, recovery=0,
                                           message=str(status_password))
                user.set_password(form.password.data)
                data_session.commit()
                mail(f'Для аккаунта {user.login}, успешно был обновлен пароль', user.email,
                     'Изменение пароля')
                return redirect('/login?message=Пароль обновлен')
            return render_template('recovery.html', title='Восстановление', form=form, recovery=0, message='')
        else:
            return redirect('/login?message=Пользователь не найден&danger=True')
    except SignatureExpired:
        return redirect('/login?message=Срок действия ссылки истек&danger=True')


@app.route('/recovery', methods=['GET', 'POST'])
def recovery():
    if not current_user.is_authenticated:
        form = RecoveryForm()
        if form.validate_on_submit():
            token = s.dumps(form.email.data)
            link_conf = url_for('conf_recovery', token=token, _external=True)
            mail(f'Для сбросы пароля пройдите по ссылке: {link_conf}', form.email.data,
                 'Восстановление доступа')
            return redirect('/login?message=Мы выслали ссылку для сброса вам на почту')
        return render_template('recovery.html', title='Восстановление пароля', form=form, recovery=True, message='')
    else:
        return redirect('/')


@app.route('/project/<int:id_project>/delete', methods=['GET', 'POST'])
def delete_project(id_project):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        project_del = data_session.query(Projects).filter(Projects.id == id_project).first()
        if project_del:
            if project_del.creator == current_user.id:
                form = DeleteProjectForm()
                if form.validate_on_submit():
                    if str(form.conf.data).lower().strip() != f'delete/{str(project_del.name)}'.lower().strip():
                        return render_template('delete_project.html', title='Удаление проекта', form=form,
                                               project=project_del,
                                               message='Вы не правильно ввели фразу')
                    delete_project_data(project_del, data_session)
                    return redirect('/projects')
                return render_template('delete_project.html', title='Удаление проекта', form=form, project=project_del,
                                       message='')
            else:
                abort(403)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/user/<string:_login>', methods=['GET', 'POST'])
def user_view(_login):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        user = data_session.query(User).filter(User.login == _login).first()
        if user:
            current_projects = data_session.query(Projects).filter(or_(Projects.creator == user.id, Projects.id.in_(
                list(map(lambda x: x[0], data_session.query(
                    StaffProjects.project).filter(
                    StaffProjects.user == user.id).all()))))).all()
            resp = list(map(lambda x: get_projects_data(x), current_projects))
            return render_template('user_view.html',
                                   title=user.name if user.name else '' + ' ' + user.surname if user.surname else '',
                                   user=user,
                                   list_projects=resp)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if current_user.is_authenticated:
        form = ProjectForm()
        data_session = db_session.create_session()
        list_users = list(
            map(lambda x: get_user_data(x), data_session.query(User).filter(User.id != current_user.id).all()))
        if form.validate_on_submit():
            current_project = Projects(
                name=form.name.data,
                description=form.description.data,
                date_create=datetime.datetime.now(),
                creator=current_user.id
            )
            current_project.photo = save_project_logo(
                form.logo.data) if form.logo.data else 'static/images/none_project.png'
            data_session.add(current_project)
            data_session.flush()
            data_session.refresh(current_project)
            for i in list_users:
                if request.form.getlist(f"choose_{i['login']}") and i['id'] != current_user.id:
                    new_staffer = StaffProjects(
                        user=i['id'],
                        project=current_project.id,
                        role='user',
                        permission=3
                    )
                    data_session.add(new_staffer)
            data_session.commit()
            os.mkdir(f'static/app_files/all_projects/{str(current_project.id)}')
            return redirect('/projects')
        return render_template('new_project.html', title='Новый проект', form=form, list_users=list_users)
    else:
        return redirect('/login')


@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if current_user.is_authenticated:
        find = False
        form = FindProjectForm()
        data_session = db_session.create_session()
        resp = []
        current_projects = \
            data_session.query(Projects).filter(or_(Projects.creator == current_user.id,
                                                    Projects.id.in_(
                                                        list(map(lambda x: x[0],
                                                                 data_session.query(
                                                                     StaffProjects.project).filter(
                                                                     StaffProjects.user
                                                                     == current_user.id).all()))))).all()
        if form.validate_on_submit():
            new_resp = []
            for i in range(len(current_projects)):
                if str(form.project.data).lower().strip() in str(current_projects[i].name).lower().strip():
                    new_resp.append(current_projects[i])
            current_projects = new_resp
            find = True
        resp = list(map(lambda x: get_projects_data(x), current_projects))
        return render_template('projects.html', title='Проекты', list_projects=resp, form=form, find=find)
    else:
        return redirect('/login')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if current_user.is_authenticated:
        form = EditProfileForm(
            CombinedMultiDict((request.files, request.form)),
            email=current_user.email,
            name=current_user.name,
            surname=current_user.surname,
            about=current_user.about,
            birthday=current_user.birthday
        )
        if form.del_photo.data:
            data_session = db_session.create_session()
            user = data_session.query(User).filter(User.id == current_user.id).first()
            if not user:
                return render_template('profile.html', title='Профиль', form=form,
                                       message='Ошибка, пользователь ненайден')
            os.remove(current_user.photo)
            user.photo = 'static/images/none_logo.png'
            data_session.commit()
        if form.validate_on_submit():
            data_session = db_session.create_session()
            user = data_session.query(User).filter(User.id == current_user.id).first()
            if not user:
                return render_template('profile.html', title='Профиль', form=form,
                                       message='Ошибка, пользователь ненайден')
            if form.email.data != current_user.email:
                token = s.dumps(form.email.data)
                link_conf = url_for('confirmation', token=token, _external=True)
                mail(f'Для изменения почты пройдите по ссылке: {link_conf}', form.email.data,
                     'Изменение почты')
                user.activated = False
                user.email = form.email.data
            if form.photo.data:
                with open(f'static/app_files/user_logo/{current_user.login}.png', 'wb') as file:
                    form.photo.data.save(file)
                user.photo = f'static/app_files/user_logo/{current_user.login}.png'
            user.name = form.name.data
            user.surname = form.surname.data
            user.about = form.about.data
            user.birthday = form.birthday.data
            data_session.commit()
            return redirect('/profile')
        return render_template('profile.html', title='Профиль', form=form, message='')
    else:
        return redirect('/login')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated:
        message = request.args.get('message') if request.args.get('message') else ''
        danger = request.args.get('danger') if request.args.get('danger') else False
        form = LoginForm()
        if form.validate_on_submit():
            data_session = db_session.create_session()
            user = data_session.query(User).filter(User.email == form.login.data).first()
            if not user:
                user = data_session.query(User).filter(User.login == form.login.data).first()
            if user and user.check_password(form.password.data):
                if user.activated:
                    login_user(user, remember=form.remember_me.data)
                    logging.info(f'{user.login} logged in')
                    return redirect('/projects')
                else:
                    return render_template('login.html',
                                           message="Ваша почта не подтверждена",
                                           danger=True,
                                           form=form)
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   danger=True,
                                   form=form)
        return render_template('login.html', title='Авторизация', form=form, message=message,
                               danger=danger)
    else:
        return redirect('/projects')


@app.route('/logout')
@login_required
def logout():
    logging.info(f'{current_user.login} logged out')
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not current_user.is_authenticated:
        form = RegisterForm()
        if form.validate_on_submit():
            data_session = db_session.create_session()
            if data_session.query(User).filter(User.login == form.login.data).first():
                return render_template('register.html', form=form, message="Такой пользователь уже есть",
                                       title='Регистрация')
            if data_session.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', form=form, message="Такая почта уже есть", title='Регистрация')
            status_password = check_password(form.password.data)
            if status_password != 'OK':
                return render_template('register.html', form=form, message=status_password, title='Регистрация')
            user = User(
                email=form.email.data,
                name=form.name.data,
                login=form.login.data,
                activity=datetime.datetime.now(),
                data_reg=datetime.date.today(),
                photo='static/images/none_logo.png',
                role=1
            )
            user.set_password(form.password.data)
            data_session.add(user)
            data_session.commit()
            token = s.dumps(form.email.data)
            link_conf = url_for('confirmation', token=token, _external=True)
            mail(f'Для завершения регистрации пройдите по ссылке: {link_conf}', form.email.data,
                 'Подтверждение регистрации')
            logging.info(f'{form.login.data} was registered')
            return redirect('/login?message=Мы выслали ссылку для подтверждения почты')
        return render_template('register.html', form=form, message='', title='Регистрация')
    else:
        return redirect('/projects')


@app.route('/confirmation/<token>')
def confirmation(token):
    try:
        user_email = s.loads(token, max_age=86400)
        data_session = db_session.create_session()
        user = data_session.query(User).filter(User.email == user_email).first()
        if user:
            user.activated = True
            data_session.commit()
            logging.info(f'{user.login} has been confirmed')
            return redirect('/login?message=Почта успешно подтверждена')
        else:
            return redirect('/login?message=Пользователь не найден&danger=True')
    except SignatureExpired:
        data_session = db_session.create_session()
        users = data_session.query(User).filter(
            User.activated == 0 and User.activated < datetime.datetime.now() - datetime.timedelta(days=1)).all()
        if users:
            list(map(lambda x: data_session.delete(x), users))
            data_session.commit()
        return redirect('/login?message=Срок действия ссылки истек, данные удалены&danger=True')


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('page_error.html', title='Ошибка сервера', error='500', message='Технические шоколадки')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_error.html', title='Страница не найдена', error='404', message='Страница не найдена')


@app.errorhandler(403)
def access_error(error):
    return render_template('page_error.html', title='Ошибка доступа', error='403', message='Доступ сюда запрещен')


def main():
    db_path = 'db/incepted.db'
    db = os.path.exists(db_path)
    db_session.global_init(db_path)
    if not db:
        init_db_default()
    serve(app, host='0.0.0.0', port=5000, threads=10)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logging.warning(f'{error}')
