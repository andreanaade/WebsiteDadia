# Generated by Django 4.0.4 on 2022-05-01 10:08

from django.db import migrations, models
import django.db.models.deletion
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentUsulan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usulan_comment', models.TextField()),
                ('tanggal', models.DateTimeField(default=None, null=True)),
                ('like', models.IntegerField(blank=True)),
                ('dislike', models.IntegerField(blank=True)),
            ],
        ),
        migrations.RenameField(
            model_name='kas',
            old_name='total',
            new_name='jumlah',
        ),
        migrations.AddField(
            model_name='kas',
            name='deskripsi',
            field=models.TextField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kas',
            name='status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='kas',
            name='tanggal',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='kas',
            name='tipe',
            field=models.CharField(default='Anggota', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='berita',
            name='tanggal',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='pengguna',
            name='foto_ktp',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=main.models.get_upload_path_ktp),
        ),
        migrations.AlterField(
            model_name='pengguna',
            name='foto_profile',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=main.models.get_upload_path_profile),
        ),
        migrations.AlterField(
            model_name='pengguna',
            name='no_hp',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='pengguna',
            name='no_ktp',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name='pengumuman',
            name='tanggal',
            field=models.DateTimeField(),
        ),
        migrations.CreateModel(
            name='Usulan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usulan', models.TextField()),
                ('tanggal', models.DateTimeField(default=None, null=True)),
                ('like', models.IntegerField(blank=True)),
                ('dislike', models.IntegerField(blank=True)),
                ('acara', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.acara')),
                ('pengusul', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.pengguna')),
            ],
        ),
        migrations.CreateModel(
            name='Notifikasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pesan', models.TextField()),
                ('tanggal', models.DateTimeField(default=None, null=True)),
                ('url', models.TextField()),
                ('sudah_dibaca', models.BooleanField(default=False)),
                ('dari', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.pengguna')),
                ('ke', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dari', to='main.pengguna')),
            ],
        ),
        migrations.CreateModel(
            name='LikeUsulan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tanggal', models.DateTimeField(default=None, null=True)),
                ('tipe', models.BooleanField(default=False)),
                ('pengusul', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.pengguna')),
                ('usulan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.usulan')),
            ],
        ),
        migrations.CreateModel(
            name='LikeCommentUsulan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tanggal', models.DateTimeField(default=None, null=True)),
                ('tipe', models.BooleanField(default=False)),
                ('comment_usulan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.commentusulan')),
                ('pengusul', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.pengguna')),
            ],
        ),
        migrations.AddField(
            model_name='commentusulan',
            name='pengusul',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.pengguna'),
        ),
        migrations.AddField(
            model_name='commentusulan',
            name='usulan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.usulan'),
        ),
    ]
