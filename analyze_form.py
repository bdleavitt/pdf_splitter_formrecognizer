########### Python Form Recognizer Async Analyze #############
import json
import os
import datetime
from pathlib import Path
from json import JSONEncoder
from dotenv import load_dotenv
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential

class DateTimeEncoder(JSONEncoder):    
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

def analyze_form(form_client, model_id, input_form_path):
    with open(input_form_path, "rb") as fd:
        form = fd.read()
    poller = form_client.begin_recognize_custom_forms(model_id=model_id, form=form)
    result = poller.result()
    return result

def write_output(form_recognizer_result, output_directory, output_file_name):
    path = Path(output_directory)
    path.mkdir(parents=True, exist_ok=True, )
    output_path = os.path.join(output_directory, output_file_name)
    print(output_path)

    try:
        with open(output_path, 'w') as outfile:
            output = json.dumps(form_recognizer_result[0].to_dict(), cls=DateTimeEncoder)
            outfile.write(output)
            print(f"Successfully wrote output to {output_path}")
    except Exception as e:
        print(f"There was an error writing to {output_path}")
        print(e)





output_directory = 'results\\482900_SN9011'
output_file_name = '482900_SN9011_page_4.pdf.results.json'

write_output(res, output_directory=output_directory, output_file_name=output_file_name)