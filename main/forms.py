from django import forms
from .models import Pengguna
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime

def get_choices():
    pilihan = [('', '-----------')]
    for pengguna in Pengguna.objects.all():
        pilihan.append((pengguna.id, pengguna.nama))
    return pilihan


class Register(forms.Form):
    no_ktp = forms.IntegerField(required=True, label='Nomor KTP', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nomor KTP anda'}))
    foto_ktp = forms.FileField(required=True, label='Gambar KTP', widget=forms.FileInput(attrs={'accept':'s/*', 'class':'form-control'}))
    nama = forms.CharField(required=True, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nama lengkap anda'}))
    email = forms.CharField(label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan email anda'}))
    no_hp = forms.IntegerField(required=True, label='Nomor HP', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan nomor HP anda'}))


class NewAuth(forms.Form):
    username = forms.CharField(required=True, label='Username', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan username anda'}))
    password = forms.CharField(max_length=100, label='Password', required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password anda'}))
    password_validation = forms.CharField(max_length=100, label='Validasi Password', required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Validasi Password'}))

class Login(forms.Form):
    username = forms.CharField(required=True, label='Username', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan username anda'}))
    password = forms.CharField(max_length=100, label='Password', required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password anda'}))


class DateInput(forms.DateInput):
    input_type = 'date'


class Acara(forms.Form):
    judul = forms.CharField(required=True, label='Judul Kegiatan', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Judul Kegiatan'}))
    deskripsi = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Deskripsi Kegiatan'}), label='Deskripsi Kegiatan')
    tanggal_mulai = forms.DateField(required=True, widget=DateInput(attrs={'autocomplete':'off', 'class': 'form-control'}), label='Tanggal Mulai Kegiatan')
    tanggal_selesai = forms.DateField(required=True, widget=DateInput(attrs={'autocomplete':'off', 'class': 'form-control'}), label='Tanggal Selesai Kegiatan')
    jumlah_peturunan = forms.IntegerField(required=True, label='Estimasi Biaya', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Estimasi Biaya'}))
    batas_pembayaran = forms.DateField(required=True, widget=DateInput(attrs={'autocomplete':'off', 'class': 'form-control'}), label='Batas Pembayaran')
    # pengguna = forms.ModelChoiceField(queryset=Pengguna.objects.all())

class Dana(forms.Form):
    tipe = forms.Field(required=True, label='Tipe Dana', widget=forms.Select(attrs={'class':'form-select'}, choices=(('','--------'),('Pemasukan', 'Pemasukan'), ('Pengeluaran', 'Pengeluaran'))))
    deskripsi = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Keterangan Dana'}), label='Keterangan Dana')
    jumlah = forms.IntegerField(required=True, label='Jumlah Dana', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Dana'}))
    struk = forms.FileField(required=False, label='Struk Belanja', widget=forms.FileInput(attrs={'accept':'s/*', 'class':'form-control'}))


class Peturunan(forms.Form):
    # pengguna = forms.Field(required=True, label='Pengguna', widget=forms.Select(attrs={'class':'form-select'}, choices=[(pengguna.id, pengguna.nama) for pengguna in Pengguna.objects.all()]))
    pengguna = forms.Field(required=True, label='Pengguna', widget=forms.Select(attrs={'class':'form-select', 'required':'true', 'value':''}, choices=get_choices()))
    bayar = forms.IntegerField(required=True, label='Jumlah Bayar', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Bayar'}))


class BiayaTambahan(forms.Form):
    tambahan_bayar = forms.IntegerField(required=True, label='', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Biaya Pedesaan'}))


class BayarTransfer(forms.Form):
    jumlah = forms.IntegerField(required=True, label='Jumlah Dana', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Bayar'}))
    bukti_bayar = forms.FileField(label='Bukti Pembayaran', widget=forms.FileInput(attrs={'accept':'s/*', 'class':'form-control', 'required':'true'}))


class Tolak(forms.Form):
    alasan = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Alasan Ditolak'}), label='Alasan Ditolak')


class PengajuanDana(forms.Form):
    deskripsi = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Keterangan Pengajuan'}), label='Keterangan Dana')
    jumlah = forms.IntegerField(required=True, label='Jumlah Dana', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Pengajuan'}))


class Pengguna(forms.Form):
    nama = forms.CharField(required=True, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Nama Lengkap Anggota'}))
    tipe = forms.Field(required=True, label='Jabatan Anggota', widget=forms.Select(attrs={'class':'form-select'}, choices=(('','--------'),('Anggota', 'Anggota'), ('Bendahara', 'Bendahara'), ('Admin', 'Admin'))))


class Kas(forms.Form):
    tipe = forms.Field(required=True, label='Tipe Kas', widget=forms.Select(attrs={'class':'form-select'}, choices=(('','--------'),('Pemasukan', 'Pemasukan'), ('Pengeluaran', 'Pengeluaran'))))
    deskripsi = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Keterangan Kas'}), label='Keterangan Kas')
    jumlah = forms.IntegerField(required=True, label='Jumlah Kas', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Jumlah Kas'}))


class Pengumuman(forms.Form):
    judul = forms.CharField(required=True, label='Judul Pengumuman', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Judul Pengumuman'}))
    deskripsi = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Deskripsi Pengumuman'}), label='Deskripsi Pengumuman')


class Berita(forms.Form):
    judul = forms.CharField(required=True, label='Judul Berita', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Judul Berita'}))
    deskripsi = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols': '2', 'rows':'2','class': 'form-control', 'placeholder': 'Masukkan Deskripsi Berita'}), label='Deskripsi Berita')
    foto = forms.FileField(required=False, label='Foto Berita', widget=forms.FileInput(attrs={'accept':'s/*', 'class':'form-control'}))


class Profile(forms.Form):
    nama = forms.CharField(required=True, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Nama Lengkap'}))
    no_ktp = forms.IntegerField(required=True, label='No KTP', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan No KTP', 'readonly':'true'}))
    email = forms.CharField(label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan email anda'}))
    no_hp = forms.IntegerField(required=True, label='No HP', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan No HP'}))
    tipe = forms.CharField(required=True, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Tipe', 'readonly':'true'}))
    foto_profile = forms.FileField(required=False, label='Foto Profile', widget=forms.FileInput(attrs={'accept':'s/*', 'class':'account-file-input', 'hidden':'true'}))
    username = forms.CharField(required=True, label='Username', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan username anda'}))
    password_lama = forms.CharField(max_length=100, label='Password', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password lama anda'}))
    password_baru = forms.CharField(max_length=100, label='Password', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password baru'}))
    password_validasi = forms.CharField(max_length=100, label='Password', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password baru lagi'}))