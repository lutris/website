import re
import os
import datetime

from fabric import Connection
from invoke import task


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


def activate(c):
    return c.prefix(
        'export DJANGO_SETTINGS_MODULE=%s && '
        '. %s/bin/envvars && '
        '. %s/bin/activate'
        % (env.settings_module, env.root, env.root)
    )


@task
def touch_wsgi(c):
    """Touch wsgi file to trigger reload."""
    conf_dir = os.path.join(env.code_root, 'config')
    with c.cd(conf_dir):
        c.run('touch lutrisweb.wsgi')


@task
def nginx_reload(c):
    """ reload Nginx on remote host """
    c.sudo('service nginx reload', shell=False)


@task
def supervisor_restart(c):
    """ Reload Supervisor service """
    c.sudo('service supervisor restart', shell=False)


@task
def test(c):
    c.run("python manage.py test games")
    c.run("python manage.py test accounts")


@task
def initial_setup(c):
    """Setup virtualenv"""
    c.run("mkdir -p %s" % env.root)
    with c.cd(env.root):
        c.run('virtualenv .')
        c.run('git clone %s' % LUTRIS_REMOTE)


@task
def pip_list(c):
    with c.cd(env.code_root):
        with activate(c):
            c.run('pip list')


@task
def requirements(c):
    with c.cd(env.code_root):
        with activate(c):
            c.run(
                'pip install -r config/requirements/%s.pip --exists-action=s' % env.environment
            )


def update_celery(c):
    tempfile = "/tmp/%(project)s-celery.conf" % env
    c.local('cp config/lutrisweb-celery.conf ' + tempfile)
    c.local('sed -i s#%%ROOT%%#%(root)s#g ' % env + tempfile)
    c.local('sed -i s/%%DOMAIN%%/%(domain)s/g ' % env + tempfile)
    c.put(tempfile, '%(root)s' % env)
    c.sudo(
        'cp %(root)s/lutrisweb-celery.conf /etc/supervisor/conf.d/' % env,
        shell=False
    )


@task
def copy_local_settings(c):
    c.put('config/local_settings_%(environment)s.py' % env, env.code_root)
    with c.cd(env.code_root):
        c.run('mv local_settings_%(environment)s.py local_settings_template.py' % env)


def migrate(c):
    with c.cd(env.code_root):
        with activate(c):
            c.run("./manage.py migrate")


def clone(c):
    with c.cd(env.root):
        c.run("git clone /srv/git/lutrisweb")


def pull(c):
    with c.cd(env.code_root):
        c.run("git pull")


def npm(c):
    with c.cd(env.code_root):
        c.run("npm install -U bower")
        c.run("npm install")


def bower(c):
    with c.cd(env.code_root):
        c.run("bower install")


def grunt(c):
    with c.cd(env.code_root):
        c.run("grunt")


def collect_static(c):
    c.require('code_root', provided_by=('stating', 'production'))
    with c.cd(env.code_root):
        with activate(c):
            c.run('./manage.py collectstatic --noinput')


def fix_perms(c, user='www-data', group=None):
    if not group:
        group = env.user
    with c.cd(env.code_root):
        c.sudo('chown -R %s:%s static' % (user, group))
        c.sudo('chmod -R ug+w static')
        c.sudo('chown -R %s:%s media' % (user, group))
        c.sudo('chmod -R ug+w media')


def clean(c):
    with c.cd(env.code_root):
        c.run('find . -name "*.pyc" -delete')


def configtest(c):
    c.sudo("service nginx configtest")


def authorize(c, ip):
    with c.cd(env.code_root):
        with activate(c):
            c.run('./manage.py authorize %s' % ip)


def docs(c):
    with c.cd(env.code_root):
        c.run("make client")
        with activate(c):
            c.run("make docs")


def sql_dump(c):
    with c.cd(env.sql_backup_dir):
        backup_file = "lutris-{}.tar".format(
            datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
        )
        c.run('pg_dump --format=tar lutris > {}'.format(backup_file))
        c.run('gzip {}'.format(backup_file))
        backup_file += '.gz'
        get(backup_file, backup_file)


def sql_restore(c):
    """Restore a SQL DB dump to the local database"""
    db_dump = None
    for filename in os.listdir('.'):
        if re.match('lutris-.*\.tar.gz', filename):
            db_dump = filename
            break
    if not db_dump:
        print("No SQL dump found")
        return
    c.local('gunzip {}'.format(db_dump))
    db_dump = db_dump[:-3]
    c.local('pg_restore --clean --dbname=lutris {}'.format(db_dump))
    c.local('rm {}'.format(db_dump))


@task
def deploy(c):
    """Run a full deploy"""
    pull(c)
    bower(c)
    grunt(c)
    requirements(c)
    collect_static(c)
    migrate(c)
    docs(c)
    nginx_reload(c)
    update_celery(c)
    supervisor_restart(c)


@task
def pythonfix(c):
    """Apply a fix fro Python code only (no migration, no frontend change)"""
    pull(c)
    supervisor_restart(c)
