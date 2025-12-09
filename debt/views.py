from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.http import HttpResponse
from .models import CongNo, LichSuThanhToan
from .forms import CongNoForm


class CongNoListView(ListView):
    model = CongNo
    template_name = 'debt/congno_list.html'
    context_object_name = 'cong_no_list'

    def get_queryset(self):
        return CongNo.objects.select_related('nha_cung_cap').all().order_by('-ngay_tao')


class CongNoDetailView(DetailView):
    model = CongNo
    template_name = 'debt/congno_detail.html'
    context_object_name = 'congno'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lich_su_thanh_toan'] = self.object.lich_su_thanh_toan.all().order_by('-ngay_thanh_toan')
        return context

def congno_create(request):
    if request.method == 'POST':
        form = CongNoForm(request.POST)
        if form.is_valid():
            congno = form.save()
            messages.success(request, f'Đã tạo công nợ {congno.ma_cong_no}')
            return redirect('debt:congno_list')
        else:
            messages.error(request, 'Lỗi khi tạo công nợ')
    else:
        form = CongNoForm()

    return render(request, 'debt/congno_form.html', {'form': form})


def thanh_toan_cong_no(request, pk):
    """Thanh toán"""
    if request.method == 'POST':
        congno = get_object_or_404(CongNo, pk=pk)

        if congno.so_tien_con_lai > 0:
            # Tạo lịch sử thanh toán
            LichSuThanhToan.objects.create(
                cong_no=congno,
                so_tien=congno.so_tien_con_lai,
                nguoi_thanh_toan=request.user
            )

            # Cập nhật số tiền còn lại
            congno.so_tien_con_lai = 0
            congno.save()

            messages.success(request, f'Đã thanh toán {congno.so_tien:,.0f} ₫')
        else:
            messages.info(request, 'Công nợ đã được thanh toán')

    return redirect('debt:congno_detail', pk=pk)