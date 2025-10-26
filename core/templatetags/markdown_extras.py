# -*- coding: utf-8 -*-
"""
Custom template filters for markdown conversion
"""

from django import template
import re

register = template.Library()


@register.filter(name='markdown_to_html')
def markdown_to_html(text):
    """
    Convert simple markdown to HTML
    Supports: **bold**, lists with -, line breaks
    """
    if not text:
        return ''

    # Convert **text** to <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Convert lines starting with - to <ul><li>
    lines = text.split('\n')
    html_lines = []
    in_list = False

    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            if not in_list:
                html_lines.append('<ul class="list-unstyled">')
                in_list = True
            # Remove the - and wrap in li
            html_lines.append(f'<li class="mb-2">{line[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line:
                html_lines.append(f'<p>{line}</p>')

    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)
