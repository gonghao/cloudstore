# -*- coding: UTF-8 -*-

from flask import Flask, render_template, request, redirect, abort, url_for, g, session, send_file
from flask.ext.mysql import MySQL

import os, sys, re, auth, files, filters
from decorators import login_required

# Encoding Hack
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except e:
    pass

# Configuration
DEBUG = True
MYSQL_DATABASE_USER = 'root'
MYSQL_DATABASE_PASSWORD = '123456'
MYSQL_DATABASE_DB = 'cloudstore'
UPLOAD_DIR = 'uploads'

app = Flask(__name__)
app.secret_key = '\x9b@\t\x04x\x05b( \xb7\r\xf2\xe6\xa7\x0c\x95\x99\x9a\xe1\x89\x0c6\xb2\xbb'
app.config.from_object(__name__)
app.config.from_envvar('CLOUDSTORE_SETTINGS', silent=True)

# custom filters
app.jinja_env.filters['datetimeformat'] = filters.datetimeformat

mysql = MySQL(app)

@app.before_request
def before_request():
    g.db = mysql.get_db()

@app.route('/')
@login_required()
def index():
    return render_template('index.html')

@app.route('/login', methods=[ 'GET', 'POST' ])
def login():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('index'))

        return render_template('login.html')

    if request.method == 'POST':
        user = auth.login(request.form)

        if (isinstance(user, auth.User)):
            session['user'] = user

            return redirect(request.args.get('next', '/'))

        return render_template('login.html', error=u'用户名或密码错误，请重试')

@app.route('/register', methods=[ 'GET', 'POST' ])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        user = auth.register(request.form)
        if isinstance(user, auth.User):
            session['user'] = user
            return redirect(url_for('index'))
        else:
            return render_template('register.html', errors=user)

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect(url_for('login'))

@app.route('/admin/users', methods=[ 'GET', 'POST' ])
@login_required(only_superuser=True)
def admin_users():
    if request.method == 'GET':
        users = auth.get_users(exclude=[1])
        groups = auth.get_groups_dict()

        return render_template('users.html', users=users, groups=groups)

    if request.method == 'POST':
        auth.set_users_admin(request.form)

        return redirect(url_for('admin_users'))

@app.route('/admin/groups')
@login_required(only_superuser=True)
def admin_groups():
    groups = auth.get_groups_with_members()

    return render_template('groups.html', groups=groups)

@app.route('/admin/group/add', methods=[ 'GET', 'POST' ])
@login_required(only_superuser=True)
def admin_group_add():
    if request.method == 'GET':
        users = auth.get_users_not_in_group()
        return render_template('add_group.html', users=users)

    if request.method == 'POST':
        group = auth.add_group(request.form)

        if isinstance(group, auth.Group):
            return redirect(url_for('admin_groups'))

        users = auth.get_users_not_in_group()
        return render_template('add_group.html', users=users, errors=group)

@app.route('/admin/group/<int:group_id>', methods=[ 'GET', 'POST' ])
@login_required()
def admin_group(group_id):
    user = session['user']

    if user.id != 1 and ( user.groupid != group_id or not user.is_admin ):
        abort(404)

    if request.method == 'GET':
        group = auth.get_groups_with_members(include=[group_id])[0]
        users = auth.get_users_not_in_group()

        group.members = [ member for member in group.members if member.id != user.id ]
        ids = [ str(member.id) for member in group.members + users if member.id != user.id ]

        return render_template('group.html', group=group, users=users, ids=':'.join(ids))

    if request.method == 'POST':
        auth.update_group_members(group_id, request.form)

        return redirect(url_for('admin_group', group_id=group_id))

@app.route('/file/own')
@login_required()
def list_file():
    user = session['user']

    users = None
    if user.id == 1:
        users = auth.get_users_dict()

    fs = files.get_files([user.id] if user.id != 1 else None)
    folders = files.get_folders_dict()

    return render_template('files.html', files=fs, users=users, user=user, folders=folders)

FILE_BASE = os.sep.join([app.config.root_path, UPLOAD_DIR, ''])

@app.route('/file/upload', methods=['GET', 'POST'])
@login_required()
def upload_file():
    to_folder = request.args.get('to_folder', '')

    if re.search('^\d+$', to_folder) is None:
        to_folder = None

    if request.method == 'GET':
        return render_template('upload.html', to_folder=to_folder)

    if request.method == 'POST':
        user = session['user']
        f = files.upload_file(FILE_BASE, request, user.id)

        if to_folder:
            files.add_file_to_folder(f.id, to_folder, user.id)

        return redirect(url_for('list_file') if to_folder is None else url_for('list_folder_files', folder_id=to_folder))

@app.route('/file/<int:file_id>', methods=['GET', 'POST'])
@login_required()
def edit_file(file_id):
    if request.method == 'GET':
        f = files.get_file_by_id(file_id)
        folders = files.get_folders(f.folderid) if f.folderid else []

        return render_template('file.html', file=f, folders=folders)

    if request.method == 'POST':
        errors = files.edit_file(file_id, request.form)

        if errors:
            f = files.get_file_by_id(file_id)
            folders = files.get_folders(f.folderid) if f.folderid else []

            return render_template('file.html', file=f, folders=folders)

        referrer = request.args.get('referrer', url_for('list_file'))

        return redirect(referrer)

@app.route('/file/<int:file_id>/download')
@login_required()
def download_file(file_id):
    user = session['user']

    ff = files.download_file(file_id, user)

    if ff:
        return send_file('%s%s' % (FILE_BASE, ff.location), mimetype=ff.type, as_attachment=True, attachment_filename=ff.name)

    abort(404)

@app.route('/folder/add', methods=['GET', 'POST'])
@login_required()
def add_folder():
    user = session['user']

    # superuser cannot create folder
    if user.id == 1:
        abort(404)

    next = request.args.get('next')

    if request.method == 'GET':
        return render_template('add_folder.html', next_page=next)

    if request.method == 'POST':
        errors = files.add_folder(request.form, user.id)

        if errors:
            return render_template('add_folder.html', errors=errors, next_page=next)

        return redirect(next)

@app.route('/file/<int:file_id>/addto/folder', defaults={'folder_id': 0})
@app.route('/file/<int:file_id>/addto/folder/<int:folder_id>')
@login_required()
def add_file_to_folder(file_id, folder_id):
    user = session['user']

    # superuser can not add file to folder
    if user.id == 1:
        abort(404)

    # add file to folder
    if folder_id:
        files.add_file_to_folder(file_id, folder_id, user.id)

        return redirect(url_for('list_file'))

    folders = files.get_folders(user.id if user.id != 1 else None)

    return render_template('folders.html', folders=folders, file_id=file_id, type='addto')

@app.route('/folder')
@login_required()
def list_folder():
    user = session['user']

    folders = files.get_folders(user.id if user.id != 1 else None)

    return render_template('folders.html', folders=folders)

@app.route('/folder/<int:folder_id>')
@login_required()
def list_folder_files(folder_id):
    user = session['user']

    fs = files.get_files_by_folder(folder_id)
    folder = files.get_folder_by_id(folder_id)

    users = None
    if user.id == 1:
        users = auth.get_users_dict()

    return render_template('files.html', files=fs, users=users, user=user, folder=folder)

if __name__ == '__main__':
    app.run()
