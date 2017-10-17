import io

from vmprof.profiler import read_profile

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import F, Func, When, Value, Case, BooleanField
from django.http import Http404
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import RequestProfile


class SuperuserRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        user: User = self.request.user
        return user.is_active and user.is_superuser


class ProfilerEntryJSON(SuperuserRequiredMixin, DetailView):
    model = RequestProfile

    def render_to_response(self, context, **response_kwargs):
        data = self.object.data
        if (data is None):
            raise Http404()
        profile = read_profile(io.BytesIO(data))
        profile_tree = profile.get_tree()
        profile_data = {
            "VM": profile.interp,
            "profiles": profile_tree._serialize(),
            "argv": "%s %s" % (profile.interp, profile.getargv()),
            "version": 2,
        }
        return JsonResponse({"data": profile_data})


class ProfilerEntryView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_profiler_vmprof/entry.html'


class ProfilerIndexView(SuperuserRequiredMixin, ListView):
    model = RequestProfile
    template_name = 'django_profiler_vmprof/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list'] = list(
            self.object_list
                .order_by('-started_at')
                .defer('data')
                .annotate(has_data=Case(When(data=None, then=Value(False)), default=True, output_field=BooleanField()))
                .values()
        )
        return context
