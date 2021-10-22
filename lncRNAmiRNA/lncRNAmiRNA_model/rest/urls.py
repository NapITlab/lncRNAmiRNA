# coding: utf-8

from django.urls import path

from lncRNAmiRNA_model.rest.views import \
	hello_world, list_lncRNA, list_microRNA, predict, list_RNA

urlpatterns = [
	path('', hello_world),
	path('list_RNA', list_RNA),
	path('list_lncRNA', list_lncRNA),
	path('list_microRNA', list_microRNA),
	path('predict', predict),
]
