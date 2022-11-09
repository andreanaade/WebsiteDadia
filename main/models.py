from django.db import models
from django.contrib.auth.models import User
import os

# Create your models here.


def get_upload_path_ktp(instance, filename):
    return os.path.join("./static/documents/KTP/" + str(instance.nama), filename)


def get_upload_path_profile(instance, filename):
    return os.path.join("./static/documents/Profile/" + str(instance.nama), filename)


def get_upload_path_berita(instance, filename):
    return os.path.join("./static/documents/Berita/" + str(instance.judul), filename)


def get_upload_path_struk(instance, filename):
    return os.path.join("./static/documents/Struk/"+ str(instance.acara.judul) + '/' + str(instance.id), filename)


def get_upload_path_bukti_pembayaran(instance, filename):
    return os.path.join("./static/documents/Bukti Pembayaran/"+ str(instance.pengguna.nama) + '/' + str(instance.id), filename)


class Pengguna(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100, blank=False)
    no_ktp = models.CharField(max_length=16, blank=True, null=True)
    no_hp = models.CharField(max_length=12, blank=True, null=True)
    status = models.BooleanField(default=False)
    alasan = models.TextField(null=True, blank=True)
    tipe = models.CharField(max_length=20, blank=False)
    foto_ktp = models.FileField(upload_to=get_upload_path_ktp, max_length=1000, blank=True, null=True)
    foto_profile = models.FileField(upload_to=get_upload_path_profile, max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.nama
    

class Acara(models.Model):
    judul = models.CharField(max_length=100, blank=False)
    deskripsi = models.TextField(blank=True)
    tanggal_mulai = models.DateField(auto_now=False)
    tanggal_selesai = models.DateField(auto_now=False, blank=True)
    status_selesai = models.BooleanField(default=False)
    dibuat_oleh = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)

    def __str__(self):
        return self.judul

    
class Dana(models.Model):
    acara = models.ForeignKey(Acara, on_delete=models.CASCADE, primary_key=False)
    tipe = models.CharField(max_length=20, blank=False)
    deskripsi = models.TextField(blank=False)
    jumlah = models.IntegerField(blank=False)
    tanggal = models.DateTimeField(auto_now=True)
    struk = models.FileField(upload_to=get_upload_path_struk, max_length=1000)

    def __str__(self):
        return str(self.id)


class Peturunan(models.Model):
    acara = models.ForeignKey(Acara, on_delete=models.CASCADE, primary_key=False)
    jumlah_peturunan = models.IntegerField(blank=False)
    jumlah_bayar_tiap_anggota = models.IntegerField(blank=True)
    tambahan_bayar = models.IntegerField(blank=True, default=0)
    batas_pembayaran = models.DateField(blank=False)

    def __str__(self):
        return str(self.id)


class TambahanPeturunan(models.Model):
    peturunan = models.ForeignKey(Peturunan, on_delete=models.CASCADE, primary_key=False)
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    
    def __str__(self):
        return str(self.peturunan.acara.judul)


class DetailPeturunan(models.Model):
    peturunan = models.ForeignKey(Peturunan, on_delete=models.CASCADE, primary_key=False)
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    bayar = models.IntegerField(blank=False)
    tanggal_bayar = models.DateTimeField(null=True, default=None)
    diapprove_oleh = models.ForeignKey(Pengguna, default=None, null=True, on_delete=models.CASCADE, primary_key=False, related_name='Approve')
    status = models.BooleanField(default=False)
    tanggal_approve = models.DateTimeField(default=None, null=True)
    bukti_pembayaran = models.FileField(blank=True, upload_to=get_upload_path_bukti_pembayaran, max_length=1000)
    alasan = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Berita(models.Model):
    judul = models.TextField(blank=False)
    foto = models.FileField(upload_to=get_upload_path_berita, max_length=1000)
    deskripsi = models.TextField(blank=False)
    tanggal = models.DateTimeField(auto_now=False)
    dibuat_oleh = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)

    def __str__(self):
        return self.judul


class Pengumuman(models.Model):
    judul = models.TextField(blank=False)
    deskripsi = models.TextField(blank=False)
    tanggal = models.DateTimeField(auto_now=False)
    dibuat_oleh = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)

    def __str__(self):
        return str(self.id)


class Kas(models.Model):
    tipe = models.CharField(max_length=20, blank=False)
    deskripsi = models.TextField(blank=False)
    jumlah = models.IntegerField(blank=False)
    tanggal = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)


class Pengajuan(models.Model):
    acara = models.ForeignKey(Acara, on_delete=models.CASCADE, primary_key=False)
    dikirim_oleh = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    deskripsi = models.TextField(blank=False)
    jumlah = models.IntegerField(blank=False)
    tanggal_kirim = models.DateTimeField(null=True, default=None)
    status = models.BooleanField(default=False)
    tanggal_diapprove = models.DateTimeField(null=True, default=None)
    diapprove_oleh = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False, null=True, blank=True, related_name='ApprovePengajuan')
    alasan = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Usulan(models.Model):
    acara = models.ForeignKey(Acara, on_delete=models.CASCADE, primary_key=False)
    pengusul = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    usulan = models.TextField(blank=False)
    tanggal = models.DateTimeField(null=True, default=None)
    like = models.IntegerField(blank=True)
    dislike = models.IntegerField(blank=True)


class LikeUsulan(models.Model):
    usulan = models.ForeignKey(Usulan, on_delete=models.CASCADE, primary_key=False)
    pengusul = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    tanggal = models.DateTimeField(null=True, default=None)
    tipe = models.BooleanField(default=False)


class CommentUsulan(models.Model):
    usulan = models.ForeignKey(Usulan, on_delete=models.CASCADE, primary_key=False)
    pengusul = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    usulan_comment = models.TextField(blank=False)
    tanggal = models.DateTimeField(null=True, default=None)
    like = models.IntegerField(blank=True)
    dislike = models.IntegerField(blank=True)


class LikeCommentUsulan(models.Model):
    comment_usulan = models.ForeignKey(CommentUsulan, on_delete=models.CASCADE, primary_key=False)
    pengusul = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    tanggal = models.DateTimeField(null=True, default=None)
    tipe = models.BooleanField(default=False)


class Notifikasi(models.Model):
    dari = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False)
    ke = models.ForeignKey(Pengguna, on_delete=models.CASCADE, primary_key=False, related_name="dari")
    pesan = models.TextField(blank=False)
    tanggal = models.DateTimeField(null=True, default=None)
    url = models.TextField(blank=False)
    sudah_dibaca = models.BooleanField(default=False)