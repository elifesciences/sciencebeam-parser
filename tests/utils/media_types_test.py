from sciencebeam_parser.utils.media_types import (
    MediaTypes,
    get_first_matching_media_type,
    guess_extension_for_media_type,
    guess_media_type_for_filename
)


MEDIA_TYPE_1 = 'test/media1'
MEDIA_TYPE_2 = 'test/media3'
MEDIA_TYPE_3 = 'test/media3'
MEDIA_TYPE_4 = 'test/media4'


class TestGuessExtensionForMediaType:
    def test_should_guess_pdf_extension(self):
        assert guess_extension_for_media_type(MediaTypes.PDF) == '.pdf'

    def test_should_guess_doc_extension(self):
        assert guess_extension_for_media_type(MediaTypes.DOC) == '.doc'

    def test_should_guess_docx_extension(self):
        assert guess_extension_for_media_type(MediaTypes.DOCX) == '.docx'

    def test_should_guess_tei_xml_extension(self):
        assert guess_extension_for_media_type(MediaTypes.TEI_XML) == '.tei.xml'

    def test_should_guess_jats_xml_extension(self):
        assert guess_extension_for_media_type(MediaTypes.JATS_XML) == '.jats.xml'

    def test_should_guess_tei_xml_zip_extension(self):
        assert guess_extension_for_media_type(MediaTypes.TEI_ZIP) == '.tei.zip'

    def test_should_guess_jats_xml_zip_extension(self):
        assert guess_extension_for_media_type(MediaTypes.JATS_ZIP) == '.jats.zip'

    def test_should_guess_json_extension(self):
        assert guess_extension_for_media_type(MediaTypes.JSON) == '.json'


class TestGuessMediaTypeForFilename:
    def test_should_guess_docx(self):
        assert guess_media_type_for_filename('test.docx') == MediaTypes.DOCX

    def test_should_guess_pdf(self):
        assert guess_media_type_for_filename('test.pdf') == MediaTypes.PDF

    def test_should_not_guess_without_extension(self):
        assert guess_media_type_for_filename('test') is None


class TestGetFirstMatchingMediaType:
    def test_should_return_none_for_different_media_types(self):
        assert get_first_matching_media_type(
            [MEDIA_TYPE_1],
            [MEDIA_TYPE_2, MEDIA_TYPE_3, MEDIA_TYPE_4]
        ) is None

    def test_should_return_none_for_no_available_media_types(self):
        assert get_first_matching_media_type(
            [MEDIA_TYPE_1],
            []
        ) is None

    def test_should_return_exactly_matching_media_type(self):
        assert get_first_matching_media_type(
            [MEDIA_TYPE_2],
            [MEDIA_TYPE_1, MEDIA_TYPE_2, MEDIA_TYPE_3]
        ) == MEDIA_TYPE_2

    def test_should_return_first_media_type_for_no_accept_media_types(self):
        assert get_first_matching_media_type(
            [],
            [MEDIA_TYPE_1, MEDIA_TYPE_2, MEDIA_TYPE_3]
        ) == MEDIA_TYPE_1

    def test_should_return_first_media_type_for_wildcard_accept_media_type(self):
        assert get_first_matching_media_type(
            ['*/*'],
            [MEDIA_TYPE_1, MEDIA_TYPE_2, MEDIA_TYPE_3]
        ) == MEDIA_TYPE_1
