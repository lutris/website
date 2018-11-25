import re
import os
import datetime

from invoke import task


LUTRIS_REMOTE = 'git@github.com:lutris/website.git'
DJANGO_SETTINGS_MODULE = 'lutrisweb.settings.production'
NVM_DIR = '/home/django/.nvm'
PRODUCTION_IP = '62.210.136.153'

def get_config(context):
    try:
        host = context.host
    except AttributeError:
        host = 'localhost'

    if host == PRODUCTION_IP:
        host = 'lutris.net'

    if host == 'lutris.net':
        env = 'production'
    elif host == 'dev.lutris.net':
        env = 'staging'
    else:
        env = 'local'
    code_root = None
    if env == 'production':
        root = os.path.join('/srv/lutris')
        git_branch = 'master'
    elif env == 'staging':
        root = os.path.join('/srv/lutris_staging')
        git_branch = 'master'
    else:
        root = os.path.dirname(os.path.abspath(__file__))
        code_root = root
        git_branch = ''
    code_root = code_root or os.path.join(root, host)
    return {
        'root': root,
        'code_root': code_root,
        'vue_root': os.path.join(code_root, 'frontend/vue'),
        'domain': host,
        'git_branch': git_branch,
        'env': env
    }


def activate(c):
    config = get_config(c)
    root = config['root']
    return c.prefix(
        'export DJANGO_SETTINGS_MODULE=%s && '
        '. %s/bin/envvars && '
        '. %s/bin/activate'
        % (DJANGO_SETTINGS_MODULE, root, root)
    )


def nvm(c):
    return c.prefix('. %s/nvm.sh && nvm use default' % NVM_DIR)


@task
def touch_wsgi(c):
    """Touch wsgi file to trigger reload."""
    config = get_config(c)
    conf_dir = os.path.join(config['code_root'], 'config')
    with c.cd(conf_dir):
        c.run('touch lutrisweb.wsgi')


@task
def nginx_reload(c):
    """ reload Nginx on remote host """
    c.sudo('service nginx reload')


@task
def supervisor_restart(c):
    """ Reload Supervisor service """
    c.sudo('service supervisor restart')


@task
def test(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run("python manage.py test accounts")


@task
def initial_setup(c):
    """Setup virtualenv"""
    config = get_config(c)
    c.sudo("apt install -y python3-venv")
    c.sudo("mkdir -p %s" % config['root'])
    c.sudo("chown %s:%s %s" % (c.user, c.user, config['root']))
    with c.cd(config['root']):
        c.run('python3 -m venv .')
        c.run('git clone %s %s' % (LUTRIS_REMOTE, config['domain']))


@task
def pip_list(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run('pip list')


@task
def requirements(c, environment='production'):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run('pip install -U pip')
            c.run('pip install -U wheel')
            c.run(
                'pip install -r config/requirements/%s.pip --exists-action=s' % environment
            )


@task
def setup_scripts(c):
    config = get_config(c)
    c.put('config/celery_start.sh', remote='%(root)s/bin/celery_start.sh' % config)
    c.put('config/gunicorn_start.sh', remote='%(root)s/bin/gunicorn_start.sh' % config)


@task
def supervisor_setup(c):
    config = get_config(c)
    config_filename = "lutris-supervisor.conf"
    temppath = "/tmp/" + config_filename
    c.local('cp config/%s ' % config_filename + temppath)
    c.local('sed -i s#%%ROOT%%#%(root)s#g ' % config + temppath)
    c.local('sed -i s/%%DOMAIN%%/%(domain)s/g ' % config + temppath)
    c.put(temppath, remote=temppath)
    c.sudo(
        'mv %s /etc/supervisor/conf.d/%s.conf' %
        (temppath, config['domain'])
    )


@task
def migrate(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run("./manage.py migrate")


@task
def pull(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        c.run("git checkout %s" % config['git_branch'])
        c.run("git pull")


@task
def npm(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        with nvm(c):
            c.run("npm install")


@task
def bower(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        c.run("bower install")
        c.run("bower update")


@task
def grunt(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        c.run("grunt")


@task
def build_vue(c):
    """Build a production bundle of the Vue project"""
    config = get_config(c)
    with c.cd(config['vue_root']):
        with nvm(c):
            c.run("npm install")
            c.run("NODE_ENV=production npm run build:issues")


@task
def collect_static(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run('./manage.py collectstatic --noinput')


@task
def fix_perms(c, user='www-data', group=None):
    if not group:
        group = user
    config = get_config(c)
    with c.cd(config['code_root']):
        c.sudo('chown -R %s:%s static' % (user, group))
        c.sudo('chmod -R ug+w static')
        c.sudo('chown -R %s:%s media' % (user, group))
        c.sudo('chmod -R ug+w media')


@task
def clean(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        c.run('py3clean .')


@task
def authorize(c, ip):
    config = get_config(c)
    with c.cd(config['code_root']):
        with activate(c):
            c.run('./manage.py authorize %s' % ip)


@task
def docs(c):
    config = get_config(c)
    with c.cd(config['code_root']):
        c.run("make client")
        with activate(c):
            c.run("make docs")


@task
def sql_dump(c):
    sql_backup_dir = '/srv/backup/sql/'
    with c.cd(sql_backup_dir):
        backup_file = "lutris-{}.tar".format(
            datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
        )
        c.run('pg_dump --format=tar lutris > {}'.format(backup_file))
        c.run('gzip {}'.format(backup_file))
        backup_file += '.gz'
        c.get(backup_file, backup_file)


@task
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
    requirements(c)
    # bower(c)  # Bower install is disabled, some packages are broken
    grunt(c)
    build_vue(c)
    collect_static(c)
    migrate(c)
    docs(c)
    supervisor_setup(c)
    supervisor_restart(c)
    nginx_reload(c)


@task
def pythonfix(c):
    """Apply a fix for Python code only (no frontend change)"""
    pull(c)
    migrate(c)
    supervisor_restart(c)
