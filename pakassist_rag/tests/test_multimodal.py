from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fitz")  # PyMuPDF


def _make_text_pdf(path):
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Driving license fee is confirmed at the office counter.")
    doc.save(str(path))
    doc.close()


def test_pdf_text_extraction_uses_pymupdf_for_real_text(tmp_path):
    from backend.rag.multimodal import extract_text_from_pdf

    pdf_path = tmp_path / "sample.pdf"
    _make_text_pdf(pdf_path)

    results = extract_text_from_pdf(str(pdf_path))

    assert len(results) == 1
    page_num, text, method = results[0]
    assert page_num == 1
    assert method == "pymupdf"
    assert "Driving license fee" in text


@patch("backend.rag.multimodal._get_client")
def test_scanned_pdf_page_falls_back_to_gemini(mock_get_client, tmp_path):
    import fitz

    from backend.rag.multimodal import extract_text_from_pdf

    # a blank page has ~0 extractable text -> should trigger the Gemini path
    doc = fitz.open()
    doc.new_page()
    pdf_path = tmp_path / "scanned.pdf"
    doc.save(str(pdf_path))
    doc.close()

    mock_response = MagicMock()
    mock_response.text = "Extracted: a form with no machine-readable text."
    mock_get_client.return_value.models.generate_content.return_value = mock_response

    results = extract_text_from_pdf(str(pdf_path))

    assert len(results) == 1
    _, text, method = results[0]
    assert method == "gemini"
    assert "Extracted" in text

    # confirm no tools were passed and AFC is explicitly disabled
    _, kwargs = mock_get_client.return_value.models.generate_content.call_args
    assert "tools" not in kwargs
    assert kwargs["config"].automatic_function_calling.disable is True


@patch("backend.rag.multimodal._get_client")
@patch("PIL.Image.open")
def test_extract_text_from_image_is_plain_generate_content_call(mock_image_open, mock_get_client, tmp_path):
    from backend.rag.multimodal import extract_text_from_image

    mock_image_open.return_value = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "A CNIC card with a name and ID number visible."
    mock_get_client.return_value.models.generate_content.return_value = mock_response

    fake_image_path = tmp_path / "id.png"
    fake_image_path.write_bytes(b"not a real image, just needs to exist")

    result = extract_text_from_image(str(fake_image_path))

    assert "CNIC" in result
    _, kwargs = mock_get_client.return_value.models.generate_content.call_args
    assert "tools" not in kwargs
    assert kwargs["config"].automatic_function_calling.disable is True
