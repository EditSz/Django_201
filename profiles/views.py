from django.contrib.auth.models import User
from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from .forms import UpdateImageForm, UserForm
from feed.models import Post
from followers.models import Follower
from django.contrib.auth.decorators import login_required
from profiles.models import Profile
from django.shortcuts import render


class ProfileDetailView(DetailView):
    http_method_names = ["get"]
    template_name = "profiles/detail.html"
    model = User
    context_object_name = "user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.get_object()
        context = super().get_context_data(**kwargs)
        context['total_posts'] = Post.objects.filter(author=user).count()
        context ['total_followers'] = Follower.objects.filter(following=user).count()
        if self.request.user.is_authenticated:
            context['you_follow'] = Follower.objects.filter(following=user, followed_by=self.request.user).exists()
        return context


class FollowView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if "action" not in data or "username" not in data:
            return HttpResponseBadRequest("Missing data")

        try:
            other_user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return HttpResponseBadRequest("Missing user")

        if data['action'] == "follow":
            # Follow
            follower, created = Follower.objects.get_or_create(
                followed_by=request.user,
                following=other_user
            )
        else:
            # Unfollow
            try:
                follower = Follower.objects.get(
                    followed_by=request.user,
                    following=other_user,
                )
            except Follower.DoesNotExist:
                follower = None

            if follower:
                follower.delete()

        return JsonResponse({
            'success': True,
            'wording': "Unfollow" if data['action'] == "follow" else "Follow"
        })

@login_required
def update_profile(request, username):

    try:
        user_profile = Profile.objects.get(user=request.user)
        user_info = User.objects.get(username=request.user)
    except Profile.DoesNotExist:
        return HTTPResponse("invalid user!")

    if request.method == "POST":
        update_profile_form = UserForm(data=request.POST, instance=request.user)
        update_image_form = UpdateImageForm(data=request.POST, instance=user_profile)

        if update_profile_form.is_valid() and update_image_form.is_valid():
            user = update_profile_form.save()
            profile = update_image_form.save(commit=False)
            profile.user = user

            if 'image' in request.FILES:
                profile.image = request.FILES['image']
			
            profile.save()

        else:
            print(update_profile_form.errors, update_image_form.errors)
    else:
        update_profile_form = UserForm(instance=user_info)
        update_image_form = UpdateImageForm(instance=user_profile)
	
    return render(request, 'profiles/update_profile.html', {'update_profile_form': update_profile_form, 'update_image_form': update_image_form})




