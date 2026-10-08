# Simple tool to merge PDFs or append images to the end of PDFs
import os
import shutil
from PIL import Image
from pypdf import PdfReader, PdfWriter
from sklearn import base
from helperFunctions.cmdParse import cmdParse

temp_dir = '_temp_to_be_deleted'

def merge_append(base_pdf = None, images_to_append = [], docs_to_append = [], output_pdf = None):

    if base_pdf is None:
        raise ValueError("Both base_pdf and output_pdf must be provided.")
    pdf = [os.path.join(temp_dir, os.path.split(img.replace('.jpg','.pdf'))[1]) for img in images_to_append]
    if os.path.exists(temp_dir) == False:
        os.makedirs(temp_dir)
    resolution=300
    images = [Image.open(img).save(pdf[i],resolution=resolution) for i,img in enumerate(images_to_append) if not img.endswith('.pdf')]

    reader = PdfReader(base_pdf)
    images = [PdfReader(img) for img in pdf]
    
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    for img in images:
        writer.add_page(img.pages[0])
    for doc in docs_to_append:
        rx = PdfReader(doc)
        for page in rx.pages:
            writer.add_page(page)

    if output_pdf is None:
        output_pdf = base_pdf.replace('.pdf','_merged.pdf')
    print(f'Writing: {output_pdf}')
    writer.write(output_pdf)
    shutil.rmtree(temp_dir)

    
kwargs = cmdParse({
    'base_pdf': None,
    'images_to_append': [],
    'docs_to_append': [],
    'output_pdf': None
})
merge_append(**kwargs)