# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Platform'
        db.create_table(u'games_platform', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'games', ['Platform'])

        # Adding model 'Company'
        db.create_table(u'games_company', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
        ))
        db.send_create_signal(u'games', ['Company'])

        # Adding model 'Runner'
        db.create_table(u'games_runner', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=127, blank=True)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'games', ['Runner'])

        # Adding M2M table for field platforms on 'Runner'
        m2m_table_name = db.shorten_name(u'games_runner_platforms')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('runner', models.ForeignKey(orm[u'games.runner'], null=False)),
            ('platform', models.ForeignKey(orm[u'games.platform'], null=False))
        ))
        db.create_unique(m2m_table_name, ['runner_id', 'platform_id'])

        # Adding model 'Genre'
        db.create_table(u'games_genre', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'games', ['Genre'])

        # Adding model 'Game'
        db.create_table(u'games_game', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('publisher', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='published_game', null=True, to=orm['games.Company'])),
            ('developer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='developed_game', null=True, to=orm['games.Company'])),
            ('website', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('title_logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('steamid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'games', ['Game'])

        # Adding M2M table for field platforms on 'Game'
        m2m_table_name = db.shorten_name(u'games_game_platforms')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('game', models.ForeignKey(orm[u'games.game'], null=False)),
            ('platform', models.ForeignKey(orm[u'games.platform'], null=False))
        ))
        db.create_unique(m2m_table_name, ['game_id', 'platform_id'])

        # Adding M2M table for field genres on 'Game'
        m2m_table_name = db.shorten_name(u'games_game_genres')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('game', models.ForeignKey(orm[u'games.game'], null=False)),
            ('genre', models.ForeignKey(orm[u'games.genre'], null=False))
        ))
        db.create_unique(m2m_table_name, ['game_id', 'genre_id'])

        # Adding model 'Screenshot'
        db.create_table(u'games_screenshot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['games.Game'])),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('uploaded_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'games', ['Screenshot'])

        # Adding model 'Installer'
        db.create_table(u'games_installer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['games.Game'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'])),
            ('runner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['games.Runner'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(default='files:\n- file_id: http://location\n- unredistribuable_file: N/A\ninstaller:\n- move:\n    dst: $GAMEDIR\n    src: file_id\n')),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'games', ['Installer'])

        # Adding model 'GameLibrary'
        db.create_table(u'games_gamelibrary', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.User'], unique=True)),
        ))
        db.send_create_signal(u'games', ['GameLibrary'])

        # Adding M2M table for field games on 'GameLibrary'
        m2m_table_name = db.shorten_name(u'games_gamelibrary_games')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('gamelibrary', models.ForeignKey(orm[u'games.gamelibrary'], null=False)),
            ('game', models.ForeignKey(orm[u'games.game'], null=False))
        ))
        db.create_unique(m2m_table_name, ['gamelibrary_id', 'game_id'])

        # Adding model 'Featured'
        db.create_table(u'games_featured', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'games', ['Featured'])


    def backwards(self, orm):
        # Deleting model 'Platform'
        db.delete_table(u'games_platform')

        # Deleting model 'Company'
        db.delete_table(u'games_company')

        # Deleting model 'Runner'
        db.delete_table(u'games_runner')

        # Removing M2M table for field platforms on 'Runner'
        db.delete_table(db.shorten_name(u'games_runner_platforms'))

        # Deleting model 'Genre'
        db.delete_table(u'games_genre')

        # Deleting model 'Game'
        db.delete_table(u'games_game')

        # Removing M2M table for field platforms on 'Game'
        db.delete_table(db.shorten_name(u'games_game_platforms'))

        # Removing M2M table for field genres on 'Game'
        db.delete_table(db.shorten_name(u'games_game_genres'))

        # Deleting model 'Screenshot'
        db.delete_table(u'games_screenshot')

        # Deleting model 'Installer'
        db.delete_table(u'games_installer')

        # Deleting model 'GameLibrary'
        db.delete_table(u'games_gamelibrary')

        # Removing M2M table for field games on 'GameLibrary'
        db.delete_table(db.shorten_name(u'games_gamelibrary_games'))

        # Deleting model 'Featured'
        db.delete_table(u'games_featured')


    models = {
        u'accounts.user': {
            'Meta': {'object_name': 'User'},
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'steamid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'games.company': {
            'Meta': {'ordering': "['name']", 'object_name': 'Company'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        u'games.featured': {
            'Meta': {'object_name': 'Featured'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'games.game': {
            'Meta': {'ordering': "['name']", 'object_name': 'Game'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'developer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'developed_game'", 'null': 'True', 'to': u"orm['games.Company']"}),
            'genres': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['games.Genre']", 'null': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['games.Platform']", 'null': 'True', 'blank': 'True'}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'published_game'", 'null': 'True', 'to': u"orm['games.Company']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'steamid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title_logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'games.gamelibrary': {
            'Meta': {'object_name': 'GameLibrary'},
            'games': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['games.Game']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['accounts.User']", 'unique': 'True'})
        },
        u'games.genre': {
            'Meta': {'ordering': "['name']", 'object_name': 'Genre'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'games.installer': {
            'Meta': {'object_name': 'Installer'},
            'content': ('django.db.models.fields.TextField', [], {'default': "'files:\\n- file_id: http://location\\n- unredistribuable_file: N/A\\ninstaller:\\n- move:\\n    dst: $GAMEDIR\\n    src: file_id\\n'"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['games.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['games.Runner']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'games.platform': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Platform'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'games.runner': {
            'Meta': {'ordering': "['name']", 'object_name': 'Runner'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['games.Platform']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'})
        },
        u'games.screenshot': {
            'Meta': {'object_name': 'Screenshot'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['games.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']"})
        }
    }

    complete_apps = ['games']