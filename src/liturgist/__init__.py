"""
Liturgist - A liturgical document generator

A Python package for generating liturgical documents from schedule data
using Handlebars templates with support for PDF, DOCX, and ODT schedule formats.
"""

__version__ = "2.0.0"
__author__ = "Justin Brooks"
__email__ = "justin@jzbrooks.com"

# Re-export main functionality for convenience
from .core import (
    load_template_from_file,
    next_sunday,
    read_schedule,
)
from .hymnal import (
    HymnRef,
    load_hymnal_scores,
    parse_hymn_number,
    parse_hymn_ref,
)
from .scripture import get_scripture_text

__all__ = [
    "read_schedule",
    "load_template_from_file",
    "get_scripture_text",
    "next_sunday",
    "HymnRef",
    "load_hymnal_scores",
    "parse_hymn_number",
    "parse_hymn_ref",
]
