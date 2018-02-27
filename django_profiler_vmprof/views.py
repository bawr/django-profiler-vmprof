import gzip
import io
import json

from vmprof.profiler import read_profile

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import When, Value, Case, BooleanField
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
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
        profile_data = parse_profile(self.object)

        if (profile_data is None):
            response = HttpResponseNotFound()
        else:
            response = HttpResponse(content=profile_data, content_type='application/json; charset=utf-8')
            response['Content-Encoding'] = 'gzip'
            response['Content-Lendth'] = str(len(profile_data))

        return response


class ProfilerShortView(SuperuserRequiredMixin, DetailView):
    model = RequestProfile

    def render_to_response(self, context, **response_kwargs):
        profile_data = parse_profile(self.object)

        if (profile_data is None):
            return HttpResponseNotFound()
        else:
            return HttpResponseRedirect(
                reverse('ProfilerEntryView') + '/#/%d?id=%s' % (self.object.id, self.object.data_path)
            )


class ProfilerEntryView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_profiler_vmprof/entry.html'


class ProfilerIndexView(SuperuserRequiredMixin, ListView):
    model = RequestProfile
    model_fields = [f.name for f in model._meta.get_fields() if f.name not in ('data',)] + ['request_user_id',]
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


def parse_profile(profile: RequestProfile):
    if (profile.data and profile.data_json):
        return profile.data

    profile_dict = read_profile(io.BytesIO(profile.data))
    profile_tree = profile_dict.get_tree()
    profile_dump = profile_tree._serialize()
    profile_path = []

    cutoff_samples = int(0.85 * profile_dump[2])
    profile_next = profile_dump

    while profile_next:
        for profile_id, profile_next in enumerate(profile_next[4]):
            if (profile_next[2] > cutoff_samples):
                profile_path.append(profile_id)
                break
        else:
            break

    profile_dict = {
        "data": {
            "VM": profile_dict.interp,
            "profiles": profile_dump,
            "argv": "%s %s" % (profile_dict.interp, profile_dict.getargv()),
            "version": 2,
        }
    }

    profile_json = gzip.compress(json.dumps(profile_dict).encode('utf-8'), compresslevel=8)

    profile.data = profile_json
    profile.data_json = True
    profile.data_path = ','.join(map(str, profile_path))
    profile.size_json = len(profile_json)
    profile.save(force_update=True, update_fields=['data', 'data_json', 'data_path', 'size_json'])

    return profile_json
