import pandas as pd
from Bio import SeqIO
from django.conf import settings
from rest_framework import permissions
from rest_framework.decorators import api_view, \
	authentication_classes, \
	permission_classes
from rest_framework.response import Response

from lncRNAmiRNA_model.utils.model_utils import predict_one


class lncRNAGetter(object):
	lncRNAs = {}

	def __init__(self):
		for record in SeqIO.parse(settings.LNCRNA_FP, "fasta"):
			l_id = record.description
			seq = record.seq._data
			self.lncRNAs[l_id] = seq

	def lncRNA_by_id(self, l_id):
		if l_id not in self.lncRNAs:
			raise Exception(f"Could not find lncRNA with id '{l_id}'")
		return self.lncRNAs[l_id]

	@property
	def lncRNA_list(self):
		return self.lncRNAs.keys()


class miRNAGetter(object):
	miRNAs = {}

	def __init__(self):
		for record in SeqIO.parse(settings.MIRNA_FP, "fasta"):
			m_id = record.description.split(" ")[0]
			seq = record.seq._data
			self.miRNAs[m_id] = seq

	def miRNA_by_id(self, m_id):
		if m_id not in self.miRNAs:
			raise Exception(f"Could not find lncRNA with id '{m_id}'")
		return self.miRNAs[m_id]

	@property
	def miRNA_list(self):
		return self.miRNAs.keys()


mirna_getter = miRNAGetter()
lncrna_getter = lncRNAGetter()


@api_view(['GET', 'POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def hello_world(request):
	if request.method == 'POST':
		return Response({"message": "Got some data!", "data": request.data})
	return Response({"message": "Hello, world!"})


@api_view(['GET', ])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def list_lncRNA(request):
	return Response(lncrna_getter.lncRNA_list)


@api_view(['GET', ])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def list_microRNA(request):
	return Response(mirna_getter.miRNA_list)


@api_view(['GET', ])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def list_RNA(request):
	return Response([mirna_getter.miRNA_list, lncrna_getter.lncRNA_list])


@api_view(['POST', ])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def predict(request):
	lncrna = request.data["lncrna"]
	mirna = request.data["mirna"]
	lncrna_seq = lncrna_getter.lncRNA_by_id(lncrna)
	mirna_seq = mirna_getter.miRNA_by_id(mirna)
	data_for_predict = pd.DataFrame(
			{"mirna": mirna, "lncrna": lncrna,
				"seq": mirna_seq, "read": lncrna_seq, "target": 0.5},
			index=[0],
	)
	prob = predict_one(data_for_predict)
	return Response(prob[0])
