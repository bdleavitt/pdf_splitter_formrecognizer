import os
from pathlib import Path
from PyPDF2 import PdfFileReader, PdfFileWriter

input_directory_path = "./forms"
output_directory_path = "./forms_split"

## Splits a multi-page PDF into one file per page. 
def pdf_splitter(input_path, output_directory):
    fname = os.path.splitext(os.path.basename(input_path))[0]
    pdf = PdfFileReader(input_path)
    for page in range(pdf.getNumPages()):
        pdf_writer = PdfFileWriter()
        pdf_writer.addPage(pdf.getPage(page))
        output_directory_path = os.path.join(output_directory, fname)

        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)

        output_filename = '{}_page_{}.pdf'.format(fname, page+1)
        
        output_file_path = os.path.join(output_directory, fname, output_filename)
        with open(output_file_path, 'wb') as out:
            pdf_writer.write(out)
        print('Created: {}'.format(output_filename))


if __name__ == '__main__':
    ## Get List of each pdf in input directory and split them into individual pages
    form_path_list = [str(form) for form in Path(input_directory_path).rglob('*.pdf')]

    print(f'Splitting {len(form_path_list)} documents into individual files')

    for file in form_path_list:  
        pdf_splitter(file, output_directory_path)
        

    split_form_list = [str(form) for form in Path(output_directory_path).rglob('*.pdf')]

    print(f'Split {len(form_path_list)} documents into {len(split_form_list)} individual files')

