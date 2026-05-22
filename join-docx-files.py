from docx import Document
from docxcompose.composer import Composer
import os

folder = "/Users/avenuecreek/Downloads/book/" 

files = sorted(
    [f for f in os.listdir(folder) if f.endswith(".docx")]
)

master = Document(os.path.join(folder, files[0]))
composer = Composer(master)

for file in files[1:]:
    doc = Document(os.path.join(folder, file))
    composer.append(doc)

composer.save("merged.docx")

print("Created merged.docx")
