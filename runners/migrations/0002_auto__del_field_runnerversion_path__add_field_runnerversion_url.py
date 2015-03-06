# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'RunnerVersion.path'
        db.delete_column(u'runners_runnerversion', 'path')

        # Adding field 'RunnerVersion.url'
        db.add_column(u'runners_runnerversion', 'url',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'RunnerVersion.path'
        db.add_column(u'runners_runnerversion', 'path',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True),
                      keep_default=False)

        # Deleting field 'RunnerVersion.url'
        db.delete_column(u'runners_runnerversion', 'url')


    models = {
        u'platforms.platform': {
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
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'runners'", 'symmetrical': 'False', 'to': u"orm['platforms.Platform']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'})
        },
        u'runners.runnerversion': {
            'Meta': {'object_name': 'RunnerVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'runner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['runners.Runner']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['runners']