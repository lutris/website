# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_table('games_runnerversion', 'runners_runnerversion')
        db.rename_table('games_runner_platforms', 'runners_runner_platforms')
        db.rename_table('games_runner', 'runners_runner')

    def backwards(self, orm):
        db.rename_table('runners_runnerversion', 'games_runnerversion')
        db.rename_table('runners_runner_platforms', 'games_runner_platforms')
        db.rename_table('runners_runner', 'games_runner')

    models = {
        u'games.platform': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Platform'},
            'default_installer': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'runners.runner': {
            'Meta': {'ordering': "['name']", 'object_name': 'Runner'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'runners'", 'symmetrical': 'False', 'to': u"orm['games.Platform']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'})
        },
        u'runners.runnerversion': {
            'Meta': {'object_name': 'RunnerVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'runner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['runners.Runner']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['runners']
