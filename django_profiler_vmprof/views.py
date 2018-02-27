import io

from vmprof.profiler import read_profile

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import When, Value, Case, BooleanField
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
        profile_dump = profile_tree._serialize()
        profile_type = self.kwargs['type']

        if (profile_type == 'top'):
            cutoff_samples = int(0.8 * profile_dump[2])
            while profile_dump:
                for profile_next in profile_dump[4]:
                    if (profile_next[2] > cutoff_samples):
                        profile_dump = profile_next
                        break
                else:
                    break

        profile_data = {
            "VM": profile.interp,
            "profiles": profile_dump,
            "argv": "%s %s" % (profile.interp, profile.getargv()),
            "version": 2,
        }
        return JsonResponse({"data": profile_data})


class ProfilerEntryView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_profiler_vmprof/entry.html'


class ProfilerIndexView(SuperuserRequiredMixin, ListView):
    model = RequestProfile
    model_fields = [f.name for f in model._meta.get_fields() if f.name not in ('data',)]
    template_name = 'django_profiler_vmprof/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list'] = list(
            self.object_list
                .order_by('-started_at')
                .annotate(has_data=Case(When(data=None, then=Value(False)), default=True, output_field=BooleanField()))
                .values('has_data', *self.model_fields)
        )
        return context
