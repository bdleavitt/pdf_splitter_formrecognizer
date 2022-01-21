import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer
from pathlib import Path
import json
import datetime
from pathlib import Path
from json import JSONEncoder
from dotenv import load_dotenv
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential

## Load the needed environment variables
load_dotenv()
# Endpoint URL
endpoint = os.environ['ENDPOINT']
# Subscription Key
apim_key = os.environ['APIM_KEY']
credential = AzureKeyCredential(apim_key)

# Model ID
model_id = os.environ['MODEL_ID']

## directory holding the pdfs to analyze
source_directory = "./forms_split"

## Make a form recognizer client
form_recognizer_client = FormRecognizerClient(endpoint, credential)

## Get all all of pdfs in the target directory
forms = [str(form) for form in Path(source_directory).rglob('*.pdf')]



## This function calls the Forms Recognizer API then calls the write_output function
def analyze_form(form_client, model_id, input_form_path):
    start = default_timer()
    print(f"Submitting {input_form_path}")
    with open(input_form_path, "rb") as fd:
        form = fd.read()
    try:
        poller = form_client.begin_recognize_custom_forms(model_id=model_id, form=form)
        result = poller.result()
        total = default_timer() - start
        print(f"Completed {input_form_path}: in {round(total, 2)} secs")
    except Exception as e:
        total = default_timer() - start
        print(round(total, 2), e)
        return False

    ## And write out the result to disk
    path_parsed = os.path.normpath(input_form_path).split(os.sep)
    output_directory = os.path.join('results', path_parsed[-2])
    output_file_name = f'{path_parsed[-1]}_results.json'
    write_output(result, output_directory=output_directory, output_file_name=output_file_name)
    return True

## Writes dictionary object to file
def write_output(form_recognizer_result, output_directory, output_file_name):
    start = default_timer()
    path = Path(output_directory)
    path.mkdir(parents=True, exist_ok=True, )
    output_path = os.path.join(output_directory, output_file_name)
    try:
        with open(output_path, 'w') as outfile:
            output = json.dumps(form_recognizer_result[0].to_dict(), cls=DateTimeEncoder)
            outfile.write(output)
            total = default_timer() - start
            print(f"Wrote to {output_path} in {total} seconds")
    except Exception as e:
        total = default_timer() - start
        print(f"There was an error writing to {output_path} that occured after {total} seconds")
        print(e)

## Helper Function to aid in writing the results to JSON
class DateTimeEncoder(JSONEncoder):    
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

async def analyze_forms_async(forms, form_recognizer_client, model_id):
    ## form recognizer allows for 15 concurrent job submissions,
    ## so limiting the ThreadPoolExecutor to 15
    tpe = ThreadPoolExecutor(max_workers=15)
    loop = asyncio.get_event_loop()
    loop.set_default_executor(tpe)

    ## Take each form in the list
    ## make an async task from it that uses
    ## the analyze_form function to get the data from the service
    ## and start the task running in the event loop

    tasks = [loop.run_in_executor(None, analyze_form, form_recognizer_client, model_id, form) for form in forms]
    
    ## gather all the tasks from the event loop
    ## once they finish running
    ## (This is a blocking command)

    for response in await asyncio.gather(*tasks):
        print(response)
        
if __name__ == '__main__':
    start = default_timer()
    print("Starting the Job Submission... buckle up, buttercup.")
    asyncio.run(analyze_forms_async(forms=forms, form_recognizer_client=form_recognizer_client, model_id=model_id))
    elapsed = default_timer() - start
    print("completed...", elapsed, "seconds")
