"""
Test suite for querystring template tag
"""

import pytest
from django.template import Context, Template
from django.test import RequestFactory


@pytest.mark.django_db
class TestQueryStringTag:
    """Tests for the querystring template tag"""

    def test_tag_is_registered(self):
        """Test that querystring tag is registered"""
        from core.templatetags import querystring

        assert hasattr(querystring, "register")
        assert hasattr(querystring, "querystring")

    def test_tag_adds_parameter(self):
        """Test adding a new parameter"""
        factory = RequestFactory()
        request = factory.get("/search/")

        template = Template("{% load querystring %}?{% querystring county='cluj' %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "county=cluj" in output

    def test_tag_updates_existing_parameter(self):
        """Test updating an existing parameter"""
        factory = RequestFactory()
        request = factory.get("/search/?county=bucuresti")

        template = Template("{% load querystring %}?{% querystring county='cluj' %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "county=cluj" in output
        assert "bucuresti" not in output

    def test_tag_removes_parameter_with_none(self):
        """Test removing a parameter by setting it to None"""
        factory = RequestFactory()
        request = factory.get("/search/?county=bucuresti&rating=4.5")

        template = Template("{% load querystring %}?{% querystring county=None %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "county" not in output
        assert "rating=4.5" in output

    def test_tag_removes_parameter_with_empty_string(self):
        """Test removing a parameter by setting it to empty string"""
        factory = RequestFactory()
        request = factory.get("/search/?county=cluj&category=instalatii")

        template = Template('{% load querystring %}?{% querystring county="" %}')
        context = Context({"request": request})
        output = template.render(context)

        assert "county" not in output
        assert "category=instalatii" in output

    def test_tag_preserves_other_parameters(self):
        """Test that other parameters are preserved"""
        factory = RequestFactory()
        request = factory.get("/search/?q=test&county=cluj&rating=4.5")

        template = Template("{% load querystring %}?{% querystring category='constructii' %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "q=test" in output
        assert "county=cluj" in output
        assert "rating=4.5" in output
        assert "category=constructii" in output

    def test_tag_handles_multiple_updates(self):
        """Test updating multiple parameters at once"""
        factory = RequestFactory()
        request = factory.get("/search/?q=test")

        template = Template("{% load querystring %}?{% querystring county='cluj' rating='4.5' %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "q=test" in output
        assert "county=cluj" in output
        assert "rating=4.5" in output

    def test_tag_handles_empty_query_string(self):
        """Test tag works with no existing parameters"""
        factory = RequestFactory()
        request = factory.get("/search/")

        template = Template("{% load querystring %}?{% querystring county='cluj' rating='4.5' %}")
        context = Context({"request": request})
        output = template.render(context)

        assert "county=cluj" in output
        assert "rating=4.5" in output

    def test_tag_url_encodes_parameters(self):
        """Test that parameters are properly URL encoded"""
        factory = RequestFactory()
        request = factory.get("/search/")

        template = Template("{% load querystring %}?{% querystring q='vopsit apartament' %}")
        context = Context({"request": request})
        output = template.render(context)

        # Should be URL encoded
        assert "vopsit" in output or "q=" in output

    def test_tag_without_request_context(self):
        """Test tag returns empty string without request in context"""
        template = Template("{% load querystring %}?{% querystring county='cluj' %}")
        context = Context({})  # No request
        output = template.render(context)

        # Should return just the "?" since there's no request
        assert output.strip() == "?"
