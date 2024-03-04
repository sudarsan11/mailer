# Generated by Django 3.2.24 on 2024-03-03 07:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('label_name', models.CharField(max_length=100, unique=True)),
                ('label_type', models.CharField(choices=[('SYSTEM', 'System'), ('USER', 'User')], max_length=20)),
                ('message_list_visibility', models.CharField(max_length=100, null=True)),
                ('label_list_visibility', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.TextField(unique=True)),
                ('thread_id', models.TextField(unique=True)),
                ('history_id', models.TextField()),
                ('size_estimate', models.IntegerField()),
                ('internal_date', models.DateTimeField()),
                ('snippet', models.TextField()),
                ('labels', models.ManyToManyField(related_name='labels', to='db.Label')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=254, unique=True)),
                ('username', models.CharField(max_length=254, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_type', models.CharField(choices=[('SENDER', 'Sender'), ('RECIPIENT', 'Recipient')], max_length=40)),
                ('message_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.message')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.user')),
            ],
        ),
        migrations.CreateModel(
            name='MessageHeaderValues',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('header', models.CharField(max_length=100)),
                ('value', models.TextField()),
                ('message_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.message')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='user_id',
            field=models.ManyToManyField(through='db.UserMessage', to='db.User'),
        ),
        migrations.AddField(
            model_name='label',
            name='user_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='db.user'),
        ),
    ]
