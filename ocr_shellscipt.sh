export PATH="/usr/local/Cellar/tesseract/4.1.1/bin/":$PATH #path to tesseract
export PATH="usr/local/bin/":$PATH #path to ocrmypdf
ocrmypdf --output-type pdf --deskew --force-ocr "$1" "$1" #$1 is the file to be ocr'd (save to same place)