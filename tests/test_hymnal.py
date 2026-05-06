"""Tests for liturgist.hymnal module."""

from pathlib import Path

import fitz  # pymupdf

from liturgist.hymnal import (
    HymnRef,
    _parse_score_filename,
    load_hymn_images,
    load_hymnal_scores,
    parse_hymn_number,
    parse_hymn_ref,
)


def _make_test_pdf(path: Path, num_pages: int = 1):
    doc = fitz.open()
    for _ in range(num_pages):
        doc.new_page(width=72, height=72)
    doc.save(str(path))
    doc.close()


class TestParseHymnRef:
    def test_number_and_title(self):
        assert parse_hymn_ref("Hymn 552 - Rejoice, All Ye Believers") == HymnRef(
            number=552,
            title="Rejoice, All Ye Believers",
        )

    def test_number_only(self):
        assert parse_hymn_ref("Hymn 42") == HymnRef(number=42)

    def test_case_insensitive(self):
        ref = parse_hymn_ref("hymn 100 - some title")
        assert ref.number == 100
        assert ref.title == "some title"

    def test_bare_number_and_title(self):
        assert parse_hymn_ref("552 - Rejoice, All Ye Believers") == HymnRef(
            number=552,
            title="Rejoice, All Ye Believers",
        )

    def test_bare_number(self):
        assert parse_hymn_ref("552") == HymnRef(number=552)

    def test_title_only(self):
        assert parse_hymn_ref("Doxology") == HymnRef(title="Doxology")

    def test_empty_string(self):
        assert parse_hymn_ref("") == HymnRef()


class TestParseHymnNumber:
    def test_standard_format(self):
        assert parse_hymn_number("Hymn 552 - Rejoice, All Ye Believers") == 552

    def test_no_match(self):
        assert parse_hymn_number("Doxology") is None


class TestParseScoreFilename:
    def test_number_and_title(self):
        assert _parse_score_filename("344_O-Sacred-Head") == HymnRef(
            number=344,
            title="O Sacred Head",
        )

    def test_number_only(self):
        assert _parse_score_filename("344") == HymnRef(number=344)

    def test_title_only(self):
        assert _parse_score_filename("O-Sacred-Head") == HymnRef(title="O Sacred Head")

    def test_title_starting_with_digits(self):
        assert _parse_score_filename("100-Songs") == HymnRef(title="100 Songs")


class TestLoadHymnImages:
    def test_single_page_pdf(self, tmp_path):
        _make_test_pdf(tmp_path / "100.pdf", num_pages=1)
        result = load_hymn_images("100", tmp_path)
        assert len(result) == 1
        assert result[0].startswith("data:image/png;base64,")

    def test_multi_page_pdf(self, tmp_path):
        _make_test_pdf(tmp_path / "552.pdf", num_pages=3)
        result = load_hymn_images("552", tmp_path)
        assert len(result) == 3
        for uri in result:
            assert uri.startswith("data:image/png;base64,")

    def test_stem_with_title(self, tmp_path):
        _make_test_pdf(tmp_path / "344_O-Sacred-Head.pdf", num_pages=1)
        result = load_hymn_images("344_O-Sacred-Head", tmp_path)
        assert len(result) == 1

    def test_missing(self, tmp_path):
        assert load_hymn_images("999", tmp_path) == []


class TestLoadHymnalScores:
    def test_list_input(self, tmp_path):
        _make_test_pdf(tmp_path / "552.pdf")
        hymns = [
            "Hymn 552 - Rejoice, All Ye Believers",
            "Hymn 999 - Does Not Exist",
        ]
        result = load_hymnal_scores(hymns, tmp_path)
        assert len(result) == 2
        assert result[0]["number"] == 552
        assert result[0]["title"] == "Rejoice, All Ye Believers"
        assert len(result[0]["sheets"]) == 1
        assert result[1] is None

    def test_string_input(self, tmp_path):
        _make_test_pdf(tmp_path / "100.pdf")
        result = load_hymnal_scores("Hymn 100 - A Title", tmp_path)
        assert len(result) == 1
        assert result[0]["number"] == 100
        assert result[0]["title"] == "A Title"

    def test_title_lookup(self, tmp_path):
        _make_test_pdf(tmp_path / "552_Rejoice.pdf")
        result = load_hymnal_scores("Rejoice", tmp_path)
        assert len(result) == 1
        assert result[0]["number"] == 552
        assert result[0]["title"] == "Rejoice"

    def test_title_lookup_case_insensitive(self, tmp_path):
        _make_test_pdf(tmp_path / "552_Rejoice.pdf")
        result = load_hymnal_scores("rejoice", tmp_path)
        assert result[0] is not None
        assert result[0]["number"] == 552

    def test_title_lookup_ignores_punctuation(self, tmp_path):
        _make_test_pdf(tmp_path / "552_Rejoice-Ye-Pure-In-Heart.pdf")
        result = load_hymnal_scores("Rejoice, Ye Pure In Heart", tmp_path)
        assert result[0] is not None
        assert result[0]["number"] == 552

    def test_title_lookup_with_hyphenated_cell(self, tmp_path):
        _make_test_pdf(tmp_path / "O-Sacred-Head.pdf")
        result = load_hymnal_scores("O-Sacred-Head", tmp_path)
        assert result[0] is not None
        assert result[0]["title"] == "O-Sacred-Head"

    def test_csv_title_takes_precedence(self, tmp_path):
        _make_test_pdf(tmp_path / "552_Rejoice.pdf")
        result = load_hymnal_scores("Hymn 552 - Rejoice, All Ye Believers", tmp_path)
        assert result[0]["title"] == "Rejoice, All Ye Believers"

    def test_title_from_filename_when_no_csv_title(self, tmp_path):
        _make_test_pdf(tmp_path / "552_Rejoice.pdf")
        result = load_hymnal_scores("Hymn 552", tmp_path)
        assert result[0]["number"] == 552
        assert result[0]["title"] == "Rejoice"

    def test_no_match(self, tmp_path):
        assert load_hymnal_scores("Doxology", tmp_path) == [None]

    def test_empty_list(self, tmp_path):
        assert load_hymnal_scores([], tmp_path) == []
