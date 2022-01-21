The scripts in this repo help take a multi-page PDF document and split it into individual pages before sending to the specified form recognizer model. 

This can be useful when you have a lot of similarly formatted pages of in form. 

To get started:
1. Clone the repository
2. Rename the .env-sample file to .env
3. Update the values in .env to your cognitive services key and form recognizer model. 


## Step 1: Split PDFs
Run the file 01_split_pdfs.py to simply take each page of a document and load it to a particular directory. 

After you run this file, you could use these split pages to upload to FR service to tag and train a model. 

## Step 2: Analyze Forms Async
Once you have a trained model, you can run script 02_analyze_form_azync.py to submit each form page for data extraction. 

## Step 3: Combine Results:
03_flatten_and_combine_fr_json.py will take the results from step 2 and combine them into a single tabular-style dataset which can be used for subsequent analysis. 