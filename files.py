# -*- coding: utf-8 -*-

from time import time
from flask import g
from wtforms import Form, TextField, validators

class File(object):
    def __init__(self, file_dict):
        self.id = file_dict['fileid']
        self.name = file_dict['filename']
        self.userid = file_dict['userid']
        self.is_private = file_dict['fileident'] == '1'
        self.upload_datetime = file_dict['upload']
        self.modify_datetime = file_dict['modify']
        self.count = file_dict['count']
        self.location = file_dict['location']
        self.type = file_dict['type']
        self.folderid = file_dict['folderid']

class Folder(object):
    def __init__(self, folderid, foldername, userid):
        self.id = folderid
        self.name = foldername
        self.userid = userid

class EditFileForm(Form):
    filename = TextField('filename', [
        validators.Length(min=1, max=200, message=u'文件名长度必须介于%(min)d与%(max)d之间')
    ])

class AddFolderForm(Form):
    foldername = TextField('foldername', [
        validators.Length(min=1, max=20, message=u'文件夹名长度必须介于%(min)d与%(max)d之间')
    ])

def get_files(user_id=None):
    db = g.db

    where_sql = ''
    if user_id:
        where_sql = ' OR '.join([ 'userid = %s' % id for id in user_id ])

    sql = 'SELECT * FROM `File`%s' % (' WHERE %s' % where_sql if where_sql else '')
    db.query(sql)

    data = db.store_result()

    return [File(f) for f in data.fetch_row(maxrows=0, how=1)]

def get_file_by_id(file_id):
    db = g.db

    sql = 'SELECT * FROM `File` WHERE `fileid` = "%s"' % file_id
    db.query(sql)
    data = db.store_result()

    return File(data.fetch_row(how=1)[0])

def get_files_by_folder(folder_id):
    db = g.db

    sql = 'SELECT * FROM `File` WHERE `folderid` = "%s"' % folder_id
    db.query(sql)

    data = db.store_result()

    return [File(f) for f in data.fetch_row(maxrows=0, how=1)]

def get_folders(user_id=None):
    db = g.db

    sql = 'SELECT * FROM `Folder`'

    if user_id:
        sql += ' WHERE `userid` = "%s"' % user_id
    db.query(sql)

    data = db.store_result()

    return [Folder(**f) for f in data.fetch_row(maxrows=0, how=1)]

def get_folders_dict(user_id=None):
    folders = get_folders(user_id)

    return dict([ [folder.id, folder] for folder in folders ])

def get_folder_by_id(folder_id):
    db = g.db

    sql = 'SELECT * FROM `Folder` WHERE `folderid` = "%s"' % folder_id
    db.query(sql)
    data = db.store_result()

    return Folder(**data.fetch_row(how=1)[0])

FILE_NAME = '{userid}_{fileid}_{filename}'

def upload_file(path, request, user_id):
    db = g.db

    f = request.files['filename']
    fn = f.filename
    fileident = request.form['private']
    now = int(time())

    sql = ('''
        INSERT INTO `File` (`filename`, `userid`, `fileident`, `upload`, `modify`, `type`)
        VALUES ('%s', '%s', '%s', '%s', '%s', '%s')
    ''') % (fn, user_id, fileident, now, now, f.mimetype)

    db.query(sql)
    db.commit()

    sql = ('''
        SELECT * FROM `File` WHERE `filename` = '%s' and `userid` = '%s' and `fileident` = '%s' and `upload` = '%s'
        and `modify` = '%s' and `type` = '%s'
    ''' % (fn, user_id, fileident, now, now, f.mimetype))

    db.query(sql)
    data = db.store_result()
    ff = File(data.fetch_row(how=1)[0])
    ff.location = FILE_NAME.format(userid=user_id, fileid=ff.id, filename=ff.name)

    sql = 'UPDATE `File` SET `location`="%s" WHERE `fileid` = "%d"' % (ff.location, ff.id)

    db.query(sql)
    db.commit()

    path = '%s%s' % (path, ff.location)
    f.save(path)

    return ff

def download_file(file_id, user):
    db = g.db

    sql = 'SELECT * FROM `File` WHERE `fileid` = "%s"' % file_id

    if user.id != 1:
        sql += ' AND `userid` = "%s"' % user.id

    db.query(sql)
    data = db.store_result()

    if data.num_rows() > 0:
        data = data.fetch_row(how=1)[0]

        sql = 'UPDATE `File` SET `count` = `count` + 1 WHERE `fileid` = "%s"' % file_id
        db.query(sql)
        db.commit()

        return File(data)

    return None

def edit_file(file_id, form):
    db = g.db

    fileident = form['private']
    folderid = form['folderid']
    form = EditFileForm(form)

    if form.validate():
        filename = form.data['filename'].strip()
        sql = ( '''UPDATE `File` SET `filename` = "%s", `fileident` = %s, folderid = %s, modify = "%s"
                WHERE `fileid` = %s'''
                % (filename, fileident, folderid if int(folderid) > 0 else 'null', int(time()), file_id) )

        db.query(sql)
        db.commit()

        return None

    return form.errors

def add_folder(form, user_id):
    form = AddFolderForm(form)
    foldername = form.data['foldername'].strip()

    if form.validate():
        db = g.db

        sql = 'SELECT * FROM `Folder` WHERE `userid` = "%s" AND `foldername` = "%s"' % (user_id, foldername)

        db.query(sql)
        data = db.store_result()

        if data.num_rows() > 0:
            return {
                'foldername': [u'文件夹已经存在，请重新输入一个文件夹名']
            }

        sql = 'INSERT INTO `Folder` (`foldername`, `userid`) VALUES ("%s", "%s")' % (foldername, user_id)
        db.query(sql)
        db.commit()

        return None

    return form.errors

def add_file_to_folder(file_id, folder_id, user_id):
    db = g.db

    sql = 'UPDATE `File` SET `folderid` = "%s" WHERE `fileid` = "%s" and `userid` = "%s"' % (folder_id, file_id, user_id)
    db.query(sql)
    db.commit()
