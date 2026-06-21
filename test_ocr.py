import pytesseract

# IMPORTANT: set your path here
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Admin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

print("Tesseract Version:")
print(pytesseract.get_tesseract_version())