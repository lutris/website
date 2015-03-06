# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Platform'
        db.rename_table('games_platform', 'platforms_platform')


    def backwards(self, orm):
        db.rename_table('platforms_platform', 'games_platform')


    models = {
        u'platforms.platform': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Platform'},
            'default_installer': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['platforms']
