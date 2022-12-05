import datetime

from flask import Flask, render_template, request, url_for
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from werkzeug.utils import redirect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from functions import check_password, mail
from forms.login import LoginForm
from forms.register import RegisterForm
from data.users import User
from waitress import serve
from data import db_session

app = Flask(__name__)
key = 'test_secret_key'
app.config['SECRET_KEY'] = key
s = URLSafeTimedSerializer(key)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def base():
    return render_template('main.html', title='Главная')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated:
        message = request.args.get('message') if request.args.get('message') else ''
        email_repeat = request.args.get('email_repeat') if request.args.get('email_repeat') else False
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                if user.activated:
                    login_user(user, remember=form.remember_me.data)
                    return redirect('/')
                else:
                    return render_template('login.html',
                                           message="Ваша почта не подтверждена",
                                           form=form)
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', title='Авторизация', form=form, message=message, email_repeat=email_repeat)
    else:
        return redirect('/')


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
                activity=datetime.datetime.now()
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
        return redirect('/')


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
            return redirect('/login?message=Пользователь не найден')
    except SignatureExpired:
        data_session = db_session.create_session()
        users = data_session.query(User).filter(
            User.activated == 0 and User.activated < datetime.datetime.now() - datetime.timedelta(days=1)).all()
        if users:
            list(map(lambda x: data_session.delete(x), users))
            data_session.commit()
        data_session.close()
        return redirect('/login?message=Срок действия ссылки истек, данные удалены')


def main():
    db_session.global_init("db/incepted.db")
    serve(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
