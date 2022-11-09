from django.shortcuts import render, redirect
from django.db.models import Q, Sum, F
from django.core import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib import messages
from .forms import Register, Login, Acara as AcaraForm, Berita as BeritaForm, Dana as DanaForm, Peturunan as PeturunanForm, BiayaTambahan as BiayaTambahanForm, BayarTransfer as BayarTransferForm, Tolak as TolakForm, PengajuanDana as PengajuanDanaForm, Pengguna as PenggunaForm, NewAuth, Kas as KasForm, Pengumuman as PengumumanForm, Profile as ProfileForm
from .models import Pengguna, Acara, Peturunan, Berita, Dana, DetailPeturunan, TambahanPeturunan, Pengajuan, Kas, Usulan, LikeUsulan, CommentUsulan, LikeCommentUsulan, Notifikasi, Pengumuman
from datetime import datetime, date
import json
import string
import random
import os


# Create your views here.
def kirim(dari, ke, pesan, url):
    for k in ke:
        notifikasi = Notifikasi.objects.create(
            dari=dari,
            ke=k,
            pesan=pesan,
            tanggal=timezone.now(),
            url=url
        )
        notifikasi.save()


def generate_random_password():
    characters = list(string.ascii_letters + string.digits)
    length = 5
    random.shuffle(characters)
    password = []
    for i in range(length):
        password.append(random.choice(characters))

    random.shuffle(password)
    return str("".join(password))


def checkAuth(request):
    return request.user.is_authenticated


def check_perm(request, tipe):
    return request.user.pengguna.tipe == tipe


def logout(request):
    auth_logout(request)
    return redirect('/profile/login/')


def new_auth(request):
    response = {}
    
    if request.method == 'POST':
        form = NewAuth(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['password_validation']:
                response['form'] = form
                messages.error(request, 'Password tidak sama dengan kolom validasi!')
                return render(request, 'main/new_auth.html', response)

            user = User.objects.create(
                username=form.cleaned_data['username'], 
                is_active=True
            )
            user.set_password(form.cleaned_data['password'])
            user.save()
            request.session['user_id'] = user.id
            request.session['username'] = form.cleaned_data['username']
            request.session['password'] = form.cleaned_data['password']
            return redirect('/profile/register/')
    else:
        form = NewAuth()
    
    response['form'] = form
    return render(request, 'main/new_auth.html', response)


def register(request):
    response = {}
    if request.method == 'POST':
        if request.FILES:
            form = Register(request.POST, request.FILES)
        else:
            form = Register(request.POST)
        user = User.objects.filter(id=request.session.get('user_id')).first()
        user.email = request.POST.get('email')
        user.save()
        pengguna = Pengguna.objects.create(
            user=user,
            nama=request.POST.get('nama'),
            no_ktp=request.POST.get('no_ktp'),
            foto_ktp=request.FILES.get('foto_ktp'),
            no_hp=request.POST.get('no_hp'),
            status=False,
            tipe='Anggota'
        )
        pengguna.save()
        dari = pengguna
        ke = [p for p in Pengguna.objects.filter(tipe='Admin')]
        pesan = "{} meminta validasi akun!".format(pengguna.nama)
        url = "/validasi-anggota/"
        kirim(dari, ke, pesan, url)
        messages.info(request, 'Proses registrasi berhasil! Harap tunggu validasi dari Admin dan mohon terus mengecek status akun anda dengan login menggunakan username dan password yang telah dibuat!')
        return redirect('/profile/login/')

    else:
        form = Register()

    response['form'] = form
    return render(request, 'main/register.html', response)


def login(request):
    response = {}
    if request.method == 'POST':
        form = Login(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                obj = User.objects.get(username=username)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                obj = None

            if obj is not None:
                user = authenticate(username=username, password=password)
                if user is not None:
                    auth_login(request, user)
                    pengguna = Pengguna.objects.filter(user=user).first()
                    request.session['pengguna_id'] = pengguna.id
                    request.session['user_id'] = user.id
                    if pengguna.alasan:
                        messages.error(request, 'Request akses anda ditolak oleh Admin dengan alasan: \"{}\". Silahkan mengisi ulang formulir berikut!'.format(pengguna.alasan))
                        return redirect('/profile/update-profile/')
                    elif not pengguna.status and pengguna.no_ktp and pengguna.no_hp and user.email:
                        auth_logout(request)
                        messages.error(request, 'Maaf data anda belum divalidasi oleh Admin! Silahkan menghubungi admin terlebih dahulu!')
                        return redirect('/profile/login/')
                    elif pengguna.no_ktp and pengguna.no_hp and user.email and pengguna.status:
                        messages.success(request, 'Login Berhasil')
                        return redirect(request.GET.get('next') if request.GET.get('next') else '/pengumuman/')
                    else:
                        return redirect('/profile/update-profile/')
                else:
                    messages.error(request, 'Username atau password anda salah!')
                    response['username'] = username
                    response['password'] = password
    else:
        form = Login()
    response['form'] = form
    return render(request, 'main/login.html', response)


def tambah_acara(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    if request.method == 'POST':
        form = AcaraForm(request.POST)
        if form.is_valid():
            pengguna = Pengguna.objects.filter(user=request.user).first()
            acara = Acara.objects.create(
                judul=form.cleaned_data['judul'],
                deskripsi=form.cleaned_data['deskripsi'],
                tanggal_mulai=form.cleaned_data['tanggal_mulai'],
                tanggal_selesai=form.cleaned_data['tanggal_selesai'],
                dibuat_oleh=pengguna
            )
            peturunan = Peturunan.objects.create(
                acara=acara,
                jumlah_peturunan=form.cleaned_data['jumlah_peturunan'],
                jumlah_bayar_tiap_anggota=form.cleaned_data['jumlah_peturunan']/Pengguna.objects.all().count(),
                batas_pembayaran=form.cleaned_data['batas_pembayaran']
            )
            dana = Dana.objects.create(
                acara=acara,
                tipe="Pemasukan",
                deskripsi="Peturunan (Estimasi Biaya)",
                jumlah=peturunan.jumlah_peturunan,
                struk=None
            )
            acara.save()
            peturunan.save()
    else:
        form = AcaraForm()

    response['form'] = form
    return render(request, 'main/tambah_acara.html', response)


def tambah_berita(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    if request.method == 'POST' and request.FILES:
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            form = BeritaForm(request.POST, request.FILES)
            if form.is_valid():
                print(form.cleaned_data)
                berita = Berita.objects.create(
                    judul=' '.join(kata.capitalize() for kata in form.cleaned_data['judul'].split()),
                    foto=form.cleaned_data['foto'],
                    deskripsi=form.cleaned_data['deskripsi']
                )
                berita.save()
                messages.success(request, 'Berita berhasil di upload!')
                form = BeritaForm()
    else:
        form = BeritaForm()
    response['form'] = form
    return render(request, 'main/tambah_berita.html', response)


def berita(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    if request.method == 'POST':
        if request.FILES:
            form = BeritaForm(request.POST, request.FILES)
        else:
            form = BeritaForm(request.POST)

        if form.is_valid():
            if request.POST.get('btn') == 'Tambah':
                berita = Berita.objects.create(
                    judul=form.cleaned_data['judul'],
                    foto=form.cleaned_data['foto'],
                    deskripsi=form.cleaned_data['deskripsi'],
                    tanggal=timezone.now(),
                    dibuat_oleh=request.user.pengguna
                )
                berita.save()
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.all()]
                pesan = "Berita {} telah dibuat!".format(form.cleaned_data['judul'])
                url = "/Berita/"
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Berita berhasil dimasukkan!')
            elif request.POST.get('btn') == 'Ubah':
                berita = Berita.objects.filter(id=request.POST.get('id_berita')).first()
                if berita:
                    berita.judul = form.cleaned_data['judul']
                    berita.foto = form.cleaned_data['foto']
                    berita.deskripsi = form.cleaned_data['deskripsi']
                    berita.save()
                    messages.success(request, 'Berita berhasil diubah!')
    else:
        form = BeritaForm()

    response['form'] = form
    response['semua_berita'] = Berita.objects.all().order_by('-id')
    response['ada_data'] = len(response['semua_berita']) > 0

    return render(request, 'main/berita.html', response)


def detail_berita(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    response['berita'] = Berita.objects.filter(id=id).first()
    return render(request, 'main/detail_berita.html', response)


def update_acara(request=None):
    semua_acara = Acara.objects.all()
    for acara in semua_acara:
        if acara.tanggal_selesai >= date.today():
            acara.status_selesai = False
            peturunan = Peturunan.objects.filter(acara=acara).first()
            peturunan.jumlah_bayar_tiap_anggota = peturunan.jumlah_peturunan/Pengguna.objects.filter(status=True).count()
            peturunan.save()
        else:
            if not Kas.objects.filter(deskripsi='Sisa Dana di Acara ({})'.format(acara.judul)):
                total_pemasukan_raw = Dana.objects.filter(acara=acara, tipe='Pemasukan').aggregate(Sum('jumlah'))['jumlah__sum']
                total_pengeluaran_raw = Dana.objects.filter(acara=acara, tipe='Pengeluaran').aggregate(Sum('jumlah'))['jumlah__sum']
                total_pemasukan = total_pemasukan_raw if total_pemasukan_raw else 0
                total_pengeluaran = total_pengeluaran_raw if total_pengeluaran_raw else 0
                total = total_pemasukan - total_pengeluaran
                kas = Kas.objects.create(
                    tipe='Pemasukan',
                    deskripsi='Sisa Dana di Acara ({})'.format(acara.judul),
                    jumlah=total
                )
                kas.save()
                acara.status_selesai = True
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.all()]
                pesan = "Acara {} telah selesai!".format(acara.judul)
                url = "/kas/"
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Peturunan telah berhasil dimasukkan!')

        acara.save()


def acara(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    response = {}
    
    if request.method == 'POST':
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            form = AcaraForm(request.POST)
            if form.is_valid():
                pengguna = Pengguna.objects.filter(user=request.user).first()
                acara = Acara.objects.create(
                    judul=form.cleaned_data['judul'],
                    deskripsi=form.cleaned_data['deskripsi'] if len(form.cleaned_data['deskripsi']) > 0 else 'Tidak Ada',
                    tanggal_mulai=form.cleaned_data['tanggal_mulai'],
                    tanggal_selesai=form.cleaned_data['tanggal_selesai'],
                    dibuat_oleh=pengguna
                )
                peturunan = Peturunan.objects.create(
                    acara=acara,
                    jumlah_peturunan=form.cleaned_data['jumlah_peturunan'],
                    jumlah_bayar_tiap_anggota=form.cleaned_data['jumlah_peturunan']/Pengguna.objects.filter(status=True).count(),
                    batas_pembayaran=form.cleaned_data['batas_pembayaran']
                )
                dana = Dana.objects.create(
                    acara=acara,
                    tipe="Pemasukan",
                    deskripsi="Peturunan (Estimasi Biaya)",
                    jumlah=peturunan.jumlah_peturunan,
                    struk=None
                )
                acara.save()
                peturunan.save()
                dana.save()
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.all()]
                pesan = "Acara {} telah dibuat!".format(form.cleaned_data['judul'])
                url = "/acara/"
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Acara telah berhasil dibuat!')
    else:
        form = AcaraForm()
    
    response['form'] = form
    response['acara'] = Acara.objects.all().order_by('-id')
    response['ada_data'] = len(response['acara']) > 0
    update_acara()

    return render(request, 'main/acara.html', response)


def detail_acara(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    response = {}

    if request.method == 'POST':
        form_bayar = BayarTransferForm(request.POST)
        form = AcaraForm(request.POST)
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            if form.is_valid():
                if request.POST['btn'] == 'Ubah':
                    ubah_acara = Acara.objects.filter(id=int(request.POST.get('id_acara'))).first()
                    ubah_acara.judul = form.cleaned_data['judul']
                    ubah_acara.deskripsi=form.cleaned_data['deskripsi']
                    ubah_acara.tanggal_mulai=form.cleaned_data['tanggal_mulai']
                    ubah_acara.tanggal_selesai=form.cleaned_data['tanggal_selesai']

                    ubah_peturunan = Peturunan.objects.filter(acara=ubah_acara).first()
                    ubah_peturunan.jumlah_peturunan = form.cleaned_data['jumlah_peturunan']
                    ubah_peturunan.jumlah_bayar_tiap_anggota=form.cleaned_data['jumlah_peturunan']/Pengguna.objects.all().count()
                    ubah_peturunan.batas_pembayaran = form.cleaned_data['batas_pembayaran']

                    ubah_dana = Dana.objects.filter(acara=ubah_acara).earliest('id')
                    ubah_dana.jumlah = ubah_peturunan.jumlah_peturunan

                    ubah_acara.save()
                    ubah_peturunan.save()
                    ubah_dana.save()

                    messages.success(request, 'Acara telah berhasil diubah!')
                    return redirect('/acara/{}'.format(id))

        if request.POST['btn'] == 'Bayar' and request.FILES:
            acara = Acara.objects.filter(id=id).first()
            if acara:
                peturunan = Peturunan.objects.filter(acara=acara).first()
                pengguna = request.user.pengguna
                if peturunan:
                    detail_peturunan = DetailPeturunan.objects.create(
                        peturunan=peturunan,
                        pengguna=pengguna,
                        tanggal_bayar=timezone.now(),
                        bayar=request.POST.get('jumlah'),
                        status=False,
                        bukti_pembayaran=request.FILES.get('bukti_bayar')
                    )
                    dari = request.user.pengguna
                    ke = [p for p in Pengguna.objects.filter(Q(tipe='Bendahara') | Q(tipe='Admin'))]
                    pesan = "{} meminta validasi pembayaran transfer!".format(pengguna.nama)
                    url = "/acara/{}/validasi-bayar-transfer/".format(acara.id)
                    kirim(dari, ke, pesan, url)
                    messages.success(request, 'Bukti Bayar Berhasil Dikirim Untuk Divalidasi Oleh Bendaraha/Admin, Silahkan Tunggu Notifikasinya!')


        if request.POST['btn'] == 'Tambah Usulan':
            if request.POST.get('usulan'):
                usulan = Usulan.objects.create(
                    acara=Acara.objects.filter(id=id).first(),
                    pengusul=request.user.pengguna,
                    usulan=request.POST.get('usulan'),
                    tanggal=timezone.now(),
                    like=0,
                    dislike=0
                )
                usulan.save()
                messages.success(request, 'Usulan sudah berhasil ditambahkan!')
    else:
        form = AcaraForm()
        form_bayar = BayarTransferForm()
    
    response['form'] = form
    response['form_bayar'] = form_bayar
    response['acara'] = Acara.objects.filter(id=id).first()
    response['peturunan'] = Peturunan.objects.filter(acara_id=id).first()
    semua_usulan = Usulan.objects.filter(acara=response['acara']).order_by('-id')
    mapped_usulan = []
    for usulan in semua_usulan:
        sudah_like = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=True).first()
        sudah_dislike = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=False).first()
        mapped_usulan.append({'usulan':usulan, 'like':sudah_like, 'dislike':sudah_dislike})
    response['semua_usulan'] = mapped_usulan
    response['kena_tambahan_biaya'] = True if TambahanPeturunan.objects.filter(peturunan=response['peturunan'], pengguna=request.user.pengguna) else False
    total_bayar = DetailPeturunan.objects.filter(peturunan=response['peturunan'], pengguna=request.user.pengguna, status=True).aggregate(Sum('bayar'))['bayar__sum']
    total_bayar = total_bayar if total_bayar else 0
    tambahan = TambahanPeturunan.objects.filter(peturunan=response['peturunan'], pengguna=request.user.pengguna)
    if tambahan:
        response['belum_dibayar'] = response['peturunan'].jumlah_bayar_tiap_anggota + response['peturunan'].tambahan_bayar - total_bayar
    else:
        response['belum_dibayar'] = response['peturunan'].jumlah_bayar_tiap_anggota - total_bayar
    update_acara(request)
    return render(request, 'main/detail_acara.html', response)


def dana(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    acara = None
    if id:
        acara = Acara.objects.filter(id=id).first()

    semua_dana = Dana.objects.filter(acara=acara).order_by('id')

    form_pengajuan = PengajuanDanaForm()

    if request.method == 'POST':
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            if request.FILES:
                form = DanaForm(request.POST, request.FILES)
            else:
                form_pengajuan = PengajuanDanaForm(request.POST)
                form = DanaForm(request.POST)

            if form.is_valid() or form_pengajuan.is_valid():
                if request.POST['btn'] == 'Tambah':
                    dana = Dana.objects.create(
                        acara=acara,
                        tipe=form.cleaned_data['tipe'],
                        deskripsi=form.cleaned_data['deskripsi'],
                        jumlah=form.cleaned_data['jumlah'],
                        struk=form.cleaned_data['struk']
                    )
                    dana.save()
                    messages.success(request, 'Dana telah berhasil dimasukkan!')
                    dari = request.user.pengguna
                    ke = [p for p in Pengguna.objects.all()]
                    pesan = "Dana baru telah ditambahkan!"
                    url = "/acara/{}/dana".format(acara.id)
                    kirim(dari, ke, pesan, url)
                    return redirect('/acara/{}/dana'.format(acara.id))

                elif request.POST['btn'] == 'Ubah':
                    ubah_dana = Dana.objects.filter(id=int(request.POST.get('id_dana'))).first()
                    ubah_dana.tipe=form.cleaned_data['tipe']
                    ubah_dana.deskripsi=form.cleaned_data['deskripsi']
                    ubah_dana.jumlah=form.cleaned_data['jumlah']
                    if form.cleaned_data['struk']:
                        if ubah_dana.struk:
                            os.remove(str(ubah_dana.struk))
                        ubah_dana.struk=form.cleaned_data['struk']
                    ubah_dana.save()
                    messages.success(request, 'Dana telah berhasil diubah!')
                    return redirect('/acara/{}/dana'.format(acara.id))
                elif request.POST['btn'] == 'Tambah Pengajuan':
                    pengajuan = Pengajuan.objects.create(
                        acara=acara,
                        dikirim_oleh=request.user.pengguna,
                        deskripsi=form.cleaned_data['deskripsi'],
                        jumlah=form.cleaned_data['jumlah'],
                        tanggal_kirim=timezone.now(),
                        status=False
                    )
                    pengajuan.save()
                    dari = request.user.pengguna
                    ke = [p for p in Pengguna.objects.filter(tipe='Admin')]
                    pesan = "{} meminta validasi pengajuan!".format(request.user.pengguna)
                    url = "/acara/{}/validasi-pengajuan/".format(acara.id)
                    kirim(dari, ke, pesan, url)
                    messages.info(request, 'Pengajuan berhasil dikirim untuk divalidasi oleh Admin, silahkan cek notifikasi secara berkala!')
                else:
                    messages.error(request, "Terjadi kesalahan, coba ulang kembali!")
    else:
        form = DanaForm()

    response['form'] = form
    response['ada_dana'] = (len(semua_dana) > 0)
    response['semua_dana'] = semua_dana
    total_pengeluaran = semua_dana.filter(tipe='Pengeluaran').aggregate(Sum('jumlah'))['jumlah__sum']
    total_pemasukan = semua_dana.filter(tipe='Pemasukan').aggregate(Sum('jumlah'))['jumlah__sum']
    response['total_pengeluaran'] = total_pengeluaran if total_pengeluaran else 0
    response['total_pemasukan'] = total_pemasukan if total_pemasukan else 0
    response['total_dana'] = (total_pemasukan if total_pemasukan else 0) - (total_pengeluaran if total_pengeluaran else 0)
    response['id_acara'] = id
    response['acara'] = acara
    response['form_pengajuan'] = form_pengajuan
    return render(request, 'main/dana.html', response)


def get_dana(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    dana = Dana.objects.filter(id=id).first()
    if dana:
        serialized_obj = serializers.serialize('json', [ dana, ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def hapus_dana(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
        dana = Dana.objects.filter(id=id).first()
        if dana:
            if dana.struk:
                os.remove(str(dana.struk))
            dana.delete()
            messages.success(request, "Dana telah berhasil dihapus!")
    return redirect('/acara/{}/dana'.format(dana.acara.id))


def hapus_acara(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
        acara = Acara.objects.filter(id=id).first()
        if acara:
            acara.delete()
            messages.success(request, "Acara telah berhasil dihapus!")
    return redirect('/acara')


def test(request):
    pass
    with open('data.txt', 'r') as data:
        anggota = data.read().splitlines()
        pdf = []
        for a in sorted(anggota):
            password = generate_random_password()
            username = generate_random_password()
            user = User.objects.create(
                username = username,
                email = password
            )
            user.set_password(password)
            user.save()
            pengguna = Pengguna.objects.create(
                user = user,
                no_ktp = 0,
                no_hp = 0,
                nama = a,
                tipe = 'Anggota',
                status = False
            )
            pengguna.save()
            pdf.append({'Nama':a, 'Username':username, 'Password':password})
        # f = open("nama.txt", 'a')
        # for i, p in enumerate(pdf):
        #     f.write('{}\n'.format(p['Nama']))
        # f.close()

        # f = open("username.txt", 'a')
        # for i, p in enumerate(pdf):
        #     f.write('{}\n'.format(p['Username']))
        # f.close()

        # f = open("password.txt", 'a')
        # for i, p in enumerate(pdf):
        #     f.write('{}\n'.format(p['Password']))
        # f.close()
        return render(request, 'main/test.html', {'pdf':pdf})

def tutorial(request):
    if request.user.pengguna.tipe == 'Anggota':
        return render(request, 'main/tutorial_user.html')
    else:
        return render(request, 'main/tutorial_admin.html')


def get_acara(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    acara = Acara.objects.filter(id=id).first()
    if acara:
        peturunan = Peturunan.objects.filter(acara=acara).first()
        serialized_obj = serializers.serialize('json', [ acara, peturunan, ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def get_jumlah(request, id, id_peturunan):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    pengguna = Pengguna.objects.filter(id=id).first()
    peturunan = Peturunan.objects.filter(id=id_peturunan).first()
    total_bayar = 0
    total_bayar = DetailPeturunan.objects.filter(peturunan=peturunan, pengguna=pengguna, status=True).aggregate(Sum('bayar'))['bayar__sum']
    total_bayar = total_bayar if total_bayar else 0
    tambahan = TambahanPeturunan.objects.filter(peturunan=peturunan, pengguna=pengguna)
    if tambahan:
        bayar = peturunan.jumlah_bayar_tiap_anggota + peturunan.tambahan_bayar - total_bayar
    else:
        bayar = peturunan.jumlah_bayar_tiap_anggota - total_bayar

    serialized_obj = {'nama':pengguna.nama, 'id':pengguna.id, 'bayar':bayar}
    return JsonResponse(serialized_obj, safe=False)


def get_detail_peturunan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    detail = DetailPeturunan.objects.filter(id=id).first()
    pengguna = Pengguna.objects.filter(id=detail.pengguna.id).first()
    if detail:
        serialized_obj = serializers.serialize('json', [ detail, pengguna ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def hapus_detail_peturunan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
        detail = DetailPeturunan.objects.filter(id=id).first()
        if detail:
            detail.delete()
            messages.success(request, "Peturunan telah berhasil dihapus!")
    return redirect('/acara/{}/peturunan'.format(detail.peturunan.acara.id))


def peturunan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    acara = Acara.objects.filter(id=id).first()
    if acara:
        peturunan = Peturunan.objects.filter(acara=acara).first()
    else:
        messages.error(request, "Maaf terjadi kesalahan!")
        return redirect('acara/')

    if request.method == 'POST':
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            form = PeturunanForm(request.POST)
            
            if request.POST['btn'] == 'Tambah':
                pengguna = Pengguna.objects.filter(id=request.POST.get('pengguna')).first()
                detail_peturunan = DetailPeturunan.objects.create(
                    peturunan=peturunan,
                    pengguna=pengguna,
                    tanggal_bayar=timezone.now(),
                    bayar=request.POST.get('bayar'),
                    diapprove_oleh=Pengguna.objects.filter(user=request.user).first(),
                    status=True,
                    tanggal_approve=timezone.now()
                )
                detail_peturunan.save()
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.filter(Q(tipe='Bendahara') | Q(tipe='Admin'))]
                pesan = "{} membayar peturunan sebesar {}!".format(pengguna.nama, request.POST.get('bayar'))
                url = "/acara/{}/peturunan".format(acara.id)
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Peturunan telah berhasil dimasukkan!')
                return redirect('/acara/{}/peturunan'.format(acara.id))

            elif request.POST['btn'] == 'Ubah':
                detail_peturunan = DetailPeturunan.objects.filter(id=request.POST.get('id_detail_peturunan')).first()
                detail_peturunan.bayar = request.POST.get('bayar')
                detail_peturunan.save()
                messages.success(request, 'Peturunan telah berhasil diubah!')
                return redirect('/acara/{}/peturunan'.format(acara.id))


    else:
        form = PeturunanForm()
    
    response['detail_peturunan'] = DetailPeturunan.objects.filter(peturunan=peturunan, status=True)
    response['acara'] = Acara.objects.filter(id=id).first()
    jumlah_masuk = 0
    for data in DetailPeturunan.objects.filter(peturunan=peturunan, status=True):
        jumlah_masuk += data.bayar
    response['jumlah_masuk'] = jumlah_masuk
    response['peturunan'] = peturunan
    response['total_tambahan_bayar'] = peturunan.tambahan_bayar*TambahanPeturunan.objects.filter(peturunan=peturunan).count()
    response['sisa'] = peturunan.jumlah_peturunan + response['total_tambahan_bayar'] - jumlah_masuk
    response['form'] = form
    response['semua_pengguna'] = Pengguna.objects.all()
    response['id_acara'] = id
    response['ada_data'] = len(DetailPeturunan.objects.filter(peturunan=peturunan,status=True))>0
    return render(request, 'main/peturunan.html', response)


def tunggakan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    response = {}
    response['data'] = []
    response['jumlah'] = 0

    acara = Acara.objects.filter(id=id).first()
    if acara:
        response['acara'] = acara
        peturunan = Peturunan.objects.filter(acara=acara).first()
        if peturunan:
            response['peturunan'] = peturunan
            semua_pengguna = Pengguna.objects.order_by('nama')
            for pengguna in semua_pengguna:
                sum_queryset = DetailPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan, status=True).aggregate(Sum('bayar'))
                bayar = sum_queryset['bayar__sum'] if sum_queryset['bayar__sum'] else 0
                tambahan = TambahanPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan)
                if tambahan:
                    sisa = peturunan.jumlah_bayar_tiap_anggota + peturunan.tambahan_bayar - bayar
                else:
                    sisa = peturunan.jumlah_bayar_tiap_anggota - bayar
                
                lebih = 0 if sisa > 0 else abs(sisa)
                sisa = 0 if sisa < 0 else sisa

                terakhir_bayar = DetailPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan, status=True).order_by('-id').first()
                response['data'].append({
                    'pengguna':pengguna,
                    'sisa':sisa,
                    'terakhir_bayar':terakhir_bayar.tanggal_bayar if terakhir_bayar else 'Belum Bayar',
                    'lebih':lebih
                })
                response['jumlah'] += sisa

    if request.method == 'POST':
        if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
            form = PeturunanForm(request.POST)
            
            if request.POST['btn'] == 'Tambah':
                pengguna = Pengguna.objects.filter(id=request.POST.get('pengguna')).first()
                detail_peturunan = DetailPeturunan.objects.create(
                    peturunan=peturunan,
                    pengguna=pengguna,
                    tanggal_bayar=timezone.now(),
                    bayar=request.POST.get('bayar'),
                    diapprove_oleh=Pengguna.objects.filter(user=request.user).first(),
                    status=True,
                    tanggal_approve=timezone.now()
                )
                detail_peturunan.save()
                messages.success(request, 'Peturunan telah berhasil dimasukkan!')
                return redirect('/acara/{}/tunggakan'.format(acara.id))
    else:
        form = PeturunanForm()

    response['form'] = form
    response['total_tambahan_bayar'] = peturunan.tambahan_bayar*TambahanPeturunan.objects.filter(peturunan=peturunan).count()
    response['total_tunggakan'] = peturunan.jumlah_peturunan + response['total_tambahan_bayar'] - response['jumlah']

    return render(request, 'main/tunggakan.html', response)


def biaya_tambahan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    semua_pengguna = Pengguna.objects.all()
    acara = Acara.objects.filter(id=id).first()

    if acara:
        peturunan = Peturunan.objects.filter(acara=acara).first()
        response['data'] = []
        if peturunan:
            for pengguna in semua_pengguna:
                tambahan_peturunan = TambahanPeturunan.objects.filter(peturunan=peturunan, pengguna=pengguna).first()
                response['data'].append({
                    'pengguna':pengguna,
                    'tambahan_peturunan':True if tambahan_peturunan else False
                })

    if request.method == 'POST':
        form = BiayaTambahanForm(request.POST)
        if form.is_valid():
            peturunan.tambahan_bayar = request.POST.get('tambahan_bayar')
            queryset_dana = Dana.objects.filter(acara=acara, deskripsi="Biaya Tambahan Untuk Semeton Pedesaan").first()
            
            ke = []
            for pengguna in semua_pengguna:
                if str(pengguna.id) in request.POST:
                    if request.POST.get(str(pengguna.id)) == 'true':
                        if not TambahanPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan).first():
                            tp = TambahanPeturunan.objects.create(
                                peturunan=peturunan,
                                pengguna=pengguna
                            )
                            tp.save()
                            ke.append(pengguna)
                else:
                    if TambahanPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan).first():
                        tp = TambahanPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan).first()
                        if tp:
                            tp.delete()

            dari = request.user.pengguna
            pesan = "Anda dikenakan biaya pedesaan sebesar {}!".format(str(request.POST.get('tambahan_bayar')))
            url = "/acara/{}/biaya-tambahan".format(acara.id)
            kirim(dari, ke, pesan, url)
            
            if queryset_dana == None:
                dana = Dana.objects.create(
                    acara=acara,
                    tipe="Pemasukan",
                    deskripsi="Biaya Tambahan Untuk Semeton Pedesaan",
                    jumlah=int(peturunan.tambahan_bayar)*TambahanPeturunan.objects.filter(peturunan=peturunan).count(),
                    struk=None
                )
                dana.save()
            else:
                queryset_dana.jumlah = int(peturunan.tambahan_bayar)*TambahanPeturunan.objects.filter(peturunan=peturunan).count()
                queryset_dana.save()
            peturunan.save()

            messages.success(request, 'Biaya Semeton Pedesaan Telah Berhasil Disimpan')
            return redirect('/acara/{}/biaya-tambahan'.format(id))
    else:
        form = BiayaTambahanForm()
    
    
    response['form'] = form
    response['acara'] = acara
    response['peturunan'] = peturunan

    return render(request, 'main/biaya-tambahan.html', response)


def validasi_bayar_transfer(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    response = {}
    acara = Acara.objects.filter(id=id).first()
    response['ada_data'] = False
    if acara:
        response['acara'] = acara
        peturunan = Peturunan.objects.filter(acara=acara).first()
        if peturunan:
            response['peturunan'] = peturunan
            detail = DetailPeturunan.objects.filter(peturunan=peturunan, status=False, alasan=None).order_by('-id')
            response['detail_peturunan'] = detail
            total = detail.aggregate(Sum('bayar'))['bayar__sum']
            response['total'] = total if total else 0
            response['ada_data'] = len(detail) > 0 
    
    if request.method == 'POST':
        form = TolakForm(request.POST)
        if form.is_valid():
            detail = DetailPeturunan.objects.filter(id=request.POST.get('id_detail_peturunan')).first()
            if detail:
                detail.alasan = form.cleaned_data['alasan']
                detail.save()
                dari = request.user.pengguna
                ke = [detail.pengguna]
                pesan = "{} menolak pembayaran anda dengan alasan {}".format(request.user.pengguna.tipe, form.cleaned_data['alasan'])
                url = "/acara/"
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Alasan Ditolak Berhasil Dikirim Ke Anggota Bersangkutan!')
    response['form'] = TolakForm()
    return render(request, 'main/validasi_bayar_transfer.html', response)


def validasi_transfer(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    detail = DetailPeturunan.objects.filter(id=id).first()
    if detail:
        detail.status = True
        detail.tanggal_approve = timezone.now()
        detail.diapprove_oleh = request.user.pengguna
        detail.save()
        dari = request.user.pengguna
        ke = [detail.pengguna]
        pesan = "{} telah memvalidasi pembayaran anda!".format(request.user.pengguna.tipe)
        url = "/acara/"
        kirim(dari, ke, pesan, url)
        messages.success(request, 'Pembayaran berhasil divalidasi!')

    return redirect('/acara/{}/validasi-bayar-transfer/'.format(id_acara))


def tolak_transfer(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    if request.method == 'POST':
        form = TolakForm(request.POST)
        if form.is_valid():
            detail = DetailPeturunan.objects.filter(id=id).first()
            if detail:
                detail.alasan = form.cleaned_data['alasan']
                messages.success(request, 'Alasan Ditolak Berhasil Dikirim Ke Anggota Bersangkutan!')


    return redirect('/acara/{}/validasi-bayar-transfer/'.format(id_acara))


def validasi_pengajuan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    response = {}
    acara = Acara.objects.filter(id=id).first()
    response['ada_data'] = False
    if acara:
        response['acara'] = acara
        pengajuan = Pengajuan.objects.filter(acara=acara, status=False, alasan=None).order_by('-id')
        response['pengajuan'] = pengajuan
        response['ada_data'] = len(pengajuan) > 0 

    if request.method == 'POST':
        form = TolakForm(request.POST)
        if form.is_valid():
            pengajuan = Pengajuan.objects.filter(id=request.POST.get('id_pengajuan')).first()
            if pengajuan:
                pengajuan.alasan = form.cleaned_data['alasan']
                pengajuan.save()
                messages.success(request, 'Alasan Ditolak Berhasil Dikirim Ke Bendahara!')
                return redirect('/acara/{}/validasi-pengajuan/'.format(acara.id))

    response['form'] = TolakForm()
    return render(request, 'main/validasi_pengajuan.html', response)


def terima_pengajuan(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    pengajuan = Pengajuan.objects.filter(id=id).first()
    if pengajuan:
        pengajuan.status = True
        pengajuan.tanggal_diapprove = timezone.now()
        pengajuan.diapprove_oleh = request.user.pengguna

        acara = Acara.objects.filter(id=id_acara).first()
        if acara:
            dana = Dana.objects.create(
                acara=acara,
                tipe='Pemasukan',
                deskripsi='Pengajuan Dana ({})'.format(pengajuan.deskripsi),
                jumlah=pengajuan.jumlah
            )
            kas = Kas.objects.create(
                tipe='Pengeluaran',
                deskripsi='Pengajuan Dana ({}) di Acara ({})'.format(pengajuan.deskripsi, acara.judul),
                jumlah=pengajuan.jumlah
            )
            pengajuan.save()
            dana.save()
            kas.save()
            messages.success(request, 'Pengajuan berhasil diterima!')
    return redirect('/acara/{}/validasi-pengajuan/'.format(id_acara))


def get_pengajuan(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    pengajuan = Pengajuan.objects.filter(id=id).first()
    if pengajuan:
        serialized_obj = serializers.serialize('json', [ pengajuan ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def pengguna(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    response = {}
    if request.method == 'POST':
        form = PenggunaForm(request.POST)
        if form.is_valid():
            if request.POST['btn'] == 'Tambah':
                password = generate_random_password()
                user = User.objects.create(
                    username = generate_random_password(),
                    email = password
                )
                user.set_password(password)
                user.save()
                pengguna = Pengguna.objects.create(
                    user = user,
                    nama = form.cleaned_data['nama'],
                    tipe = form.cleaned_data['tipe'],
                    status = False
                )
                pengguna.save()
                update_acara()
                messages.success(request, 'Data anggota berhasil dimasukkan!')
            elif request.POST['btn'] == 'Ubah':
                pengguna = Pengguna.objects.filter(id=request.POST.get('id_anggota')).first()
                pengguna.tipe = request.POST.get('tipe')
                pengguna.save()
                messages.success(request, 'Data anggota berhasil diubah!')
    else:
        form = PenggunaForm()
    
    
    response['form'] = form
    response['semua_pengguna'] = Pengguna.objects.order_by('nama')
    
    return render(request, 'main/pengguna.html', response)


def update_profile(request):
    response = {}

    if request.method == 'POST':
        if request.FILES:
            form = Register(request.POST, request.FILES)
            if form.is_valid():
                pengguna = Pengguna.objects.filter(pk=request.session.get('pengguna_id')).first()
                pengguna.nama = form.cleaned_data['nama']
                pengguna.no_ktp = form.cleaned_data['no_ktp']
                pengguna.foto_ktp = form.cleaned_data['foto_ktp']
                pengguna.user.email = form.cleaned_data['email']
                pengguna.no_hp = form.cleaned_data['no_hp']
                pengguna.alasan = None
                pengguna.save()
                pengguna.user.save()
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.filter(tipe='Admin')]
                pesan = "{} meminta validasi akun!".format(pengguna.nama)
                url = "/validasi-anggota/"
                kirim(dari, ke, pesan, url)
                messages.info(request, 'Data berhasil diupdate! Harap tunggu validasi dari Admin dan mohon terus mengecek status akun anda dengan login menggunakan username dan password yang telah dibuat!')
                auth_logout(request)
                return redirect('/acara/')
        else:
            form = Register(request.POST, request.FILES)
    else:
        form = Register()

    pengguna_id = request.session.get('pengguna_id')
    if pengguna_id:
        pengguna = Pengguna.objects.filter(pk=pengguna_id).first()
        if pengguna:
            form.initial['nama'] = pengguna.nama
            form.initial['no_ktp'] = pengguna.no_ktp
            form.initial['no_hp'] = pengguna.no_hp
    response['form'] = form

    return render(request, 'main/update_profile.html', response)


def profile(request):
    response = {}
    pengguna = Pengguna.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        if request.FILES:
            form = ProfileForm(request.POST, request.FILES)
        else:
            form = ProfileForm(request.POST)

        if form.is_valid():
            pengguna.nama = form.cleaned_data['nama']
            pengguna.email = form.cleaned_data['email']
            pengguna.no_hp = form.cleaned_data['no_hp']
            pengguna.user.username = form.cleaned_data['username']
            if form.cleaned_data['foto_profile']:
                pengguna.foto_profile = form.cleaned_data['foto_profile']
            pengguna.save()
            pengguna.user.save()
            if form.cleaned_data['password_lama'] or form.cleaned_data['password_baru'] or form.cleaned_data['password_validasi']:
                if form.cleaned_data['password_lama']:
                    if pengguna.user.check_password(form.cleaned_data['password_lama']):
                        if form.cleaned_data['password_baru'] == form.cleaned_data['password_validasi']:
                            pengguna.user.set_password(form.cleaned_data['password_baru'])
                            pengguna.user.save()
                            user = authenticate(username=pengguna.user.username, password=form.cleaned_data['password_baru'])
                            if user is not None:
                                auth_login(request, user)
                                messages.success(request, 'Profile anda berhasil dirubah!')
                        else:
                            messages.error(request, 'Password baru tidak sama dengan validasi password!')
                    else:
                        messages.error(request, 'Password lama salah!')
                else:
                    messages.error(request, 'Password lama kosong!')
            else:
                messages.success(request, 'Profile anda berhasil dirubah!')
    else:
        form = ProfileForm()

    form.initial['nama'] = pengguna.nama
    form.initial['no_ktp'] = pengguna.no_ktp
    form.initial['no_hp'] = pengguna.no_hp
    form.initial['email'] = pengguna.user.email
    form.initial['tipe'] = pengguna.tipe
    form.initial['username'] = pengguna.user.username

    response['form'] = form    
    response['pengguna'] = pengguna


    return render(request, 'main/profile.html', response)


def hapus_anggota(request, id):
    pengguna = Pengguna.objects.filter(id=id).first()
    user = pengguna.user
    user.delete()
    update_acara()
    messages.success(request, 'Data anggota berhasil dihapus!')
    return redirect('/anggota/')


def get_anggota(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    pengguna = Pengguna.objects.filter(id=id).first()
    if pengguna:
        serialized_obj = serializers.serialize('json', [ pengguna ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def validasi_pengguna(request):
    response = {}
    pengguna = Pengguna.objects.filter(status=False, alasan=None)
    if request.method == 'POST':
        form = TolakForm(request.POST)
        if form.is_valid():
            pengguna = Pengguna.objects.filter(id=request.POST.get('id_anggota')).first()
            if pengguna:
                pengguna.no_ktp = None
                pengguna.no_hp = None
                pengguna.foto_ktp = None
                pengguna.foto_profile = None
                pengguna.alasan = form.cleaned_data['alasan']
                pengguna.save()
                messages.success(request, 'Request akses pengguna berhasil ditolak!')
                return redirect('/validasi-anggota/')
    else:
        form = TolakForm()
    
    response['form'] = form
    response['semua_pengguna'] = pengguna.filter(~Q(no_ktp=None)).order_by('-id')
    response['ada_data'] = len(response['semua_pengguna']) > 0
    return render(request, 'main/validasi_pengguna.html', response)


def terima_anggota(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    pengguna = Pengguna.objects.filter(id=id).first()
    if pengguna:
        pengguna.status = True
        pengguna.alasan = None
        pengguna.save()
        dari = request.user.pengguna
        ke = [p for p in Pengguna.objects.filter(id=pengguna.id)]
        pesan = "Admin menerima validasi akun anda!"
        url = ""
        kirim(dari, ke, pesan, url)
        messages.success(request, 'Request akses pengguna berhasil diterima!')
    else:
        messages.error(request, 'Terjadi kesalahan!')
    update_acara()
    
    return redirect('/validasi-anggota/')


def kas(request):
    response = {}
    
    semua_kas = Kas.objects.all()
    if request.method == 'POST':
        form = KasForm(request.POST)
        if form.is_valid():
            if request.POST.get('btn') == 'Tambah':
                kas = Kas.objects.create(
                    tipe=form.cleaned_data['tipe'],
                    deskripsi=form.cleaned_data['deskripsi'],
                    jumlah=form.cleaned_data['jumlah'],
                    status=True,
                )
                kas.save()
                messages.success(request, 'Data kas berhasil ditambahkan!')
            elif request.POST.get('btn') == 'Ubah':
                kas = Kas.objects.filter(id=request.POST.get('id_kas')).first()
                kas.tipe = form.cleaned_data['tipe'],
                kas.deskripsi = form.cleaned_data['deskripsi']
                kas.jumlah = form.cleaned_data['jumlah']
                kas.save()
                messages.success(request, 'Data kas berhasil diubah!')
    else:
        form = KasForm()
    
    response['form'] = form
    jumlah_pengeluaran = semua_kas.filter(tipe='Pengeluaran').aggregate(Sum('jumlah'))['jumlah__sum']
    jumlah_pemasukan = semua_kas.filter(tipe='Pemasukan').aggregate(Sum('jumlah'))['jumlah__sum']
    response['semua_kas'] = semua_kas
    response['ada_data'] = len(response['semua_kas']) > 0
    response['jumlah_pengeluaran'] = jumlah_pengeluaran if jumlah_pengeluaran else 0
    response['jumlah_pemasukan'] = jumlah_pemasukan if jumlah_pemasukan else 0
    response['total'] = response['jumlah_pemasukan'] - response['jumlah_pengeluaran']
    return render(request, 'main/kas.html', response)


def get_kas(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    kas = Kas.objects.filter(id=id).first()
    if kas:
        serialized_obj = serializers.serialize('json', [ kas, ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/acara/')


def hapus_kas(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    if check_perm(request, 'Admin') or check_perm(request, 'Bendahara'):
        kas = Kas.objects.filter(id=id).first()
        if kas:
            kas.delete()
            messages.success(request, "Kas telah berhasil dihapus!")
    return redirect('/kas/')


def like_usulan(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    usulan = Usulan.objects.filter(id=id).first()
    like_usulan = LikeUsulan.objects.create(
        usulan=usulan,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=True
    )
    like_usulan.save()
    usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()

    dislike = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=False).first()
    if dislike:
        dislike.delete()
        usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()
    
    usulan.save()

    return redirect('/acara/{}#{}'.format(str(id_acara), str(usulan.id)))


def dislike_usulan(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    usulan = Usulan.objects.filter(id=id).first()
    like_usulan = LikeUsulan.objects.create(
        usulan=usulan,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=False
    )
    like_usulan.save()
    usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()

    like = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=True).first()
    if like:
        like.delete()
        usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()
    
    usulan.save()

    return redirect('/acara/{}#{}'.format(str(id_acara), str(usulan.id)))


def hapus_like_usulan(request, id, id_acara):
    usulan = Usulan.objects.filter(id=id).first()
    if usulan:
        like = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=True).first()
        like.delete()
        usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()
    
    usulan.save()
    
    return redirect('/acara/{}#{}'.format(str(id_acara), str(usulan.id)))


def hapus_dislike_usulan(request, id, id_acara):
    usulan = Usulan.objects.filter(id=id).first()
    if usulan:
        dislike = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=False).first()
        dislike.delete()
        usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()
    
    usulan.save()
    
    return redirect('/acara/{}#{}'.format(str(id_acara), str(usulan.id)))


def detail_usulan(request, id_acara, id):
    response = {}
    usulan = Usulan.objects.filter(id=id).first()
    acara = Acara.objects.filter(id=id_acara).first()

    if request.method == "POST":
        if request.POST.get('komentar'):
                comment = CommentUsulan.objects.create(
                    usulan=usulan,
                    pengusul=request.user.pengguna,
                    usulan_comment=request.POST.get('komentar'),
                    tanggal=timezone.now(),
                    like=0,
                    dislike=0
                )
                comment.save()
                messages.success(request, 'Komentar sudah berhasil ditambahkan!')

    response['acara'] = acara
    response['usulan'] = usulan
    # response['semua_comment'] = CommentUsulan.objects.filter(usulan=usulan)
    semua_comment = CommentUsulan.objects.filter(usulan=usulan).order_by('-id')
    mapped_comment = []
    for comment in semua_comment:
        sudah_like = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=True).first()
        sudah_dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=False).first()
        mapped_comment.append({'comment':comment, 'like':sudah_like, 'dislike':sudah_dislike})
    response['semua_comment'] = mapped_comment
    return render(request, 'main/detail_usulan.html', response)


def detail_like_usulan(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    usulan = Usulan.objects.filter(id=id).first()
    like_usulan = LikeUsulan.objects.create(
        usulan=usulan,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=True
    )
    like_usulan.save()
    usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()

    dislike = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=False).first()
    if dislike:
        dislike.delete()
        usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()
    
    usulan.save()

    return redirect('/acara/{}/usulan/{}'.format(str(id_acara), str(usulan.id)))


def detail_dislike_usulan(request, id, id_acara):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    usulan = Usulan.objects.filter(id=id).first()
    like_usulan = LikeUsulan.objects.create(
        usulan=usulan,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=False
    )
    like_usulan.save()
    usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()

    like = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=True).first()
    if like:
        like.delete()
        usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()
    
    usulan.save()

    return redirect('/acara/{}/usulan/{}'.format(str(id_acara), str(usulan.id)))


def hapus_detail_like_usulan(request, id, id_acara):
    usulan = Usulan.objects.filter(id=id).first()
    if usulan:
        like = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=True).first()
        like.delete()
        usulan.like = LikeUsulan.objects.filter(usulan=usulan, tipe=True).count()
    
    usulan.save()
    
    return redirect('/acara/{}/usulan/{}'.format(str(id_acara), str(usulan.id)))


def hapus_detail_dislike_usulan(request, id, id_acara):
    usulan = Usulan.objects.filter(id=id).first()
    if usulan:
        dislike = LikeUsulan.objects.filter(usulan=usulan, pengusul=request.user.pengguna, tipe=False).first()
        dislike.delete()
        usulan.dislike = LikeUsulan.objects.filter(usulan=usulan, tipe=False).count()
    
    usulan.save()
    
    return redirect('/acara/{}/usulan/{}'.format(str(id_acara), str(usulan.id)))


def like_comment(request, id_acara, id_usulan, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    comment = CommentUsulan.objects.filter(id=id).first()
    like_comment = LikeCommentUsulan.objects.create(
        comment_usulan=comment,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=True
    )
    like_comment.save()
    comment.like = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=True).count()

    dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=False).first()
    if dislike:
        dislike.delete()
        comment.dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=False).count()
    
    comment.save()

    return redirect('/acara/{}/usulan/{}#{}'.format(str(id_acara), str(id_usulan), str(id)))


def dislike_comment(request, id_acara, id_usulan, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    comment = CommentUsulan.objects.filter(id=id).first()
    like_comment = LikeCommentUsulan.objects.create(
        comment_usulan=comment,
        pengusul=request.user.pengguna,
        tanggal=timezone.now(),
        tipe=False
    )
    like_comment.save()
    comment.dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=False).count()

    like = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=True).first()
    if like:
        like.delete()
        comment.like = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=True).count()
    
    comment.save()
    return redirect('/acara/{}/usulan/{}#{}'.format(str(id_acara), str(id_usulan), str(id)))


def hapus_like_comment(request, id_acara, id_usulan, id):
    comment = CommentUsulan.objects.filter(id=id).first()
    if comment:
        like = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=True).first()
        like.delete()
        comment.like = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=True).count()
    
    comment.save()
    
    return redirect('/acara/{}/usulan/{}#{}'.format(str(id_acara), str(id_usulan), str(id)))


def hapus_dislike_comment(request, id_acara, id_usulan, id):
    comment = CommentUsulan.objects.filter(id=id).first()
    if comment:
        dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, pengusul=request.user.pengguna, tipe=False).first()
        dislike.delete()
        comment.dislike = LikeCommentUsulan.objects.filter(comment_usulan=comment, tipe=False).count()
    
    comment.save()
    
    return redirect('/acara/{}/usulan/{}#{}'.format(str(id_acara), str(id_usulan), str(id)))


def get_notifikasi(request):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    notifikasi = [{'id':n.id, 'dari':n.dari.nama, 'pesan':n.pesan, 'url':n.url, 'sudah_dibaca':n.sudah_dibaca} for n in Notifikasi.objects.filter(ke=request.user.pengguna).order_by('id')[5:][::-1]]
    count = 0
    for n in notifikasi:
        if n['sudah_dibaca']:
            count+=1
            
    serialized_obj = {'notifikasi':notifikasi, 'sudah_dibaca':count == len(notifikasi)}
    return JsonResponse(serialized_obj, safe=False)
    

def baca_notifikasi(request, id):
    notifikasi = Notifikasi.objects.filter(id=id).first()
    notifikasi.sudah_dibaca = True
    notifikasi.save()
    return redirect(request.GET.get('next'))


def notifikasi(request):
    response = {}
    notifikasi = Notifikasi.objects.filter(ke=request.user.pengguna).order_by('-id')
    for n in notifikasi:
        n.sudah_dibaca = True
        n.save()
    response['semua_notifikasi'] = notifikasi
    return render(request, 'main/notifikasi.html', response)


def pengumuman(request):
    response = {}
    semua_pengumuman = Pengumuman.objects.all().order_by('-id')
    if request.method == 'POST':
        form = PengumumanForm(request.POST)
        if form.is_valid():
            if request.POST.get('btn') == 'Tambah':
                pengumuman = Pengumuman.objects.create(
                    judul=form.cleaned_data['judul'],
                    deskripsi=form.cleaned_data['deskripsi'],
                    tanggal=timezone.now(),
                    dibuat_oleh=request.user.pengguna
                )
                pengumuman.save()
                dari = request.user.pengguna
                ke = [p for p in Pengguna.objects.all()]
                pesan = "Pengumuman {} telah dibuat!".format(form.cleaned_data['judul'])
                url = "/Pengumuman/"
                kirim(dari, ke, pesan, url)
                messages.success(request, 'Pengumuman berhasil dibuat!')
            elif request.POST.get('btn') == 'Ubah':
                pengumuman = Pengumuman.objects.filter(id=request.POST.get('id_pengumuman')).first()
                pengumuman.judul = form.cleaned_data['judul']
                pengumuman.deskripsi = form.cleaned_data['deskripsi']
                pengumuman.save()
                messages.success(request, 'Pengumuman berhasil diubah!')
    else:
        form = PengumumanForm()
    
    response['form'] = form
    response['semua_pengumuman'] = semua_pengumuman
    response['ada_data'] = len(response['semua_pengumuman']) > 0
    return render(request, 'main/pengumuman.html', response)


def hapus_pengumuman(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    if check_perm(request, 'Admin'):
        pengumuman = Pengumuman.objects.filter(id=id).first()
        if pengumuman:
            pengumuman.delete()
            messages.success(request, "Pengumuman telah berhasil dihapus!")
    return redirect('/pengumuman/')


def get_pengumuman(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    pengumuman = Pengumuman.objects.filter(id=id).first()
    if pengumuman:
        serialized_obj = serializers.serialize('json', [ pengumuman, ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/pengumuman/')


def print_dana(request, id):
    response = {}
    acara = Acara.objects.filter(id=id).first()
    if acara:
        semua_dana = Dana.objects.filter(acara=acara)
        response['semua_dana'] = semua_dana
        response['acara'] = acara
        total_pengeluaran = semua_dana.filter(tipe='Pengeluaran').aggregate(Sum('jumlah'))['jumlah__sum']
        total_pemasukan = semua_dana.filter(tipe='Pemasukan').aggregate(Sum('jumlah'))['jumlah__sum']
        response['total_pengeluaran'] = total_pengeluaran if total_pengeluaran else 0
        response['total_pemasukan'] = total_pemasukan if total_pemasukan else 0
        response['total_dana'] = (total_pemasukan if total_pemasukan else 0) - (total_pengeluaran if total_pengeluaran else 0)

    return render(request, 'main/print_dana.html', response)


def print_biaya_tambahan(request, id):
    response = {}
    semua_pengguna = Pengguna.objects.all()
    acara = Acara.objects.filter(id=id).first()

    if acara:
        peturunan = Peturunan.objects.filter(acara=acara).first()
        response['data'] = []
        response['total'] = 0
        if peturunan:
            for pengguna in semua_pengguna:
                tambahan_peturunan = TambahanPeturunan.objects.filter(peturunan=peturunan, pengguna=pengguna).first()
                response['data'].append({
                    'pengguna':pengguna,
                    'tambahan_peturunan':True if tambahan_peturunan else False
                })
                response['total'] += peturunan.tambahan_bayar if tambahan_peturunan else 0
        response['acara'] = acara
        response['peturunan'] = peturunan
    return render(request, 'main/print_tambahan_biaya.html', response)


def print_peturunan(request, id):
    response = {}
    acara = Acara.objects.filter(id=id).first()
    peturunan = Peturunan.objects.filter(acara=acara).first()
    response['detail_peturunan'] = DetailPeturunan.objects.filter(peturunan=peturunan, status=True)
    response['acara'] = Acara.objects.filter(id=id).first()
    jumlah_masuk = 0
    for data in DetailPeturunan.objects.filter(peturunan=peturunan, status=True):
        jumlah_masuk += data.bayar
    response['jumlah_masuk'] = jumlah_masuk
    response['peturunan'] = peturunan
    response['total_tambahan_bayar'] = peturunan.tambahan_bayar*TambahanPeturunan.objects.filter(peturunan=peturunan).count()
    response['sisa'] = peturunan.jumlah_peturunan + response['total_tambahan_bayar'] - jumlah_masuk
    return render(request, 'main/print_peturunan.html', response)


def print_tunggakan(request, id):
    response = {}
    response['data'] = []
    response['jumlah'] = 0

    acara = Acara.objects.filter(id=id).first()
    if acara:
        response['acara'] = acara
        peturunan = Peturunan.objects.filter(acara=acara).first()
        if peturunan:
            response['peturunan'] = peturunan
            semua_pengguna = Pengguna.objects.order_by('nama')
            for pengguna in semua_pengguna:
                sum_queryset = DetailPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan, status=True).aggregate(Sum('bayar'))
                bayar = sum_queryset['bayar__sum'] if sum_queryset['bayar__sum'] else 0
                tambahan = TambahanPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan)
                if tambahan:
                    sisa = peturunan.jumlah_bayar_tiap_anggota + peturunan.tambahan_bayar - bayar
                else:
                    sisa = peturunan.jumlah_bayar_tiap_anggota - bayar
                
                lebih = 0 if sisa > 0 else abs(sisa)
                sisa = 0 if sisa < 0 else sisa

                terakhir_bayar = DetailPeturunan.objects.filter(pengguna=pengguna, peturunan=peturunan, status=True).order_by('-id').first()
                response['data'].append({
                    'pengguna':pengguna,
                    'sisa':sisa,
                    'terakhir_bayar':terakhir_bayar.tanggal_bayar if terakhir_bayar else 'Belum Bayar',
                    'lebih':lebih
                })
                response['jumlah'] += sisa

    response['total_tambahan_bayar'] = peturunan.tambahan_bayar*TambahanPeturunan.objects.filter(peturunan=peturunan).count()
    response['total_tunggakan'] = peturunan.jumlah_peturunan + response['total_tambahan_bayar'] - response['jumlah']
    
    return render(request, 'main/print_tunggakan.html', response)


def print_kas(request):
    response = {}
    semua_kas = Kas.objects.all()
    jumlah_pengeluaran = semua_kas.filter(tipe='Pengeluaran').aggregate(Sum('jumlah'))['jumlah__sum']
    jumlah_pemasukan = semua_kas.filter(tipe='Pemasukan').aggregate(Sum('jumlah'))['jumlah__sum']
    response['semua_kas'] = semua_kas
    response['jumlah_pengeluaran'] = jumlah_pengeluaran if jumlah_pengeluaran else 0
    response['jumlah_pemasukan'] = jumlah_pemasukan if jumlah_pemasukan else 0
    response['total'] = response['jumlah_pemasukan'] - response['jumlah_pengeluaran']
    return render(request, 'main/print_kas.html', response)


def get_berita(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))

    berita = Berita.objects.filter(id=id).first()
    if berita:
        serialized_obj = serializers.serialize('json', [ berita, ])
        return JsonResponse(serialized_obj, safe=False)
    else:
        return redirect('/berita/')


def hapus_berita(request, id):
    if not checkAuth(request):
        return redirect('/profile/login/?next={}'.format(request.path))
    
    berita = Berita.objects.filter(id=id).first()
    if berita:
        berita.delete()
        messages.success(request, "Berita telah berhasil dihapus!")
    return redirect('/berita/')