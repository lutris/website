# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table(u'tosec_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'tosec', ['Category'])

        # Adding model 'Game'
        db.create_table(u'tosec_game', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tosec.Category'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'tosec', ['Game'])

        # Adding model 'Rom'
        db.create_table(u'tosec_rom', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tosec.Game'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('crc', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('md5', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('sha1', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'tosec', ['Rom'])


    def backwards(self, orm):
        # Deleting model 'Category'
        db.delete_table(u'tosec_category')

        # Deleting model 'Game'
        db.delete_table(u'tosec_game')

        # Deleting model 'Rom'
        db.delete_table(u'tosec_rom')


    models = {
        u'tosec.category': {
            'Meta': {'object_name': 'Category'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
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