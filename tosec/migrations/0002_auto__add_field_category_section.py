# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Category.section'
        db.add_column(u'tosec_category', 'section',
                      self.gf('django.db.models.fields.CharField')(default='TOSEC', max_length=12),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Category.section'
        db.delete_column(u'tosec_category', 'section')


    models = {
        u'tosec.category': {
            'Meta': {'object_name': 'Category'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'section': ('django.db.models.fields.CharField', [], {'default': "'TOSEC'", 'max_length': '12'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'tosec.game': {
            'Meta': {'object_name': 'Game'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tosec.Category']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'tosec.rom': {
            'Meta': {'object_name': 'Rom'},
            'crc': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tosec.Game']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['tosec']