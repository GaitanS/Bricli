"""
Tests for 301 URL redirects from old English/mixed URLs to new Romanian ASCII URLs
"""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestURLRedirects:
    """Test 301 permanent redirects from old URLs to new Romanian URLs"""

    def test_services_to_servicii(self, client):
        """Old /services/* → /servicii/*"""
        response = client.get("/services/categorii/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/servicii/categorii/"

    def test_services_subpath_redirect(self, client):
        """Old /services/comanda/creare/ → /servicii/comanda/creare/"""
        response = client.get("/services/comanda/creare/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/servicii/comanda/creare/"

    def test_accounts_mesterii_to_meseriasi(self, client):
        """Old /accounts/mesterii/ (with ț) → /conturi/meseriasi/ (ASCII)"""
        response = client.get("/accounts/mesterii/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/conturi/meseriasi/"

    def test_accounts_mester_slug_to_meserias(self, client):
        """Old /accounts/mester/<slug>/ (with ș) → /conturi/meserias/<slug>/ (ASCII)"""
        response = client.get("/accounts/mester/ion-popescu/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/conturi/meserias/ion-popescu/"

    def test_accounts_profil_to_conturi(self, client):
        """Old /accounts/profil/ → /conturi/profil/"""
        response = client.get("/accounts/profil/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/conturi/profil/"

    def test_accounts_inregistrare_to_root(self, client):
        """Old /accounts/inregistrare/ → /inregistrare/ (root-level)"""
        response = client.get("/accounts/inregistrare/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/inregistrare/"

    def test_accounts_autentificare_to_root(self, client):
        """Old /accounts/autentificare/ → /autentificare/ (root-level)"""
        response = client.get("/accounts/autentificare/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/autentificare/"

    def test_messages_to_mesaje(self, client):
        """Old /messages/* → /mesaje/*"""
        response = client.get("/messages/conversatie/1/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/mesaje/conversatie/1/"

    def test_how_it_works_redirect(self, client):
        """Old /how-it-works/ → /cum-functioneaza/"""
        response = client.get("/how-it-works/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/cum-functioneaza/"

    def test_preserve_query_string(self, client):
        """301 redirects preserve query strings"""
        response = client.get("/services/categorii/?page=2&sort=name", follow=False)
        assert response.status_code == 301
        assert "/servicii/categorii/" in response["Location"]
        assert "page=2" in response["Location"]
        assert "sort=name" in response["Location"]

    def test_no_redirect_for_new_urls(self, client):
        """New Romanian URLs should not redirect (pass through to views)"""
        # These will 404 if view doesn't exist, but should NOT return 301
        response = client.get("/servicii/categorii/", follow=False)
        assert response.status_code != 301  # Will be 200 or 404, not redirect

    def test_accounts_portofoliu_redirect(self, client):
        """Old /accounts/portofoliu/ → /conturi/portofoliu/"""
        response = client.get("/accounts/portofoliu/", follow=False)
        assert response.status_code == 301
        assert response["Location"] == "/conturi/portofoliu/"
