# coding: utf-8


import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy, get_resolver
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("lncRNAmiRNA_model")


class RestLogMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """

        :param request:
        :type request: HttpRequest
        :return:
        """
        logger.info("request.path: {path}".format(path=request.path))
        pass

    def process_response(self, request, response):
        """
        :param request:
        :type request: HttpRequest
        :param response:
        :type response: HttpResponse
        :return:
        """

        # api_root = reverse('api-root')

        if response.status_code == 200:
            logger_method = logger.info
        elif response.status_code == 301:  # and request.path.startswith(api_root):
            logger_method = logger.error
        else:
            logger_method = logger.warning

        logger_method("request: path='{path}', response: code={code}"
                      .format(path=request.path, code=response.status_code))

        # При работе с REST лучше в коде недопускать неправильных REST url.
        # 1. REST клиент через прокси плохо понимает ответ 301, и второй запрос получается неправильный (без backend)
        # 2. Правильный URL при первом запросе ускорит работу кода
        if response.status_code == 301:  # and request.path.startswith(api_root):
            return JsonResponse(
                {
                    'message': 'The request is not valid',
                    'explanation': 'Redirect response for REST API request is not allowed. Check requested url.'
                },
                status=400)

        return response
