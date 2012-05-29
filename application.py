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
    return render_template('index.html', type='user' if 'user' in session else 'group')

@app.route('/login', methods=[ 'GET', 'POST' ])
def login():
    if request.method == 'GET':
        login_to_group = request.args.get('login_to_group', '') == '1'

        if 'user' in session or 'group' in session:
            return redirect(url_for('index'))

        return render_template('login.html', login_to_group=login_to_group)

    if request.method == 'POST':
        user = auth.login(request.form)

        success = False
        if isinstance(user, auth.User):
            success = True
            session['user'] = user

        elif isinstance(user, auth.Group):
            success = True
            session['group'] = user

        return redirect(request.args.get('next', '/')) if success else render_template('login.html', error=u'用户(用户组)名或密码错误，请重试')

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
    session.pop('user', None)
    session.pop('group', None)

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

@app.route('/file/share')
@login_required()
def list_share_file():
    user = session['user']

    if user.id == 1:
        abort(404)

    fs = files.get_user_shared_files(user.id)
    users = auth.get_users_dict()

    return render_template('files.html', files=fs, users=users, user=user, share_view=True)

@app.route('/group/files')
@login_required(only_group=True)
def list_group_files():
    group = session['group']

    fs = files.get_files_by_group(group.id)
    folders = files.get_folders_dict()
    users = auth.get_users_in_the_group(group.id)

    return render_template('files.html', files=fs, users=dict([[user.id, user] for user in users]), folders=folders, group_view=True)

FILE_BASE = os.sep.join([app.config.root_path, UPLOAD_DIR, ''])

@app.route('/file/upload', methods=['GET', 'POST'])
@login_required()
def upload_file():
    to_folder = request.args.get('to_folder', '')
    set_public_default = request.args.get('public_default', '') == '1'

    if re.search('^\d+$', to_folder) is None:
        to_folder = None

    if request.method == 'GET':
        return render_template('upload.html', to_folder=to_folder, set_public_default=set_public_default)

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
    user = None
    group = None

    if 'user' in session:
        user = session['user']
    elif 'group' in session:
        group = session['group']

    ff = files.download_file(file_id, user_id=user.id if user else None, group_id=group.id if group else None)

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

@app.route('/file/<int:file_id>/addto/folder', defaults={ 'folder_id': 0 })
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

@app.route('/file/search')
@login_required()
def search_files():
    if 'user' not in session:
        abort(404)

    query = request.args.get('q', None)
    if query is None:
        return redirect(request.referrer)

    is_own_file = request.args.get('is_own_file', '1') == '1'
    user = session['user']

    users = None
    if user.id == 1:
        # shared files are not enabled for superuser
        if is_own_file is False:
            abort(404)

        users = auth.get_users_dict()

    folders = None
    if is_own_file is False:
        users = auth.get_users_dict()
    elif user.id != 1:
        folders = files.get_folders_dict()

    fs = files.get_files([user.id] if user.id != 1 else None) if is_own_file else files.get_user_shared_files(user.id)
    fs = [ f for f in fs if f.name.find(query) >= 0 ]

    return render_template('files.html', files=fs, users=users, user=user, folders=folders, search_view=True, query=query)

@app.route('/folder/search')
@login_required()
def search_folders():
    if 'user' not in session:
        abort(404)

    query = request.args.get('q', None)
    if query is None:
        return redirect(request.referrer)

    user = session['user']

    folders = files.get_folders(user.id if user.id != 1 else None)
    folders = [ f for f in folders if f.name.find(query) >= 0 ]

    return render_template('folders.html', folders=folders, search_view=True, query=query)

if __name__ == '__main__':
    app.run()
