from pathlib import Path

import pdfplumber

FILES = [
    Path("/Users/tianaoliu/Downloads/PIIS0092867424008997-2.pdf"),
    Path("/Users/tianaoliu/Downloads/science.adf5300.pdf"),
    Path("/Users/tianaoliu/Downloads/s41586-021-03532-0.pdf"),
    Path("/Users/tianaoliu/Downloads/s41586-021-03532-0-2.pdf"),
    Path("/Users/tianaoliu/Downloads/s41467-026-68495-0.pdf"),
    Path("/Users/tianaoliu/Downloads/s41467-019-13549-9.pdf"),
    Path("/Users/tianaoliu/Downloads/s40168-026-02417-6.pdf"),
    Path("/Users/tianaoliu/Downloads/PIIS0092867424008997.pdf"),
]

out = Path("workspace/pdf_text")
out.mkdir(parents=True, exist_ok=True)

for pdf in FILES:
    pages = []
    with pdfplumber.open(pdf) as doc:
        for page_number, page in enumerate(doc.pages, start=1):
            pages.append(f"\n\n--- PAGE {page_number} ---\n{page.extract_text() or ''}")
    text = "\n".join(pages)
    target = out / f"{pdf.stem}.txt"
    target.write_text(text, encoding="utf-8")
    print(target, len(text))
