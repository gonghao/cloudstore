# -*- coding: UTF-8 -*-

from hashlib import md5
from flask import g
from wtforms import Form, TextField, PasswordField, validators

class RegistrationForm(Form):
    username = TextField('username', [ validators.Length(min=4, max=20, message=u'用户名长度必须介于%(min)d与%(max)d之间') ])
    password = PasswordField('password', [
        validators.Required(message=u'必填，不能为空'),
        validators.Length(min=6, message=u'密码最少需要%(min)d位'),
        validators.EqualTo('re_password', message=u'两次密码输入必须保持一致')
    ])
    re_password = PasswordField('re_password', [
        validators.Required(message=u'必填，不能为空'),
        validators.Length(min=6, message=u'密码最少需要%(min)d位'),
    ])

class AddGroupForm(Form):
    groupname = TextField('groupname', [
        validators.Length(min=4, max=20, message=u'用户组名长度必须介于%(min)d与%(max)d之间')
    ])
    password = PasswordField('password', [
        validators.Required(message=u'必填，不能为空'),
        validators.Length(min=6, message=u'密码最少需要%(min)d位'),
        validators.EqualTo('re_password', message=u'两次密码输入必须保持一致')
    ])
    re_password = PasswordField('re_password', [
        validators.Required(message=u'必填，不能为空'),
        validators.Length(min=6, message=u'密码最少需要%(min)d位'),
    ])

class User(object):
    def __init__(self, user_dict):
        self.id = user_dict['userid']
        self.name = user_dict['username']
        self.groupid = user_dict['groupid']
        self.is_admin = user_dict['identity'] == '1'

class Group(object):
    def __init__(self, group_dict):
        self.id = group_dict['groupid']
        self.name = group_dict['groupname']

def register(form):
    form = RegistrationForm(form)
    db = g.db

    if form.validate():
        db.query(
            '''
            SELECT * FROM %s WHERE username = '%s'
            '''
            % ('User', form.data['username'])
        )
        data = db.store_result()

        if data.num_rows() > 0:
            # return errors
            return {
                'username': [ u'该用户名已经存在，请重新输入' ]
            }

        db.query(
            '''
            INSERT INTO %s (username, password) VALUES ('%s', '%s')
            '''
            % ('User', form.data['username'].strip(), md5(form.data['password']).hexdigest())
        )

        db.commit()

        db.query(
            '''
            SELECT * FROM %s WHERE username='%s'
            '''
            % ('User', form.data['username'].strip())
        )

        data = db.store_result()

        return User(data.fetch_row(how=1)[0])

    return form.errors

def login(form):
    db = g.db

    name = form['name'].strip()
    password = md5(form['password']).hexdigest()
    login_type = form['type']

    # try to login with user
    if login_type == 'user':

        db.query(
            '''
            SELECT * FROM `User` WHERE username = '%s' and password = '%s'
            '''
            % (name, password)
        )

        data = db.store_result()

        if data.num_rows() > 0:
            user = data.fetch_row(how=1)[0]
            return User(user)

    # try to login with group
    elif login_type == 'group':

        db.query(
            '''
            SELECT * FROM `Group` WHERE `groupname` = "%s" and `grouppassword` = "%s"
            '''
            % (name, password)
        )

        data = db.store_result()

        if data.num_rows() > 0:
            group = data.fetch_row(how=1)[0]
            return Group(group)

def set_users_admin(form):
    db = g.db
    items = form.items()

    set_to_null = [ name.split(':')[0] for name, value in items if value == '0' ]
    set_to_admin = [ name.split(':')[0] for name, value in items if value == '1' ]

    where_sql = ' OR '.join([ 'userid = %s' % id for id in set_to_null ])
    db.query('UPDATE `User` SET identity="0" WHERE %s' % where_sql)

    where_sql = ' OR '.join([ 'userid = %s' % id for id in set_to_admin ])
    db.query('UPDATE `User` SET identity="1" WHERE %s' % where_sql)

    db.commit()

def get_users(include=None, exclude=None):
    db = g.db

    where_sql = ''

    if include is not None:
        where_sql = ' OR '.join([ 'userid = %s' % id for id in include ])

    elif exclude is not None:
        where_sql = ' AND '.join([ 'userid != %s' % id for id in exclude ])

    sql = ( 'SELECT * FROM `User`%s ORDER BY userid ASC' % ( (' WHERE %s' % where_sql ) if where_sql else '' ) )

    db.query(sql)
    datas = db.store_result()

    return [ User(data) for data in datas.fetch_row(maxrows=0, how=1) ]

def get_users_dict(include=None, exclude=None):
    users = get_users(include, exclude)

    return dict([[user.id, user] for user in users])

def get_users_in_group():
    db = g.db

    db.query( 'SELECT * FROM `User` WHERE groupid IS NOT NULL AND userid != 1' )

    datas = db.store_result()

    return [ User(data) for data in datas.fetch_row(maxrows=0, how=1) ]

def get_users_not_in_group():
    db = g.db

    db.query( 'SELECT * FROM `User` WHERE groupid IS NULL AND userid != 1' )

    datas = db.store_result()

    return [ User(data) for data in datas.fetch_row(maxrows=0, how=1) ]

def get_users_in_the_group(groupid):
    db = g.db

    db.query( 'SELECT * FROM `User` WHERE `groupid` = "%s"' % groupid )

    datas = db.store_result()

    return [ User(data) for data in datas.fetch_row(maxrows=0, how=1) ]

def get_groups(include=None, exclude=None):
    db = g.db

    where_sql = ''

    if include is not None:
        where_sql = ' OR '.join([ 'groupid = %s' % id for id in include ])

    elif exclude is not None:
        where_sql = ' AND '.join([ 'groupid != %s' % id for id in exclude ])

    sql = ( 'SELECT * FROM `Group`%s ORDER BY groupid ASC' % ( (' WHERE %s' % where_sql ) if where_sql else '' ) )

    db.query(sql)
    datas = db.store_result()

    return [ Group(data) for data in datas.fetch_row(maxrows=0, how=1) ]

def get_groups_with_members(include=None, exclude=None):
    groups = get_groups(include, exclude)
    users_in_group = get_users_in_group()

    for group in groups:
        group.members = [ user for user in users_in_group if user.groupid == group.id ]

    return groups

def get_groups_dict(include=None, exclude=None):
    groups = get_groups(include, exclude)

    ret = {}

    for group in groups:
        ret[group.id] = group

    return ret

def add_group(form):
    members = form.getlist('members')
    form = AddGroupForm(form)

    if form.validate():
        db = g.db
        name = form.data['groupname'].strip()

        db.query( 'SELECT * FROM `Group` WHERE groupname = "%s"' % name )

        data = db.store_result()

        if data.num_rows() > 0:
            return {
                'groupname': [ u'用户组名已经存在' ]
            }

        db.query( 'INSERT INTO `Group` (`groupname`, `grouppassword`) VALUES ("%s", "%s")' % (name, md5(form.data['password']).hexdigest()) )

        db.commit()

        db.query( 'SELECT * FROM `Group` WHERE groupname = "%s"' % name )

        data = db.store_result()

        group = Group(data.fetch_row(how=1)[0])

        for user in members:
            db.query('UPDATE `User` SET groupid="%s" WHERE userid = "%s"' % (group.id, user))

        db.commit()

        return group

    return form.errors

def update_group_members(group_id, form):
    all_users = form['all_user_ids'].split(':')
    members = form.getlist('members')

    db = g.db

    # clean data
    where_sql = ' OR '.join([ 'userid = %s' % id for id in all_users ])

    db.query('UPDATE `User` SET groupid=null WHERE %s' % where_sql)

    # update data
    where_sql = ' OR '.join([ 'userid = %s' % id for id in members ])

    db.query('UPDATE `User` SET groupid="%s" WHERE %s' % (group_id, where_sql))

    db.commit()
