import datetime
import os
import shutil
import smtplib
from json import loads
from email.message import EmailMessage
from sqlalchemy import or_

from data.answer import Answer
from data.proof_file import FileProof
from data.quests import Quests
from data.roles import Roles
from data.users import User
from data.staff_projects import StaffProjects
from data.files import Files
from data import db_session
import uuid
import pymorphy2


def check_password(password=''):
    smb = 'qwertyuiopasdfghjklzxcvbnm'
    if len(password) < 6:
        return 'Пароль должен быть длиннее 6 символов'
    elif False in [True if i.isalpha() and i.lower() in smb or i.isdigit() else False for i in password]:
        return 'Пароль может содержать только буквы латинского алфавита и цифры'
    elif True not in [True if i.isdigit() else False for i in password]:
        return 'Пароль должен содержать буквы разного регистра и цифры'
    elif False not in [True if i.islower() and i.isalpha() else False for i in password]:
        return 'Пароль должен содержать буквы разного регистра и цифры'
    else:
        return 'OK'


def mail(msg, to, topic='Подтверждение почты'):
    with open('incepted.config', 'r', encoding='utf-8') as file:
        file = loads(file.read())
    login, password = file["mail_login"], file["mail_password"]
    email_server = "smtp.yandex.ru"
    sender = "incepted@yandex.ru"
    em = EmailMessage()
    em.set_content(msg)
    em['To'] = to
    em['From'] = sender
    em['Subject'] = topic
    mailServer = smtplib.SMTP(email_server)
    mailServer.set_debuglevel(1)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(login, password)
    mailServer.ehlo()
    mailServer.send_message(em)
    mailServer.quit()


def init_db_default():
    data_session = db_session.create_session()
    roles = [['admin', 2], ['moderator', 1], ['user', 0]]
    for i in roles:
        role = Roles(
            name=i[0],
            rights=i[1]
        )
        data_session.add(role)
    data_session.commit()
    data_session.close()


def get_user_data(user):
    resp = {
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'login': user.login,
        'email': user.email,
        'photo': user.photo,
        'role': user.role
    }
    return resp


def get_projects_data(project):
    data_session = db_session.create_session()
    staff = data_session.query(StaffProjects.user).filter(StaffProjects.project == project.id).all()
    resp = {
        'id': project.id,
        'name': project.name,
        'logo': project.photo,
        'description': project.description,
        'staff': list(map(lambda x: get_user_data(x), data_session.query(User).filter(
            User.id.in_(list(map(lambda x: x[0], staff)))).all())) if staff else []
    }
    resp['staff'].insert(0, get_user_data(data_session.query(User).filter(User.id == project.creator).first()))
    return resp


def save_project_logo(photo):
    filename = f'static/app_files/project_logo/{uuid.uuid4()}.png'
    with open(filename, 'wb') as f:
        photo.save(f)
    return filename


def overdue_quest_project(quest):
    if quest.deadline is None:
        quest.overdue = ''
    elif str(quest.deadline.date()) == str(datetime.datetime.now().date()):
        quest.overdue = 'today'
    elif quest.deadline < datetime.datetime.now():
        quest.overdue = 'yes'
        quest.time_left = 'Просрочено на' + round_date(quest.deadline)
    elif quest.deadline > datetime.datetime.now():
        quest.overdue = 'no'
        quest.time_left = 'Еще есть: ' + round_date(quest.deadline)
    return quest


def round_date(date_time):
    morph = pymorphy2.MorphAnalyzer()
    difference = abs(date_time - datetime.datetime.now()).days
    resp = ''
    if difference // 365:
        resp += f'{difference // 365} {morph.parse("год")[0].make_agree_with_number(difference // 365).word}'
        difference -= 365 * (difference // 365)
    if difference // 30:
        resp += ', ' if resp else ' ' + f'{difference // 30}' \
                                        f' {morph.parse("месяц")[0].make_agree_with_number(difference // 30).word}'
        difference -= 30 * (difference // 30)
    if difference:
        resp += ', ' if resp else ' ' + f'{difference} {morph.parse("день")[0].make_agree_with_number(difference).word}'
    return f'{resp}'


def save_proof_quest(project, file, user_id):
    data_session = db_session.create_session()
    path = f'static/app_files/all_projects/{str(project.id)}/{str(file.filename)}'
    file_check = data_session.query(Files).filter(Files.path == path).first()
    file.save(path)
    if file_check:
        return file_check.id
    file = Files(
        path=path,
        user=user_id,
        up_date=datetime.datetime.now()
    )
    data_session.add(file)
    data_session.flush()
    data_session.refresh(file)
    file_id = file.id
    data_session.commit()
    data_session.close()
    return file_id


def find_files_answer(file_id):
    data_session = db_session.create_session()
    file = data_session.query(Files).filter(Files.id == file_id).first()
    return {'id': file.id, 'path': file.path, 'user': file.user, 'up_date': file.up_date,
            'current_path': file.path[str(file.path).find('all_projects') + 13:].split('/')}


def file_tree(path):
    tree = []
    data_session = db_session.create_session()
    h = 1
    for i in os.listdir(path):
        if os.path.isfile(f'{path}/{i}'):
            file = data_session.query(Files).filter(Files.path == f'{path}/{i}').first()
            tree.append(
                {
                    'path': f'{path}/{i}',
                    'type': 'file',
                    'object': file if file else None,
                    'current_path': f'{path}/{i}'[str(file.path).find('all_projects') + 13:].split('/')
                }
            )
        else:
            tree.append(
                {
                    'id': h,
                    'name': i,
                    'path': f'{path}/{i}',
                    'type': 'folder',
                    'tree': file_tree(f'{path}/{i}')
                }
            )
            h += 1
    data_session.close()
    return tree


def delete_file_proof_data(file_proof, data_session):
    file = data_session.query(Files).filter(Files.id == file_proof.file).first()
    data_session.delete(file)


def delete_answer_data(answer, data_session):
    file_proofs = data_session.query(FileProof).filter(FileProof.answer == answer.id).all()
    list(map(lambda file: delete_file_proof_data(file, data_session), file_proofs))
    list(map(data_session.delete, file_proofs))


def delete_quest_data(quest, data_session):
    answers = data_session.query(Answer).filter(Answer.quest == quest.id).all()
    list(map(lambda answer: delete_answer_data(answer, data_session), answers))
    list(map(data_session.delete, answers))


def delete_project_data(project, data_session):
    staff = data_session.query(StaffProjects).filter(StaffProjects.project == project.id).all()
    list(map(data_session.delete, staff))
    if 'none_project' not in project.photo:
        os.remove(project.photo)
    quests = data_session.query(Quests).filter(Quests.project == project.id).all()
    list(map(lambda quest: delete_quest_data(quest, data_session), quests))
    list(map(data_session.delete, quests))
    list(map(data_session.delete,
             data_session.query(Files).filter(Files.path.contains(f'all_projects/{str(project.id)}/')).all()))
    shutil.rmtree(f'static/app_files/all_projects/{str(project.id)}')
    data_session.delete(project)
    data_session.commit()
