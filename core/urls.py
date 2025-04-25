from django.contrib import admin
from django.urls import path
from bot import views, pdf_views, price_list
from django.conf import settings
from django.conf.urls.static import static


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('sentry-debug/', trigger_error),
    path('webapp/', views.WebAppTemplateView.as_view(), name="list"),
    # path('webapp/', views.WebAppHomePage.as_view(), name="list"),
    path("webapp/<int:pk>/", views.WebAppDetailPage.as_view(), name="detail"),
    path("webapp/category/", views.WebAppCategoryPage.as_view(), name="by_category"),
    path('pdf/', pdf_views.generate_pdf2_view, name='generate_pdf2'),
    path('pdf/<int:pk>/', pdf_views.generate_pdf_view, name='generate_pdf'),
    path('generate-multiple-pdfs/', pdf_views.generate_multiple_pdfs_view, name='generate_multiple_pdfs'),
    path('generate-price-list/', price_list.export_products_to_excel, name='generate-excel-price'),
    # path("webapp/cart/", views.WebAppCartPage.as_view(), name="cart")
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


urlpatterns += [path('', admin.site.urls),]