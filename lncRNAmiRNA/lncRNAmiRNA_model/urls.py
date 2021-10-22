from django.urls import path, include
import lncRNAmiRNA_model.rest.urls

urlpatterns = [
    path('rest/', include(lncRNAmiRNA_model.rest.urls), name='lncRNAmiRNA model REST API'),
]
