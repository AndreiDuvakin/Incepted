import datetime
import os

from flask import Flask, render_template, request, url_for
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from flask_wtf import CSRFProtect
from flask_restful import abort
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import redirect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from sqlalchemy import or_

from functions import check_password, mail, init_db_default, get_projects_data, get_user_data, save_project_logo
from forms.edit_profile import EditProfileForm
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.new_project import NewProjectForm

from data.users import User
from data.files import Files
from data.projects import Projects
from data.staff_projects import StaffProjects
from waitress import serve
from data import db_session

app = Flask(__name__)
key = 'test_secret_key'
app.config['SECRET_KEY'] = key
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


@app.route('/projects/delete/<int:id_project>', methods=['GET', 'POST'])
def delete_project(id_project):
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        project_del = data_session.query(Projects).filter(Projects.id == id_project).first()
        if project_del:
            if project_del.creator == current_user.id:
                staff = data_session.query(StaffProjects).filter(StaffProjects.project == id_project).all()
                for i in staff:
                    data_session.delete(i)
                if 'none_project' not in project_del.photo:
                    os.remove(project_del.photo)
                data_session.delete(project_del)
                data_session.commit()
                data_session.close()
                return redirect('/projects')
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
            projects = data_session.query(Projects).filter(or_(Projects.creator == user.id, Projects.id.in_(
                list(map(lambda x: x[0], data_session.query(
                    StaffProjects.project).filter(
                    StaffProjects.user == user.id).all()))))).all()
            resp = list(map(lambda x: get_projects_data(x), projects))
            return render_template('user_view.html', title=user.name + ' ' + user.surname, user=user,
                                   list_projects=resp)
        else:
            abort(404)
    else:
        return redirect('/login')


@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if current_user.is_authenticated:
        form = NewProjectForm()
        data_session = db_session.create_session()
        list_users = list(
            map(lambda x: get_user_data(x), data_session.query(User).filter(User.id != current_user.id).all()))
        if form.validate_on_submit():
            project = Projects(
                name=form.name.data,
                description=form.description.data,
                date_create=datetime.datetime.now(),
                creator=current_user.id
            )
            project.photo = save_project_logo(form.logo.data) if form.logo.data else 'static/images/none_project.png'
            data_session.add(project)
            data_session.flush()
            data_session.refresh(project)
            for i in list_users:
                if request.form.getlist(f"choose_{i['login']}") and i['id'] != current_user.id:
                    new_staffer = StaffProjects(
                        user=i['id'],
                        project=project.id,
                        role='user',
                        permission=3
                    )
                    data_session.add(new_staffer)
            data_session.commit()
            data_session.close()
            return redirect('/projects')
        data_session.close()
        return render_template('new_project.html', title='Новый проект', form=form, list_users=list_users)
    else:
        return redirect('/login')


@app.route('/projects', methods=['GET', 'POST'])
def project():
    if current_user.is_authenticated:
        data_session = db_session.create_session()
        resp = []
        if request.method == 'POST':
            pass
        else:
            projects = data_session.query(Projects).filter(or_(Projects.creator == current_user.id, current_user.id in
                                                               data_session.query(StaffProjects.project).filter(
                                                                   StaffProjects.user == current_user.id).all())).all()
            resp = list(map(lambda x: get_projects_data(x), projects))
        return render_template('projects.html', title='Проекты', list_projects=resp)
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
            data_session.close()
        if form.validate_on_submit():
            data_session = db_session.create_session()
            user = data_session.query(User).filter(User.id == current_user.id).first()
            if not user:
                return render_template('profile.html', title='Профиль', form=form,
                                       message='Ошибка, пользователь ненайден')
            if form.email.data != current_user.email:
                pass
            if form.photo.data:
                with open(f'static/app_files/user_logo/{current_user.login}.png', 'wb') as file:
                    form.photo.data.save(file)
                user.photo = f'static/app_files/user_logo/{current_user.login}.png'
            user.name = form.name.data
            user.surname = form.surname.data
            user.about = form.about.data
            user.birthday = form.birthday.data
            data_session.commit()
            data_session.close()
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
            data_session.close()
            if user and user.check_password(form.password.data):
                if user.activated:
                    login_user(user, remember=form.remember_me.data)
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
            data_session.close()
            token = s.dumps(form.email.data)
            link_conf = url_for('confirmation', token=token, _external=True)
            mail(f'Для завершения регистрации пройдите по ссылке: {link_conf}', form.email.data,
                 'Подтверждение регистрации')
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
            data_session.close()
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
        data_session.close()
        return redirect('/login?message=Срок действия ссылки истек, данные удалены&danger=True')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_error.html', title='Страница не найдена', error='404', message='Страница не найдена')


@app.errorhandler(403)
def page_not_found(error):
    return render_template('page_error.html', title='Ошибка доступа', error='403', message='Доступ сюда запрещен')


def main():
    db_path = 'db/incepted.db'
    db = os.path.exists(db_path)
    db_session.global_init(db_path)
    if not db:
        init_db_default()
    serve(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
