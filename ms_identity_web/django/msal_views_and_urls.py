import os
import environ
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse
import logging

env = environ.Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, 'env_file'))


class MsalViews:
    def __init__(self, ms_identity_web):
        self.logger = logging.getLogger('MsalViewsLogger')
        self.ms_identity_web = ms_identity_web
        self.prefix = self.ms_identity_web.aad_config.django.auth_endpoints.prefix + "/"
        self.endpoints = self.ms_identity_web.aad_config.django.auth_endpoints

    def get_redirect_uri(self, request):
        protocol = "http" if os.environ.get('ENVIROMENT') != "PROD" else "https"
        return f"{protocol}://{request.get_host()}{reverse(self.endpoints.redirect)}"

    def url_patterns(self):
        return [
            path(self.endpoints.sign_in, self.sign_in, name=self.endpoints.sign_in),
            path(self.endpoints.edit_profile, self.edit_profile, name=self.endpoints.edit_profile),
            path(self.endpoints.redirect, self.aad_redirect, name=self.endpoints.redirect),
            path(self.endpoints.sign_out, self.sign_out, name=self.endpoints.sign_out),
            path(self.endpoints.post_sign_out, self.post_sign_out, name=self.endpoints.post_sign_out),
        ]

    def sign_in(self, request):
        self.logger.debug(f"{self.prefix}{self.endpoints.sign_in}: request received. will redirect browser to login")
        auth_url = self.ms_identity_web.get_auth_url(redirect_uri=self.get_redirect_uri(request))
        return redirect(auth_url)

    def edit_profile(self, request):
        self.logger.debug(f"{self.prefix}{self.endpoints.edit_profile}: request received. will redirect browser to edit profile")
        auth_url = self.ms_identity_web.get_auth_url(
                redirect_uri=self.get_redirect_uri(request),
                b2c_policy=self.ms_identity_web.aad_config.b2c.profile)
        return redirect(auth_url)

    def aad_redirect(self, request):
        self.logger.debug(f"{self.prefix}{self.endpoints.redirect}: request received. will process params")
        return self.ms_identity_web.process_auth_redirect(
            redirect_uri=self.get_redirect_uri(request),
            afterwards_go_to_url=reverse(os.environ.get('REDIRECT_URL_MS'))
        )

    def sign_out(self, request):
        self.logger.debug(f"{self.prefix}{self.endpoints.sign_out}: signing out username: {request.identity_context_data.username}")
        return self.ms_identity_web.sign_out(request.build_absolute_uri(reverse(self.endpoints.post_sign_out)))

    def post_sign_out(self, request):
        self.logger.debug(f"{self.prefix}{self.endpoints.post_sign_out}: clearing session for username: {request.identity_context_data.username}")
        self.ms_identity_web.remove_user(request.identity_context_data.username)
        return redirect(reverse(os.environ.get('REDIRECT_URL_MS')))
