import gzip
import sys
import tempfile
import time
import inspect
import typing

import psutil
import vmprof

if sys.platform.startswith('linux'):
    from psutil._common import pcputimes
    from psutil._pslinux import pfullmem
elif sys.platform.startswith('darwin'):
    from psutil._common import pcputimes
    from psutil._psosx import pfullmem
else:
    pcputimes = typing.Tuple[float, ...]
    pfullmem = typing.Tuple[int, ...]

import django.conf
import django.http
import django.utils.timezone

from .models import RequestProfile


class RequestProfiler:
    profile_file: typing.BinaryIO
    profile: RequestProfile
    process: psutil.Process
    cpu_real: float
    cpu_time: pcputimes
    cpu_diff: pcputimes
    mem_info: pfullmem
    mem_diff: pfullmem

    def __init__(self):
        self.profile_file = tempfile.TemporaryFile()
        self.process = psutil.Process()
        self.profile = RequestProfile()

    def enable(self, request: django.http.HttpRequest):
        self.profile.started_at = django.utils.timezone.now()
        self.profile.request_user_id = request.user.id
        self.profile.request_path = request.path

        self.cpu_real = time.monotonic()
        self.cpu_time = self.process.cpu_times()
        self.mem_info = self.process.memory_full_info()

        # the web view has no support for lines and memory views
        # native currently fails when trying to unload a library on next request
        # real_time is necessary for our use case - otherwise we'll only profile CPU time, which we don't care about

        vmprof.enable(self.profile_file.fileno(), lines=False, memory=False, native=False, real_time=True)

    def disable(self, response_status_code=-1):
        time_now = time.monotonic()
        self.cpu_real = time_now - self.cpu_real
        self.cpu_diff = self.cpu_time._make(q - p for (p, q) in zip(self.cpu_time, self.process.cpu_times()))
        self.mem_diff = self.mem_info._make(q - p for (p, q) in zip(self.mem_info, self.process.memory_full_info()))

        vmprof.disable()

        self.profile.created_at = django.utils.timezone.now()
        self.profile.response_code = response_status_code
        self.profile.time_real = self.cpu_real
        self.profile.time_user = self.cpu_time.user
        self.profile.time_sys = self.cpu_time.system
        self.profile.allocated_vm = self.mem_diff.vms

        self.profile_file.seek(0)
        self.profile.data = self.profile_file.read()
        self.profile_file.close()


class RequestProfilerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def profile_request(self, request: django.http.HttpRequest):
        return request.user.is_authenticated()

    def profile_response(self, request: django.http.HttpRequest, response: django.http.HttpResponse, profile: RequestProfile):
        profile.data = gzip.compress(profile.data)
        profile.save()

    def __call__(self, request: django.http.HttpRequest):
        profiler: RequestProfiler = None

        if self.profile_request(request):
            try:
                profiler = RequestProfiler()
                profiler.enable(request)
            except:
                profiler = None

        try:
            response = self.get_response(request)
        except:
            if (profiler is not None):
                profiler.disable()
            raise

        if profiler:
            profiler.disable(response.status_code)
            self.profile_response(request, response, profiler.profile)

        return response
