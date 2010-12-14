# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'HiiCart'
        db.create_table('hiicart_hiicart', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_cart_state', self.gf('django.db.models.fields.CharField')(default='OPEN', max_length=16, db_index=True)),
            ('_cart_uuid', self.gf('django.db.models.fields.CharField')(max_length=36, db_index=True)),
            ('gateway', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hiicarts', to=orm['auth.User'])),
            ('failure_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('success_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('_sub_total', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=18, decimal_places=2, blank=True)),
            ('_total', self.gf('django.db.models.fields.DecimalField')(max_digits=18, decimal_places=2)),
            ('tax', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=18, decimal_places=2, blank=True)),
            ('shipping', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=18, decimal_places=2, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(default='', max_length=30)),
            ('last_name', self.gf('django.db.models.fields.CharField')(default='', max_length=30)),
            ('email', self.gf('django.db.models.fields.EmailField')(default='', max_length=75)),
            ('phone', self.gf('django.db.models.fields.CharField')(default='', max_length=30)),
            ('ship_street1', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('ship_street2', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('ship_city', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('ship_state', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('ship_postal_code', self.gf('django.db.models.fields.CharField')(default='', max_length=30)),
            ('ship_country', self.gf('django.db.models.fields.CharField')(default='', max_length=2)),
            ('bill_street1', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('bill_street2', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('bill_city', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('bill_state', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('bill_postal_code', self.gf('django.db.models.fields.CharField')(default='', max_length=30)),
            ('bill_country', self.gf('django.db.models.fields.CharField')(default='', max_length=2)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('hiicart', ['HiiCart'])

        # Adding model 'LineItem'
        db.create_table('hiicart_lineitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_sub_total', self.gf('django.db.models.fields.DecimalField')(max_digits=18, decimal_places=10)),
            ('_total', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=2)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(related_name='lineitems', to=orm['hiicart.HiiCart'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('discount', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ordering', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sku', self.gf('django.db.models.fields.CharField')(default='1', max_length=255, db_index=True)),
            ('thankyou', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('unit_price', self.gf('django.db.models.fields.DecimalField')(max_digits=18, decimal_places=10)),
        ))
        db.send_create_signal('hiicart', ['LineItem'])

        # Adding model 'Note'
        db.create_table('hiicart_note', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('hiicart', ['Note'])

        # Adding model 'Payment'
        db.create_table('hiicart_payment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=18, decimal_places=2)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(related_name='payments', to=orm['hiicart.HiiCart'])),
            ('gateway', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=45, null=True, blank=True)),
        ))
        db.send_create_signal('hiicart', ['Payment'])

        # Adding model 'RecurringLineItem'
        db.create_table('hiicart_recurringlineitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_sub_total', self.gf('django.db.models.fields.DecimalField')(max_digits=18, decimal_places=10)),
            ('_total', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=2)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recurringlineitems', to=orm['hiicart.HiiCart'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('discount', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ordering', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sku', self.gf('django.db.models.fields.CharField')(default='1', max_length=255, db_index=True)),
            ('thankyou', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('duration', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('duration_unit', self.gf('django.db.models.fields.CharField')(default='DAY', max_length=5)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('payment_token', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('recurring_price', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=2)),
            ('recurring_shipping', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=2)),
            ('recurring_times', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('recurring_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('trial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('trial_price', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=18, decimal_places=2)),
            ('trial_length', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('trial_times', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('hiicart', ['RecurringLineItem'])


    def backwards(self, orm):
        
        # Deleting model 'HiiCart'
        db.delete_table('hiicart_hiicart')

        # Deleting model 'LineItem'
        db.delete_table('hiicart_lineitem')

        # Deleting model 'Note'
        db.delete_table('hiicart_note')

        # Deleting model 'Payment'
        db.delete_table('hiicart_payment')

        # Deleting model 'RecurringLineItem'
        db.delete_table('hiicart_recurringlineitem')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hiicart.hiicart': {
            'Meta': {'object_name': 'HiiCart'},
            '_cart_state': ('django.db.models.fields.CharField', [], {'default': "'OPEN'", 'max_length': '16', 'db_index': 'True'}),
            '_cart_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'db_index': 'True'}),
            '_sub_total': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '2', 'blank': 'True'}),
            '_total': ('django.db.models.fields.DecimalField', [], {'max_digits': '18', 'decimal_places': '2'}),
            'bill_city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'bill_country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2'}),
            'bill_postal_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'bill_state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'bill_street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'bill_street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75'}),
            'failure_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'ship_city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'ship_country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2'}),
            'ship_postal_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'ship_state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'ship_street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'ship_street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'shipping': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '2', 'blank': 'True'}),
            'success_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '2', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hiicarts'", 'to': "orm['auth.User']"})
        },
        'hiicart.lineitem': {
            'Meta': {'ordering': "('ordering',)", 'object_name': 'LineItem'},
            '_sub_total': ('django.db.models.fields.DecimalField', [], {'max_digits': '18', 'decimal_places': '10'}),
            '_total': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '2'}),
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lineitems'", 'to': "orm['hiicart.HiiCart']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sku': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '255', 'db_index': 'True'}),
            'thankyou': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '18', 'decimal_places': '10'})
        },
        'hiicart.note': {
            'Meta': {'object_name': 'Note'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'hiicart.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '18', 'decimal_places': '2'}),
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'to': "orm['hiicart.HiiCart']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gateway': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '45', 'null': 'True', 'blank': 'True'})
        },
        'hiicart.recurringlineitem': {
            'Meta': {'ordering': "('ordering',)", 'object_name': 'RecurringLineItem'},
            '_sub_total': ('django.db.models.fields.DecimalField', [], {'max_digits': '18', 'decimal_places': '10'}),
            '_total': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '2'}),
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recurringlineitems'", 'to': "orm['hiicart.HiiCart']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '10'}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'duration_unit': ('django.db.models.fields.CharField', [], {'default': "'DAY'", 'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'payment_token': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'recurring_price': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '2'}),
            'recurring_shipping': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '2'}),
            'recurring_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recurring_times': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'sku': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '255', 'db_index': 'True'}),
            'thankyou': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'trial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trial_length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'trial_price': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '18', 'decimal_places': '2'}),
            'trial_times': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['hiicart']
