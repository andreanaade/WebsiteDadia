from django.contrib import admin
from .models import Pengguna, Acara, Dana, Peturunan, DetailPeturunan, Berita, Pengajuan, Pengumuman, Kas, TambahanPeturunan, Pengajuan, Usulan, LikeCommentUsulan, LikeUsulan, CommentUsulan, Notifikasi

# Register your models here.
admin.site.register(Pengguna)
admin.site.register(Notifikasi)
admin.site.register(Acara)
admin.site.register(Dana)
admin.site.register(Peturunan)
admin.site.register(DetailPeturunan)
admin.site.register(Berita)
admin.site.register(Pengumuman)
admin.site.register(Kas)
admin.site.register(TambahanPeturunan)
admin.site.register(Pengajuan)
admin.site.register(Usulan)
admin.site.register(LikeUsulan)
admin.site.register(LikeCommentUsulan)
admin.site.register(CommentUsulan)