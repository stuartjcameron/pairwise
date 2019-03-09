# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 11:55:05 2018

@author: Stuart
"""

from docx import Document
fn = 'C:\\Users\\Stuart\\Dropbox (OPML)\\Apps\\pwv_cognitive\\AVSI 8a verde A.docx'
output_file = 'C:\\Users\\Stuart\\Dropbox (OPML)\\Apps\\pwv_cognitive\\output.txt'
doc = Document(fn)
paras = doc.paragraphs
paras = [p for p in paras if p.text != u'' and p.text != u'A']

with open(output_file, 'w') as file:
    for i, para in enumerate(paras):
        file.write("#{}: {}\n\n".format(i, para.text.encode('utf-8')))
        
