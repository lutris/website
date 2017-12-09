import re
import os
import datetime

from fabric.api import run, env, local, sudo, put, require, cd
from fabric.operations import get
from fabric.context_managers import prefix


LUTRIS_REMOTE = 'git@github.com:lutris/website.git'

env.project = 'lutrisweb'
env.home = '/srv'
env.name = 'lutris'
env.settings_module = 'lutrisweb.settings.production'


def _setup_path():
    env.root = os.path.join(env.home, env.name)
    env.code_root = os.path.join(env.root, env.domain)


def staging():
    """ use staging environment on remote host"""
    env.user = 'django'
    env.environment = 'staging'
    env.domain = 'dev.lutris.net'
    env.port = '22101'
    env.hosts = [env.domain + ':' + env.port]
    _setup_path()


def production():
    """ use production environment on remote host"""
    env.sql_backup_dir = '/srv/backup/sql/'
    env.user = 'django'
    env.environment = 'production'
    env.domain = 'lutris.net'
    env.port = '22101'
    env.hosts = [env.domain]
    _setup_path()


def activate():
    return prefix(
        'export DJANGO_SETTINGS_MODULE=%s && '
        '. %s/bin/envvars && '
        '. %s/bin/activate'
        % (env.settings_module, env.root, env.root)
    )


def touch_wsgi():
    """Touch wsgi file to trigger reload."""
    conf_dir = os.path.join(env.code_root, 'config')
    with cd(conf_dir):
        run('touch lutrisweb.wsgi')


def nginx_reload():
    """ reload Nginx on remote host """
    sudo('service nginx reload', shell=False)


def supervisor_restart():
    """ Reload Supervisor service """
    sudo('service supervisor restart', shell=False)


def test():
    local("python manage.py test games")
    local("python manage.py test accounts")


def initial_setup():
    """Setup virtualenv"""
    run("mkdir -p %s" % env.root)
    with cd(env.root):
        run('virtualenv .')
        run('git clone %s' % LUTRIS_REMOTE)


def pip_list():
    require('environment', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with activate():
            run('pip list')

def requirements():
    require('environment', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with activate():
            run('pip install -r config/requirements/%s.pip --exists-action=s'
                % env.environment)


def update_celery():
    tempfile = "/tmp/%(project)s-celery.conf" % env
    local('cp config/lutrisweb-celery.conf ' + tempfile)
    local('sed -i s#%%ROOT%%#%(root)s#g ' % env + tempfile)
    local('sed -i s/%%DOMAIN%%/%(domain)s/g ' % env + tempfile)
    put(tempfile, '%(root)s' % env)
    sudo('cp %(root)s/lutrisweb-celery.conf ' % env
         + '/etc/supervisor/conf.d/', shell=False)


def copy_local_settings():
    require('code_root', provided_by=('staging', 'production'))
    put('config/local_settings_%(environment)s.py' % env, env.code_root)
    with cd(env.code_root):
        run('mv local_settings_%(environment)s.py local_settings_template.py'
            % env)


def migrate():
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        with activate():
            run("./manage.py migrate")


def clone():
    with cd(env.root):
        run("git clone /srv/git/lutrisweb")


def pull():
    with cd(env.code_root):
        run("git pull")


def npm():
    with cd(env.code_root):
        run("npm install -U bower")
        run("npm install")


def bower():
    with cd(env.code_root):
        run("bower install")


def grunt():
    with cd(env.code_root):
        run("grunt")


def collect_static():
    require('code_root', provided_by=('stating', 'production'))
    with cd(env.code_root):
        with activate():
            run('./manage.py collectstatic --noinput')


def fix_perms(user='www-data', group=None):
    if not group:
        group = env.user
    with cd(env.code_root):
        sudo('chown -R %s:%s static' % (user, group))
        sudo('chmod -R ug+w static')
        sudo('chown -R %s:%s media' % (user, group))
        sudo('chmod -R ug+w media')


def clean():
    with cd(env.code_root):
        run('find . -name "*.pyc" -delete')


def configtest():
    sudo("service nginx configtest")


def authorize(ip):
    with cd(env.code_root):
        with activate():
            run('./manage.py authorize %s' % ip)


def docs():
    with cd(env.code_root):
        run("make client")
        with activate():
            run("make docs")


def sql_dump():
    with cd(env.sql_backup_dir):
        backup_file = "lutris-{}.tar".format(
            datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
        )
        run('pg_dump --format=tar lutris > {}'.format(backup_file))
        run('gzip {}'.format(backup_file))
        backup_file += '.gz'
        get(backup_file, backup_file)


def sql_restore():
    db_dump = None
    for f in os.listdir('.'):
        if re.match('lutris-.*\.tar.gz', f):
            db_dump = f
            break
    if not db_dump:
        print("No SQL dump found")
        return
    local('gunzip {}'.format(db_dump))
    db_dump = db_dump[:-3]
    local('pg_restore --clean --dbname=lutris {}'.format(db_dump))
    local('rm {}'.format(db_dump))


def deploy():
    pull()
    bower()
    grunt()
    requirements()
    collect_static()
    migrate()
    docs()
    nginx_reload()
    update_celery()
    supervisor_restart()


def pythonfix():
    """Apply a fix fro Python code only (no migration, no frontend change)"""
    pull()
    supervisor_restart()
