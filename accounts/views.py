from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from .models import User, CraftsmanProfile, CraftsmanPortfolio, County, City
from .forms import (
    UserRegistrationForm, CraftsmanRegistrationForm, ProfileUpdateForm,
    SimpleUserRegistrationForm, SimpleCraftsmanRegistrationForm,
    CraftsmanPortfolioForm, BulkPortfolioUploadForm, CraftsmanSkillsForm
)


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Contul a fost creat cu succes! Te poți conecta acum.')
        return response


class SimpleRegisterView(CreateView):
    """Simplified registration view similar to MyHammer"""
    model = User
    form_class = SimpleUserRegistrationForm
    template_name = 'accounts/simple_register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Contul a fost creat cu succes! Bun venit pe Bricli!')
        return response


class SimpleCraftsmanRegisterView(CreateView):
    """Simplified craftsman registration view"""
    model = User
    form_class = SimpleCraftsmanRegistrationForm
    template_name = 'accounts/simple_craftsman_register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Contul de meșter a fost creat cu succes! Bun venit pe Bricli!')
        return response


class CraftsmanRegisterView(CreateView):
    model = User
    form_class = CraftsmanRegistrationForm
    template_name = 'accounts/craftsman_register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.user_type = 'craftsman'
        user.save()

        # Create craftsman profile
        CraftsmanProfile.objects.create(user=user)

        messages.success(self.request, 'Contul de meșter a fost creat cu succes! Te poți conecta acum.')
        return redirect(self.success_url)


class LoginView(BaseLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:home')


class LogoutView(BaseLogoutView):
    template_name = 'registration/logged_out.html'
    next_page = reverse_lazy('core:home')
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        from django.contrib.auth import logout
        logout(request)
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Handle POST requests for logout"""
        return super().post(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.user_type == 'craftsman':
            try:
                context['craftsman_profile'] = self.request.user.craftsman_profile
            except CraftsmanProfile.DoesNotExist:
                CraftsmanProfile.objects.create(user=self.request.user)
                context['craftsman_profile'] = self.request.user.craftsman_profile
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user


class CraftsmanDetailView(DetailView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsman_detail.html'
    context_object_name = 'craftsman'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.received_reviews.all()[:5]
        context['portfolio'] = self.object.portfolio_images.all()[:6]
        return context


class CraftsmenListView(ListView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsmen_list.html'
    context_object_name = 'craftsmen'
    paginate_by = 12

    def get_queryset(self):
        queryset = CraftsmanProfile.objects.filter(user__is_active=True)

        # Filter by county
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county_id=county)

        # Filter by service
        service = self.request.GET.get('service')
        if service:
            queryset = queryset.filter(services__service_id=service)

        # Search by name or company
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(company_name__icontains=search)
            )

        return queryset.order_by('-average_rating', '-total_reviews')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counties'] = County.objects.all()
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profilul a fost actualizat cu succes!')
        return super().form_valid(form)


class CraftsmenListView(ListView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsmen_list.html'
    context_object_name = 'craftsmen'
    paginate_by = 12

    def get_queryset(self):
        queryset = CraftsmanProfile.objects.filter(user__is_active=True)

        # Filter by trade
        trade = self.request.GET.get('trade')
        if trade:
            queryset = queryset.filter(trade=trade)

        # Filter by county
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county_id=county)

        # Filter by rating
        rating = self.request.GET.get('rating')
        if rating:
            queryset = queryset.filter(average_rating__gte=rating)

        return queryset.order_by('-user__is_verified', '-average_rating', '-total_reviews')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'counties': County.objects.all().order_by('name'),
            'total_craftsmen': CraftsmanProfile.objects.filter(user__is_active=True).count(),
            'verified_craftsmen': CraftsmanProfile.objects.filter(
                user__is_active=True, user__is_verified=True
            ).count(),
        })
        return context


class CraftsmanDetailView(DetailView):
    model = CraftsmanProfile
    template_name = 'accounts/craftsman_detail.html'
    context_object_name = 'craftsman'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add portfolio images
        context['portfolio_images'] = self.object.portfolio_images.all()[:6]
        # Add reviews, etc.
        return context


class CraftsmanPortfolioView(LoginRequiredMixin, TemplateView):
    """View for managing craftsman portfolio"""
    template_name = 'accounts/craftsman_portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            craftsman = self.request.user.craftsman_profile
            context['craftsman'] = craftsman
            context['portfolio_images'] = craftsman.portfolio_images.all()
            context['upload_form'] = CraftsmanPortfolioForm()
            context['bulk_upload_form'] = BulkPortfolioUploadForm()
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')
        return context


class PortfolioUploadView(LoginRequiredMixin, CreateView):
    """View for uploading single portfolio image"""
    model = CraftsmanPortfolio
    form_class = CraftsmanPortfolioForm
    template_name = 'accounts/portfolio_upload.html'

    def form_valid(self, form):
        try:
            form.instance.craftsman = self.request.user.craftsman_profile
            messages.success(self.request, 'Imaginea a fost adăugată în portfolio.')
            return super().form_valid(form)
        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')

    def get_success_url(self):
        return reverse_lazy('accounts:portfolio')


class BulkPortfolioUploadView(LoginRequiredMixin, FormView):
    """View for uploading multiple portfolio images"""
    form_class = BulkPortfolioUploadForm
    template_name = 'accounts/bulk_portfolio_upload.html'

    def form_valid(self, form):
        try:
            craftsman = self.request.user.craftsman_profile
            images = form.get_images()

            created_count = 0
            for image in images:
                CraftsmanPortfolio.objects.create(
                    craftsman=craftsman,
                    image=image,
                    title=f"Lucrare {created_count + 1}"
                )
                created_count += 1

            messages.success(
                self.request,
                f'Au fost încărcate {created_count} imagini în portfolio.'
            )
            return redirect('accounts:portfolio')

        except CraftsmanProfile.DoesNotExist:
            messages.error(self.request, 'Nu ai un profil de meșter.')
            return redirect('accounts:profile')

    def get_success_url(self):
        return reverse_lazy('accounts:portfolio')


class PortfolioDeleteView(LoginRequiredMixin, DetailView):
    """View for deleting portfolio image"""
    model = CraftsmanPortfolio

    def post(self, request, *args, **kwargs):
        portfolio_item = self.get_object()

        # Check if user owns this portfolio item
        if portfolio_item.craftsman.user != request.user:
            messages.error(request, 'Nu ai permisiunea să ștergi această imagine.')
            return redirect('accounts:portfolio')

        portfolio_item.delete()
        messages.success(request, 'Imaginea a fost ștearsă din portfolio.')
        return redirect('accounts:portfolio')


class CraftsmanOnboardingView(LoginRequiredMixin, TemplateView):
    """Multi-step onboarding for new craftsmen"""
    template_name = 'accounts/craftsman_onboarding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.request.GET.get('step', '1')
        context['current_step'] = step

        if step == '1':
            # Profile setup
            try:
                craftsman = self.request.user.craftsman_profile
                context['profile_form'] = CraftsmanProfileForm(instance=craftsman)
            except CraftsmanProfile.DoesNotExist:
                context['profile_form'] = CraftsmanProfileForm()

        elif step == '2':
            # Skills selection
            context['skills_form'] = CraftsmanSkillsForm()

        elif step == '3':
            # Portfolio upload
            context['portfolio_form'] = BulkPortfolioUploadForm()

        return context

    def post(self, request, *args, **kwargs):
        step = request.GET.get('step', '1')

        if step == '1':
            return self._handle_profile_step(request)
        elif step == '2':
            return self._handle_skills_step(request)
        elif step == '3':
            return self._handle_portfolio_step(request)

        return self.get(request, *args, **kwargs)

    def _handle_profile_step(self, request):
        try:
            craftsman = request.user.craftsman_profile
            form = CraftsmanProfileForm(request.POST, instance=craftsman)
        except CraftsmanProfile.DoesNotExist:
            form = CraftsmanProfileForm(request.POST)

        if form.is_valid():
            if hasattr(request.user, 'craftsman_profile'):
                form.save()
            else:
                craftsman = form.save(commit=False)
                craftsman.user = request.user
                craftsman.save()

            messages.success(request, 'Profilul a fost actualizat.')
            return redirect(f'{request.path}?step=2')

        return render(request, self.template_name, {
            'current_step': '1',
            'profile_form': form
        })

    def _handle_skills_step(self, request):
        form = CraftsmanSkillsForm(request.POST)
        if form.is_valid():
            # Save skills to craftsman profile or separate model
            messages.success(request, 'Competențele au fost salvate.')
            return redirect(f'{request.path}?step=3')

        return render(request, self.template_name, {
            'current_step': '2',
            'skills_form': form
        })

    def _handle_portfolio_step(self, request):
        form = BulkPortfolioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                craftsman = request.user.craftsman_profile
                images = form.get_images()

                for i, image in enumerate(images):
                    CraftsmanPortfolio.objects.create(
                        craftsman=craftsman,
                        image=image,
                        title=f"Lucrare {i + 1}"
                    )

                messages.success(request, f'Au fost încărcate {len(images)} imagini.')
                return redirect('accounts:profile')

            except CraftsmanProfile.DoesNotExist:
                messages.error(request, 'Profilul de meșter nu a fost găsit.')

        return render(request, self.template_name, {
            'current_step': '3',
            'portfolio_form': form
        })
