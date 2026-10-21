"""
Single source of truth for every tool: its URL, the template that holds the
tool itself, and all the landing-page content (steps, benefits, FAQ).

Adding or editing a tool's page means editing the entry below - the hub page,
homepage tiles, sitemap and structured data are all generated from this list.
"""

import json
import os

SITE_NAME = "PDFJantaParty"
SITE_URL = os.environ.get("SITE_URL", "https://pdfjantaparty.onrender.com").rstrip("/")

CATEGORIES = [
    ("organize", "Organize PDF", "Combine, split and tidy up the pages of a PDF."),
    ("optimize", "Optimize", "Make PDFs and images smaller for forms, email and uploads."),
    ("to_pdf", "Convert to PDF", "Turn images, documents, spreadsheets and web pages into PDF."),
    ("from_pdf", "Convert from PDF", "Turn a PDF into images, Word, PowerPoint, Excel or PDF/A."),
    ("edit", "Edit & Sign", "Edit text, sign, fill forms and work with scanned pages."),
    ("security", "PDF Security", "Lock a PDF with a password, unlock one, or redact sensitive details."),
]

# How each kind of tool handles your file. Used for the "is it safe?" FAQ so
# the answer is accurate for each tool instead of one blanket claim.
PRIVACY_FAQ = {
    "server": (
        "Is it safe to upload my PDF?",
        "Your file is sent to our server over an encrypted (HTTPS) connection, processed to "
        "create your result, and returned to you. There is no account or sign-in, and your "
        "document is not used for anything else. If a file is highly confidential, you may "
        "prefer to process it on your own computer.",
    ),
    "browser": (
        "Is my PDF uploaded to your server?",
        "No. Your PDF is opened and processed in your own browser, so the file itself is not "
        "sent to our server.",
    ),
    "mixed": (
        "Is my PDF uploaded when I edit it?",
        "Opening, editing and saving all happen in your browser. The only time anything is sent "
        "to our server is when you run OCR on a scanned page - an image of that page is sent so "
        "its text can be read. Pages that already contain typed text are read directly in your "
        "browser and are not sent.",
    ),
}


def _convert_context(title, description, action, accept, button_text, note=None):
    return {
        "title": title,
        "description": description,
        "action": action,
        "accept": accept,
        "button_text": button_text,
        "note": note,
    }


TOOLS = [
    # ------------------------------------------------------------------ organize
    {
        "key": "merge", "slug": "merge-pdf", "template": "merge.html", "category": "organize",
        "icon": "📎", "name": "Merge PDF", "processing": "server",
        "short": "Combine multiple PDFs into one.",
        "meta_title": "Merge PDF Files Online - Combine PDFs Free | PDFJantaParty",
        "meta_description": "Combine two or more PDF files into one document online. Free, with no sign-up and no watermark. Select your files, merge, and download.",
        "tagline": "Combine several PDF files into one document in a few clicks.",
        "howto": "How to merge PDF files online",
        "steps": [
            ("Select your PDFs", "Choose two or more PDF files from your computer or phone."),
            ("Check the order", "Files are merged in the order shown in the list on the page."),
            ("Merge and download", "Click the merge button and download your combined PDF."),
        ],
        "benefits": [
            ("Free to use", "No account, no sign-up and no watermark on your merged file."),
            ("Pages stay untouched", "Pages are copied across as they are, so text and images are not re-compressed."),
            ("Nothing to install", "Works in your browser on a phone, tablet or computer."),
        ],
        "faq": [
            ("How do I combine PDF files into one?", "Select two or more PDFs, click the merge button, and download the combined file."),
            ("In what order are the files merged?", "In the order they appear in the list on the page after you select them."),
            ("Does merging reduce quality?", "No. Pages are copied across as they are, so text and images are not re-compressed. If the merged file is too large to upload somewhere, use Compress PDF afterwards."),
        ],
        "related": ["split", "compress", "rearrange", "remove"],
    },
    {
        "key": "split", "slug": "split-pdf", "template": "split.html", "category": "organize",
        "icon": "✂️", "name": "Split PDF", "processing": "server",
        "short": "Extract chosen pages into a new PDF.",
        "meta_title": "Split PDF - Extract Pages From a PDF Online | PDFJantaParty",
        "meta_description": "Extract the pages you need from a PDF. Enter page numbers or ranges like 1-3,7 and download them as a new PDF. Free, with no sign-up.",
        "tagline": "Pull specific pages or page ranges out of a PDF into a new file.",
        "howto": "How to extract pages from a PDF",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to take pages from."),
            ("Enter the pages you want", "Type page numbers or ranges, for example 5-6, 1,3,5 or 1-3,7-9."),
            ("Download the new PDF", "You get one new PDF that contains only the pages you listed."),
        ],
        "benefits": [
            ("Simple page ranges", "Mix single pages and ranges in one go, such as 1,4,8-10."),
            ("Original stays safe", "Your original file is not changed - you get a new PDF."),
            ("Free, no sign-up", "Use it as often as you like without creating an account."),
        ],
        "faq": [
            ("How do I extract pages from a PDF?", "Upload the PDF, type the pages you want (for example 2-4,9), and download the new file."),
            ("Can I split one PDF into several files?", "This tool creates one new PDF from the pages you list. To get several separate files, run it once for each group of pages."),
            ("Does it change my original file?", "No. Your original stays as it is and you receive a new PDF."),
        ],
        "related": ["merge", "remove", "rearrange", "compress"],
    },
    {
        "key": "remove", "slug": "remove-pdf-pages", "template": "remove_pages.html", "category": "organize",
        "icon": "🗑️", "name": "Remove PDF Pages", "processing": "server",
        "short": "Delete unwanted pages from a PDF.",
        "meta_title": "Remove Pages From PDF Online - Delete PDF Pages | PDFJantaParty",
        "meta_description": "Delete unwanted pages from a PDF online. Enter page numbers or ranges like 2,4 or 5-7 and download the cleaned PDF. Free, with no sign-up.",
        "tagline": "Delete the pages you don't need and keep the rest exactly as they are.",
        "howto": "How to delete pages from a PDF",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to clean up."),
            ("Enter the pages to delete", "Type page numbers or ranges, such as 2, 4 or 5-7."),
            ("Download the result", "Save the new PDF without those pages."),
        ],
        "benefits": [
            ("Remove many pages at once", "Combine single pages and ranges in one entry."),
            ("Other pages untouched", "The pages you keep are left exactly as they were."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("How do I delete pages from a PDF?", "Upload your PDF, enter the page numbers to remove, and download the new file."),
            ("Can I remove several pages at once?", "Yes. Separate page numbers with commas and use a dash for ranges, such as 1, 3, 5-7."),
            ("Can I undo it?", "Your original file is not changed, so you can run the tool again with different pages if you removed the wrong ones."),
        ],
        "related": ["split", "rearrange", "merge", "compress"],
    },
    {
        "key": "rearrange", "slug": "rearrange-pdf-pages", "template": "rearrange_pages.html", "category": "organize",
        "icon": "🔄", "name": "Rearrange PDF Pages", "processing": "server",
        "short": "Reorder the pages of a PDF.",
        "meta_title": "Rearrange PDF Pages Online - Reorder PDF Pages | PDFJantaParty",
        "meta_description": "Reorder the pages of a PDF online. Type the new page order, such as 3,1,2,4-6, and download the rearranged PDF. Free, with no sign-up.",
        "tagline": "Put your PDF's pages in the order you want.",
        "howto": "How to reorder pages in a PDF",
        "steps": [
            ("Upload your PDF", "Choose the PDF whose pages you want to reorder."),
            ("Type the new order", "Enter page numbers in the order you want them, for example 3, 1, 2, 4-6."),
            ("Download the result", "Save the rearranged PDF."),
        ],
        "benefits": [
            ("Full control of the order", "List pages in any order, including ranges."),
            ("Reverse or repeat pages", "A range like 6-4 reverses the order, and you can list a page twice."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("How do I reorder pages in a PDF?", "Upload the PDF, type the new page order such as 3,1,2,4-6, and download the result."),
            ("What happens to pages I don't list?", "They are left out of the new file, so list every page you want to keep."),
            ("Can I reverse pages or repeat a page?", "Yes. A descending range like 6-4 gives pages 6, 5, 4, and you can list a page more than once to repeat it."),
        ],
        "related": ["remove", "merge", "split", "compress"],
    },
    # ------------------------------------------------------------------ optimize
    {
        "key": "compress", "slug": "compress-pdf", "template": "compress.html", "category": "optimize",
        "icon": "📉", "name": "Compress PDF", "processing": "server",
        "short": "Reduce a PDF to a target size like 100 KB.",
        "meta_title": "Compress PDF to 100KB, 50KB or 20KB Online Free | PDFJantaParty",
        "meta_description": "Reduce a PDF to a target size such as 20 KB, 50 KB, 100 KB, 200 KB or 1 MB for exam forms, job portals and email. Free, with no sign-up.",
        "tagline": "Shrink a PDF to the size an exam portal, job form or email asks for.",
        "howto": "How to compress a PDF to a target size",
        "steps": [
            ("Upload your PDF", "Choose the PDF that is too large."),
            ("Pick a target size", "Choose a preset such as 20 KB (Exam Mode), 50 KB, 100 KB, 200 KB, 500 KB or 1 MB, or enter your own."),
            ("Compress and download", "Click compress, then download the smaller PDF."),
        ],
        "benefits": [
            ("Built for upload limits", "Pick the size a form asks for and the tool works toward it."),
            ("Exam Mode presets", "Quick choices for the small limits common on application portals."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("How do I compress a PDF to 100 KB?", "Upload your PDF, choose 100 KB as the target size, click compress, and download the result."),
            ("What if the target size can't be reached?", "The result page tells you when the exact target could not be reached without damaging quality. Choose a slightly larger target and try again."),
            ("Will the text still be selectable after compression?", "If your PDF can be made smaller without changing its pages, text stays selectable. When more shrinking is needed, pages are converted to compressed images, so text may no longer be selectable."),
            ("What is the smallest target size I can choose?", "10 KB."),
        ],
        "related": ["compress-image", "merge", "split", "pdf-to-jpg"],
    },
    {
        "key": "compress-image", "slug": "compress-image", "template": "image_compress.html", "category": "optimize",
        "icon": "🖼️", "name": "Compress Image", "processing": "server",
        "short": "Reduce a photo or signature to a target size.",
        "meta_title": "Compress Image to 20KB, 50KB or 100KB Online Free | PDFJantaParty",
        "meta_description": "Reduce a JPG, PNG or WebP photo or signature image to a target size like 20 KB, 50 KB or 100 KB for application forms. Free, no sign-up.",
        "tagline": "Get a photo or signature image down to the size a form asks for.",
        "howto": "How to reduce an image to a target size",
        "steps": [
            ("Upload your image", "Choose a JPG, JPEG, PNG or WebP image."),
            ("Pick a target size", "Choose a preset in KB or enter your own."),
            ("Compress and download", "Download the smaller image."),
        ],
        "benefits": [
            ("Made for form uploads", "Aim for limits like 20 KB, 50 KB or 100 KB."),
            ("Works with common formats", "JPG, JPEG, PNG and WebP images are accepted."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("How do I reduce an image to 50 KB?", "Upload your image, choose 50 KB as the target size, and download the result."),
            ("What format is the result?", "JPG. PNG and WebP images are converted to JPG, so any transparent areas become solid."),
            ("Why didn't my image reach the exact size?", "The tool adjusts JPG quality to get as close to your target as it can without resizing the image, so a very large photo may not reach a very small target such as 20 KB. Starting from a smaller image helps."),
        ],
        "related": ["compress", "jpg-to-pdf", "pdf-to-jpg", "merge"],
    },
    # ------------------------------------------------------------------ to PDF
    {
        "key": "jpg-to-pdf", "slug": "jpg-to-pdf", "template": "jpg_to_pdf.html", "category": "to_pdf",
        "icon": "🖼️", "name": "JPG to PDF", "processing": "server",
        "short": "Turn JPG and PNG images into one PDF.",
        "meta_title": "JPG to PDF Converter - Images to PDF Online Free | PDFJantaParty",
        "meta_description": "Convert JPG and PNG images into a single PDF online. Select one or more pictures, create the PDF and download it. Free, with no sign-up.",
        "tagline": "Turn one or many pictures into a single PDF document.",
        "howto": "How to convert JPG to PDF",
        "steps": [
            ("Select your images", "Choose one or more JPG, JPEG or PNG files."),
            ("Create the PDF", "Each image becomes one page of the PDF."),
            ("Download your PDF", "Save the finished document."),
        ],
        "benefits": [
            ("Many images, one PDF", "Combine photos or scans of a document into a single file."),
            ("Each page fits its image", "Pages are sized to match the picture."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Can I combine several images into one PDF?", "Yes. Select multiple images and each one becomes a page in the same PDF."),
            ("Which image formats work?", "JPG, JPEG and PNG."),
            ("The PDF is too big. What can I do?", "Use Compress PDF on the result to bring it down to the size you need."),
        ],
        "related": ["compress", "compress-image", "pdf-to-jpg", "merge"],
    },
    {
        "key": "word-to-pdf", "slug": "word-to-pdf", "template": "generic-convert.html", "category": "to_pdf",
        "icon": "📃", "name": "Word to PDF", "processing": "server",
        "short": "Convert a Word document to PDF.",
        "meta_title": "Word to PDF Converter - DOC and DOCX to PDF Free | PDFJantaParty",
        "meta_description": "Convert Word documents (.doc and .docx) to PDF online. Upload your document and download the PDF. Free, with no sign-up.",
        "tagline": "Turn a Word document into a PDF that looks the same on any device.",
        "howto": "How to convert Word to PDF",
        "steps": [
            ("Upload your document", "Choose a .doc or .docx file."),
            ("Convert", "Click the convert button."),
            ("Download the PDF", "Save the finished PDF."),
        ],
        "benefits": [
            ("DOC and DOCX supported", "Works with both older and current Word formats."),
            ("A fixed layout", "A PDF looks the same on any phone, computer or printer."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Which files can I convert?", "Word files ending in .doc or .docx."),
            ("Will my formatting stay the same?", "Most documents convert accurately, but complex layouts can shift slightly, and fonts that aren't available on our server are replaced with similar ones. Check the result before sending it."),
            ("Can I convert a Google Doc?", "Download it as a .docx file from Google Docs first, then upload that file here."),
        ],
        "related": ["pdf-to-word", "compress", "merge", "protect"],
        "context": _convert_context("Word to PDF", "Convert a .docx or .doc file into a PDF.", "/word-to-pdf", ".doc,.docx", "Convert to PDF"),
    },
    {
        "key": "ppt-to-pdf", "slug": "powerpoint-to-pdf", "template": "generic-convert.html", "category": "to_pdf",
        "icon": "📽️", "name": "PowerPoint to PDF", "processing": "server",
        "short": "Convert a presentation to PDF.",
        "meta_title": "PowerPoint to PDF Converter - PPT and PPTX to PDF | PDFJantaParty",
        "meta_description": "Convert PowerPoint presentations (.ppt and .pptx) to PDF online. Upload your slides and download the PDF. Free, with no sign-up.",
        "tagline": "Turn your slides into a PDF that is easy to share and print.",
        "howto": "How to convert PowerPoint to PDF",
        "steps": [
            ("Upload your presentation", "Choose a .ppt or .pptx file."),
            ("Convert", "Click the convert button."),
            ("Download the PDF", "Each slide becomes one page."),
        ],
        "benefits": [
            ("PPT and PPTX supported", "Works with older and current PowerPoint formats."),
            ("Easy to share", "A PDF opens on any device without PowerPoint."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Which files can I convert?", "PowerPoint files ending in .ppt or .pptx."),
            ("Are animations kept?", "No. A PDF is static, so animations and transitions are not included. Each slide becomes one page."),
            ("Will my slides look exactly the same?", "Most do, but unusual fonts or effects can change slightly. Check the result before sharing it."),
        ],
        "related": ["pdf-to-ppt", "compress", "merge", "protect"],
        "context": _convert_context("PowerPoint to PDF", "Convert a .pptx or .ppt file into a PDF.", "/ppt-to-pdf", ".ppt,.pptx", "Convert to PDF"),
    },
    {
        "key": "excel-to-pdf", "slug": "excel-to-pdf", "template": "generic-convert.html", "category": "to_pdf",
        "icon": "📊", "name": "Excel to PDF", "processing": "server",
        "short": "Convert a spreadsheet to PDF.",
        "meta_title": "Excel to PDF Converter - XLS and XLSX to PDF Free | PDFJantaParty",
        "meta_description": "Convert Excel spreadsheets (.xls and .xlsx) to PDF online. Upload your workbook and download the PDF. Free, with no sign-up.",
        "tagline": "Turn a spreadsheet into a PDF you can share or print.",
        "howto": "How to convert Excel to PDF",
        "steps": [
            ("Upload your spreadsheet", "Choose an .xls or .xlsx file."),
            ("Convert", "Click the convert button."),
            ("Download the PDF", "Save the finished PDF."),
        ],
        "benefits": [
            ("XLS and XLSX supported", "Works with older and current Excel formats."),
            ("Easy to share and print", "A PDF keeps your tables laid out the same way everywhere."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Which files can I convert?", "Excel files ending in .xls or .xlsx."),
            ("How are wide sheets handled?", "Very wide sheets can be split across several pages. Setting a print area and page width in Excel first gives the neatest result."),
            ("Will formulas still work?", "No. A PDF shows the values, not the formulas behind them."),
        ],
        "related": ["pdf-to-excel", "compress", "merge", "protect"],
        "context": _convert_context("Excel to PDF", "Convert a .xlsx or .xls file into a PDF.", "/excel-to-pdf", ".xls,.xlsx", "Convert to PDF"),
    },
    {
        "key": "html-to-pdf", "slug": "html-to-pdf", "template": "generic-convert.html", "category": "to_pdf",
        "icon": "🌐", "name": "HTML to PDF", "processing": "server",
        "short": "Convert an HTML file to PDF.",
        "meta_title": "HTML to PDF Converter - Convert HTML Files Online | PDFJantaParty",
        "meta_description": "Convert an HTML file to PDF online. Upload your .html file and download the PDF. Free, with no sign-up.",
        "tagline": "Turn an HTML file into a PDF document.",
        "howto": "How to convert HTML to PDF",
        "steps": [
            ("Upload your HTML file", "Choose a .html or .htm file."),
            ("Convert", "Click the convert button."),
            ("Download the PDF", "Save the finished PDF."),
        ],
        "benefits": [
            ("Straight from a file", "Upload the HTML file you already have."),
            ("A fixed layout", "A PDF looks the same on any device."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Can I convert a web page by its address?", "Not at the moment. Upload an .html file instead."),
            ("Why are images or styles missing?", "The tool converts the file you upload. Images and stylesheets that are only linked from other files or websites may not load, so a self-contained HTML file gives the best result."),
            ("Which files can I upload?", "Files ending in .html or .htm."),
        ],
        "related": ["word-to-pdf", "compress", "merge", "protect"],
        "context": _convert_context("HTML to PDF", "Convert an .html file into a PDF.", "/html-to-pdf", ".html,.htm", "Convert to PDF"),
    },
    # ---------------------------------------------------------------- from PDF
    {
        "key": "pdf-to-jpg", "slug": "pdf-to-jpg", "template": "pdf_to_jpg.html", "category": "from_pdf",
        "icon": "📷", "name": "PDF to JPG", "processing": "server",
        "short": "Turn every PDF page into a JPG image.",
        "meta_title": "PDF to JPG Converter - PDF Pages to Images | PDFJantaParty",
        "meta_description": "Convert each page of a PDF into a high-quality JPG image online. Download all pages as a ZIP file. Free, with no sign-up.",
        "tagline": "Save every page of a PDF as a sharp JPG image.",
        "howto": "How to convert PDF to JPG",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to turn into images."),
            ("Convert", "Each page is turned into its own JPG."),
            ("Download the ZIP", "All the images arrive together in one ZIP file."),
        ],
        "benefits": [
            ("High quality", "Pages are rendered at 200 DPI, which is sharp for reading and printing."),
            ("One image per page", "Named page_1.jpg, page_2.jpg and so on."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("How many images will I get?", "One JPG for every page, delivered together in a ZIP file."),
            ("What resolution are the images?", "200 DPI."),
            ("Can I convert only some pages?", "Not directly. Use Split PDF to extract the pages you want first, then convert that file."),
        ],
        "related": ["jpg-to-pdf", "compress-image", "split", "compress"],
    },
    {
        "key": "pdf-to-word", "slug": "pdf-to-word", "template": "generic-convert.html", "category": "from_pdf",
        "icon": "📝", "name": "PDF to Word", "processing": "server",
        "short": "Convert a PDF to an editable Word file.",
        "meta_title": "PDF to Word Converter - PDF to DOCX Online Free | PDFJantaParty",
        "meta_description": "Convert a PDF into an editable Word (.docx) document online. Upload your PDF and download the Word file. Free, with no sign-up.",
        "tagline": "Turn a PDF into a Word document you can edit.",
        "howto": "How to convert PDF to Word",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to edit in Word."),
            ("Convert", "Click the convert button."),
            ("Download the Word file", "Open the .docx in Word or any compatible app."),
        ],
        "benefits": [
            ("Editable output", "Get a .docx you can change in Word."),
            ("Best on typed PDFs", "PDFs made from Word or Google Docs convert most cleanly."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Will it keep the original layout?", "It works best on PDFs that contain real text. Complex layouts and tables may need some tidying in Word afterwards."),
            ("Does it work on scanned PDFs?", "A scanned PDF is a picture of a page, so there is no text to convert and the result will mostly contain images. To work with scanned pages, use Edit PDF with OCR instead."),
            ("Which file do I get?", "A .docx file."),
        ],
        "related": ["word-to-pdf", "edit", "pdf-to-excel", "compress"],
        "context": _convert_context("PDF to Word", "Convert a PDF into an editable .docx file.", "/pdf-to-word", ".pdf", "Convert to Word"),
    },
    {
        "key": "pdf-to-ppt", "slug": "pdf-to-powerpoint", "template": "generic-convert.html", "category": "from_pdf",
        "icon": "📽️", "name": "PDF to PowerPoint", "processing": "server",
        "short": "Convert a PDF to PowerPoint slides.",
        "meta_title": "PDF to PowerPoint Converter - PDF to PPTX Online | PDFJantaParty",
        "meta_description": "Convert a PDF into a PowerPoint (.pptx) presentation online, one slide per page. Upload your PDF and download the slides. Free, no sign-up.",
        "tagline": "Turn each page of a PDF into a PowerPoint slide.",
        "howto": "How to convert PDF to PowerPoint",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want as slides."),
            ("Convert", "Click the convert button."),
            ("Download the .pptx", "Each PDF page becomes one slide."),
        ],
        "benefits": [
            ("One slide per page", "Your pages arrive as ready-made slides."),
            ("Text as text boxes", "Text is placed in separate boxes you can select and edit."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Can I edit the text in the slides?", "Text arrives in separate text boxes that you can edit, but PDFs don't store slide layouts, so fonts, spacing and positions often need adjusting."),
            ("Which file do I get?", "A .pptx file with one slide for every page of your PDF."),
            ("Does it work on scanned PDFs?", "A scanned PDF is a picture of a page, so there is no text to place in text boxes. The result is not suitable for editing."),
        ],
        "related": ["ppt-to-pdf", "pdf-to-word", "pdf-to-jpg", "compress"],
        "context": _convert_context("PDF to PowerPoint", "Convert a PDF into a .pptx file, one slide per page.", "/pdf-to-ppt", ".pdf", "Convert to PowerPoint",
                                    "Results vary: text arrives as separate editable text boxes, but fonts, spacing and positions often need adjusting."),
    },
    {
        "key": "pdf-to-excel", "slug": "pdf-to-excel", "template": "generic-convert.html", "category": "from_pdf",
        "icon": "📈", "name": "PDF to Excel", "processing": "server",
        "short": "Extract tables from a PDF into Excel.",
        "meta_title": "PDF to Excel Converter - PDF Tables to XLSX | PDFJantaParty",
        "meta_description": "Extract tables from a PDF into an Excel (.xlsx) file online. Upload your PDF and download the spreadsheet. Free, with no sign-up.",
        "tagline": "Pull the tables out of a PDF and into a spreadsheet.",
        "howto": "How to convert PDF to Excel",
        "steps": [
            ("Upload your PDF", "Choose a PDF that contains tables."),
            ("Convert", "Click the convert button."),
            ("Download the .xlsx", "Each table is placed in its own sheet."),
        ],
        "benefits": [
            ("Tables become sheets", "Each table gets its own sheet, named by page and table number."),
            ("A fallback for plain text", "If no table is found, the page text is placed in a sheet one line per row."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Does it work on scanned PDFs?", "No. It reads tables from PDFs that contain real text. A scanned page is a picture, so no table can be found."),
            ("What if my PDF has no tables?", "The text of each page is placed in a sheet instead, one line per row."),
            ("How are the tables arranged?", "Each table appears in its own sheet, named like Page1_Table1."),
        ],
        "related": ["excel-to-pdf", "pdf-to-word", "compress", "merge"],
        "context": _convert_context("PDF to Excel", "Extract tables from a PDF into an .xlsx file.", "/pdf-to-excel", ".pdf", "Convert to Excel",
                                    "Works best on PDFs with real tables. Scanned/image-only PDFs need OCR first and won't extract cleanly."),
    },
    {
        "key": "pdf-to-pdfa", "slug": "pdf-to-pdfa", "template": "generic-convert.html", "category": "from_pdf",
        "icon": "🗄️", "name": "PDF to PDF/A", "processing": "server",
        "short": "Convert a PDF to archival PDF/A.",
        "meta_title": "PDF to PDF/A Converter - Archival PDF Online | PDFJantaParty",
        "meta_description": "Convert a PDF into the PDF/A archival format online. Upload your PDF and download a PDF/A file. Free, with no sign-up.",
        "tagline": "Create an archival PDF/A version of your PDF.",
        "howto": "How to convert a PDF to PDF/A",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to archive."),
            ("Convert", "Click the convert button."),
            ("Download the PDF/A", "Save the archival version."),
        ],
        "benefits": [
            ("Made for long-term storage", "PDF/A is the standard format for documents kept for the long term."),
            ("PDF/A-1b output", "The file is marked as PDF/A-1b."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("What is PDF/A?", "An ISO standard version of PDF designed for long-term archiving, so a document looks the same years from now."),
            ("Is the result guaranteed to pass strict validators?", "This is a best-effort conversion. Some documents may not pass strict validation, and complex layouts or fonts can shift slightly. If you need certified compliance, check the file with a PDF/A validator."),
            ("Will my PDF look the same?", "Usually, but the file is rebuilt during conversion, so compare it with the original before relying on it."),
        ],
        "related": ["compress", "pdf-to-word", "protect", "merge"],
        "context": _convert_context("PDF to PDF/A", "Convert a PDF into the PDF/A archival format.", "/pdf-to-pdfa", ".pdf", "Convert to PDF/A",
                                    "This is a best-effort conversion, not a guarantee of full PDF/A compliance for every document - complex layouts may shift slightly."),
    },
    # ---------------------------------------------------------------- edit & sign
    {
        "key": "edit", "slug": "edit-pdf", "template": "landing.html", "category": "edit",
        "icon": "✏️", "name": "Edit PDF", "processing": "mixed",
        "short": "Edit text, annotate, and manage pages.",
        "meta_title": "Edit PDF Online Free - PDF Editor | PDFJantaParty",
        "meta_description": "Edit a PDF online: change text, add text and images, highlight, draw, whiteout, and rotate or reorder pages. Free, with no sign-up.",
        "h1": "Edit PDF Online",
        "tagline": "Change text, add notes and images, and manage pages - right in your browser.",
        "cta": {"label": "Open the PDF Editor", "href": "/editor", "note": "Free. No account needed."},
        "howto": "How to edit a PDF online",
        "steps": [
            ("Open your PDF", "Open the editor and choose the PDF you want to change."),
            ("Pick a tool", "Edit text, add text or images, highlight, draw, whiteout or manage pages."),
            ("Save your PDF", "Click Save PDF to download the edited file."),
        ],
        "benefits": [
            ("Edit typed text in place", "On PDFs that already contain text, lines are read directly so size and position match the original."),
            ("Scanned pages too", "Run OCR to turn scanned lines into editable text."),
            ("Mark up", "Highlight, underline, strike through, draw, add shapes and sticky notes."),
            ("Add and cover", "Add text, images and signatures, or whiteout something you want hidden."),
            ("Manage pages", "Rotate, delete, add and reorder pages, with undo and redo."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Can I edit the text in a PDF?", "Yes. In a PDF that contains typed text, double-click a line to change it. The new text keeps the original size and position, using the closest standard font."),
            ("Can I edit a scanned PDF?", "Yes, using OCR. Click Run OCR, then double-click a detected line to edit it. OCR accuracy depends on how clear the scan is, and busy table layouts may be easier to fix with Whiteout plus Add Text."),
            ("Will the edited text use the same font?", "The size and position match, but text is saved in the closest standard font (sans-serif, serif or monospace). Bold and special fonts are not preserved."),
            ("Any tips for the best results?", "Save before changing the zoom or rotating pages - redrawing the page clears text edits that you haven't saved yet."),
        ],
        "related": ["ocr", "sign", "redact", "compress"],
    },
    {
        "key": "ocr", "slug": "ocr-pdf", "template": "landing.html", "category": "edit",
        "icon": "🔤", "name": "OCR PDF", "processing": "mixed",
        "short": "Make scanned text editable with OCR.",
        "meta_title": "OCR PDF Online - Edit Text in Scanned PDFs | PDFJantaParty",
        "meta_description": "Turn text in scanned PDFs into editable lines with OCR, then correct it and save. English text. Free, with no sign-up.",
        "h1": "OCR PDF - Edit Text in Scanned PDFs",
        "tagline": "Read the text in a scanned PDF so you can correct it and save a new copy.",
        "cta": {"label": "Open the PDF Editor", "href": "/editor", "note": "Click Run OCR once your PDF is open."},
        "howto": "How to use OCR on a scanned PDF",
        "steps": [
            ("Open the scanned PDF", "Open the editor and choose your PDF."),
            ("Click Run OCR", "Every page is read and the text is split into editable lines."),
            ("Edit and save", "Double-click a line to change it, then click Save PDF."),
        ],
        "benefits": [
            ("Line-by-line editing", "Each detected line or column becomes its own editable box."),
            ("Typed pages are instant", "Pages that already contain text are read directly, with no OCR wait."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Which languages does OCR support?", "English text only at the moment."),
            ("Does this make the whole PDF searchable?", "No. OCR here lets you edit lines of text: your corrections are placed over the scan when you save. It does not add a hidden, searchable text layer to the whole document."),
            ("How long does OCR take?", "Pages that already contain typed text are instant. Scanned pages are processed one after another, so a long scan can take a few minutes."),
            ("How accurate is it?", "It depends on the scan. Clear, straight, high-contrast pages work best, and you can correct any mistakes when you edit the line."),
        ],
        "related": ["edit", "pdf-to-word", "compress", "sign"],
    },
    {
        "key": "sign", "slug": "sign-pdf", "template": "sign_fill.html", "category": "edit",
        "icon": "✍️", "name": "Sign & Fill PDF", "processing": "browser",
        "short": "Sign, add initials and fill forms.",
        "meta_title": "Sign PDF Online Free - Signature and Forms | PDFJantaParty",
        "meta_description": "Sign a PDF online: draw or upload your signature, add initials, fill text fields and checkboxes, then download. Free, with no sign-up.",
        "tagline": "Add your signature or initials and fill in forms without printing anything.",
        "howto": "How to sign a PDF online",
        "steps": [
            ("Open your PDF", "Choose the PDF you need to sign or fill."),
            ("Add your signature", "Draw it, upload an image of it, or type your initials, then drag it into place."),
            ("Fill in and save", "Complete the form fields or add your own, then click Save & Download."),
        ],
        "benefits": [
            ("Draw, upload or initial", "Create your signature the way that suits you."),
            ("Fill forms", "Fillable text fields and checkboxes already in the PDF are detected for you."),
            ("Stays in your browser", "The PDF is processed on your device and isn't uploaded to our server."),
        ],
        "faq": [
            ("Is this a legally valid signature?", "It places an image of your signature or initials on the PDF, which is how most everyday e-signatures work. It is not a certificate-based digital signature, and whether it is accepted depends on who asked for the document."),
            ("Can I fill in the form fields in my PDF?", "Yes. Text fields and checkboxes already in the PDF appear as fillable boxes, and you can add your own text fields and checkboxes. Radio buttons and dropdowns are not supported yet."),
            ("Can I place my signature on any page?", "Yes. Move between pages, then drag your signature or initials to where you want them."),
        ],
        "related": ["edit", "redact", "protect", "compress"],
    },
    # ------------------------------------------------------------------- security
    {
        "key": "redact", "slug": "redact-pdf", "template": "redact_pdf.html", "category": "security",
        "icon": "⬛", "name": "Redact PDF", "processing": "server",
        "short": "Permanently remove sensitive content.",
        "meta_title": "Redact PDF Online - Permanently Remove Text | PDFJantaParty",
        "meta_description": "Redact a PDF online: draw boxes over sensitive information and permanently remove it from the file, not just cover it. Free, no sign-up.",
        "tagline": "Black out sensitive details and remove the content underneath for good.",
        "howto": "How to redact a PDF",
        "steps": [
            ("Open your PDF", "Choose the PDF that contains sensitive details."),
            ("Mark the areas", "Drag boxes over anything that must be removed, on as many pages as you need."),
            ("Apply and download", "Apply the redactions and save the new PDF."),
        ],
        "benefits": [
            ("Truly removed", "The text and image content under each box is removed from the file, not just covered."),
            ("Any number of areas", "Mark several areas across several pages in one go."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Is redaction permanent?", "Yes. The content under each marked area is removed from the new PDF, so it can't be recovered by selecting or copying text. Your original file is not changed."),
            ("How is this different from a white box?", "A white box only covers content, which can still be selected or extracted from the file. Redaction removes the content itself."),
            ("Should I check the result?", "Always. Open the redacted PDF and try to select text in the blacked-out areas to confirm it is gone before you share it."),
        ],
        "related": ["protect", "edit", "sign", "unlock"],
    },
    {
        "key": "protect", "slug": "protect-pdf", "template": "protect_pdf.html", "category": "security",
        "icon": "🔒", "name": "Protect PDF", "processing": "server",
        "short": "Lock a PDF with a password.",
        "meta_title": "Protect PDF with a Password Online - Encrypt PDF | PDFJantaParty",
        "meta_description": "Add a password to a PDF online with AES-256 encryption so only people with the password can open it. Free, with no sign-up.",
        "tagline": "Lock a PDF with a password so only people who know it can open it.",
        "howto": "How to password-protect a PDF",
        "steps": [
            ("Upload your PDF", "Choose the PDF you want to protect."),
            ("Set a password", "Enter the password you want people to use."),
            ("Download the protected PDF", "The new file asks for the password when opened."),
        ],
        "benefits": [
            ("AES-256 encryption", "A strong, widely used standard for protecting documents."),
            ("Works anywhere", "Any PDF reader will ask for the password."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("What kind of encryption is used?", "AES-256."),
            ("Can you recover my password if I forget it?", "No. We don't keep your password, so a forgotten password means the file can't be opened. Store it somewhere safe."),
            ("Can I remove the password later?", "Yes, with Unlock PDF - you will need the password."),
        ],
        "related": ["unlock", "redact", "sign", "compress"],
    },
    {
        "key": "unlock", "slug": "unlock-pdf", "template": "unlock_pdf.html", "category": "security",
        "icon": "🔓", "name": "Unlock PDF", "processing": "server",
        "short": "Remove a password you know from a PDF.",
        "meta_title": "Unlock PDF - Remove PDF Password Online | PDFJantaParty",
        "meta_description": "Remove the password from a PDF you have the password for, so it opens without one. Free, with no sign-up.",
        "tagline": "Remove the password from a PDF so it opens without asking.",
        "howto": "How to remove a password from a PDF",
        "steps": [
            ("Upload your PDF", "Choose the protected PDF."),
            ("Enter its password", "Type the password you were given."),
            ("Download the unlocked PDF", "The new file opens without a password."),
        ],
        "benefits": [
            ("Opens without a prompt", "Skip typing the password every time."),
            ("Contents unchanged", "Only the password is removed."),
            ("Free, no sign-up", "No account and no watermark."),
        ],
        "faq": [
            ("Can you unlock a PDF if I forgot the password?", "No. You need the correct password. This tool removes a password you know; it doesn't guess or crack passwords."),
            ("What happens if I enter the wrong password?", "The tool tells you the password is incorrect and no file is produced."),
            ("Can I add the password back later?", "Yes, with Protect PDF."),
        ],
        "related": ["protect", "redact", "compress", "merge"],
    },
]

# ----------------------------------------------------------------------------
# Helpers used by the Flask app and templates
# ----------------------------------------------------------------------------

_BY_KEY = {t["key"]: t for t in TOOLS}
_BY_SLUG = {t["slug"]: t for t in TOOLS}


def get_tool(key):
    return _BY_KEY[key]


def tool_url(tool):
    return "/" + tool["slug"]


def canonical(path):
    return SITE_URL + (path if path.startswith("/") else "/" + path)


def faq_for(tool):
    """Tool-specific FAQ + the per-tool privacy answer + a short pricing answer."""
    items = list(tool["faq"])
    items.append(PRIVACY_FAQ[tool["processing"]])
    items.append((f"Is {tool['name']} free?", f"Yes. {tool['name']} is free to use and doesn't need an account."))
    return items


def related_tools(tool):
    return [
        {"name": r["name"], "icon": r["icon"], "short": r["short"], "url": tool_url(r)}
        for r in (_BY_KEY[k] for k in tool["related"])
    ]


def prepare_tool(tool):
    """Everything the templates need for one tool, in a plain dict."""
    data = dict(tool)
    data["url"] = tool_url(tool)
    data["faq_all"] = faq_for(tool)
    data["related_tools"] = related_tools(tool)
    data["h1"] = tool.get("h1", tool["name"])
    return data


def _ld(obj):
    # "</" would end the <script> block early, so it is escaped.
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def breadcrumb_ld(trail):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": canonical(path)}
            for i, (name, path) in enumerate(trail)
        ],
    }


def seo_for_tool(tool):
    url = canonical(tool_url(tool))
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": tool["name"],
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Web",
            "url": url,
            "description": tool["meta_description"],
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq_for(tool)
            ],
        },
        breadcrumb_ld([("Home", "/"), ("All PDF Tools", "/tools"), (tool["name"], tool_url(tool))]),
    ]
    return {
        "title": tool["meta_title"],
        "description": tool["meta_description"],
        "canonical": url,
        "noindex": False,
        "schema": [_ld(s) for s in schema],
    }


def seo_for_home():
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": canonical("/"),
    }
    return {
        "title": "PDFJantaParty - Free Online PDF Tools: Merge, Compress, Convert, Edit & Sign",
        "description": "Free online PDF tools: merge, split, compress to 100 KB or 50 KB, convert to and from Word, Excel and JPG, edit, sign and protect PDFs. No sign-up.",
        "canonical": canonical("/"),
        "noindex": False,
        "schema": [_ld(schema)],
    }


def seo_for_hub():
    items = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "PDF tools",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t["name"], "url": canonical(tool_url(t))}
            for i, t in enumerate(TOOLS)
        ],
    }
    return {
        "title": "All Free PDF Tools - Merge, Compress, Convert, Edit & Sign | PDFJantaParty",
        "description": "Browse every free PDF tool: merge, split, compress, convert to and from Word, Excel and JPG, edit, OCR, sign, redact, protect and unlock. No sign-up.",
        "canonical": canonical("/tools"),
        "noindex": False,
        "schema": [_ld(items), _ld(breadcrumb_ld([("Home", "/"), ("All PDF Tools", "/tools")]))],
    }


def tools_by_category():
    return [
        {
            "key": key, "name": name, "blurb": blurb,
            "tools": [dict(t, url=tool_url(t)) for t in TOOLS if t["category"] == key],
        }
        for key, name, blurb in CATEGORIES
    ]
