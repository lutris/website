import os
from fabric.api import run, require, env,  cd, put
from fabric.contrib.project import rsync_project
from fabric import utils
from fabric.contrib import console

RSYNC_EXCLUDE = (
    '.bzr',
    '.bzrignore',
    '*.pyc',
    '*.example',
    '*.db',
    'media/admin',
    'media/attachments',
    'local_settings.py',
    'fabfile.py',
    'bootstrap.py',
)

env.home = '/srv/django/'
env.project = 'lutrisweb'

def _setup_path():
    env.root = os.path.join(env.home, env.environment)
    env.code_root = os.path.join(env.root, env.project)
    env.virtualenv_root = os.path.join(env.root, 'island_env')
    env.settings = '%(project)s.settings_%(environment)s' % env

def staging():
    """ use staging environment on remote host"""
    env.user = 'strider'
    env.environment = 'staging'
    env.hosts = ['dev.lutris.net']
    _setup_path()

def production():
    """ use production environment on remote host"""
    utils.abort('Production deployment not yet implemented.')

def apache_reload():
    """ reload Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    run('sudo /etc/init.d/apache2 reload')

def apache_restart():
    """ restart Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    run('sudo /etc/init.d/apache2 restart')

def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=('staging', 'production'))
    run('mkdir -p %(root)s' % env)
    run('mkdir -p %s' % os.path.join(env.home, 'www', 'log'))
    create_virtualenv()
    deploy()
    update_requirements()

def syncdb():
    with cd(env.code_root):
        run("./manage.py syncdb")

def touch():
    """ touch wsgi file to trigger reload """
    require('code_root', provided_by=('staging', 'production'))
    apache_dir = os.path.join(env.code_root, 'apache')
    with cd(apache_dir):
        run('touch %s.wsgi' % env.environment)

def create_virtualenv():
    """ setup virtualenv on remote host """
    require('virtualenv_root', provided_by=('staging', 'production'))
    args = '--clear --distribute'
    run('virtualenv %s %s' % (args, env.virtualenv_root))

def deploy():
    """ rsync code to remote host """
    require('root', provided_by=('staging', 'production'))
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    extra_opts = '--omit-dir-times'
    rsync_project(
        env.root,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_opts,
    )
    touch()

def update_apache_conf():
    """ upload apache configuration to remote host """
    require('root', provided_by=('staging', 'production'))
    source = os.path.join('apache', '%(environment)s.conf' % env)
    dest = os.path.join(env.home, 'apache.conf.d')
    put(source, dest, mode=0755)
    apache_reload()

def update_requirements():
    """ update external dependencies on remote host """
    require('code_root', provided_by=('staging', 'production'))
    requirements = os.path.join(env.code_root, 'requirements.txt')
    cmd = ['pip install']
    cmd += ['-E %(virtualenv_root)s' % env]
    cmd += ['--requirement %s' % requirements]
    run(' '.join(cmd))

def configtest():
    """ test Apache configuration """
    require('root', provided_by=('staging', 'production'))
    run('apache2ctl configtest')

def bzr_commit():
    run('bzr commit')

