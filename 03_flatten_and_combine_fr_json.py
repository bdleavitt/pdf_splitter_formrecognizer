import os
import json
import pandas as pd
from pathlib import Path
import string

folder_path = "./results"

clean_results = []

def get_value_with_type(key, value_dict):
    return_dict = {}
    value_type = value_dict['value_type']
    
    if value_type == 'string':
        return_dict[key] = value_dict['value']
    elif value_type == 'dictionary':
        for k, v in value_dict['value']['Values']['value'].items():
            return_dict[k] = v['value']
    elif value_type == 'list':
        for field in value_dict['value']:
            return_key = field['value']['Keys']['value']
            try:
                return_value = field['value']['Values']['value']
            except Exception as e:
                return_value = field['value']['Values']['value_data']['text']
            
            return_dict[return_key] = return_value
    else:
        return_dict = {key: None}
    return return_dict 

def clean_dict_keys(dict):
    cleaned_dict = {}
    page_title_clean = ''.join(e for e in dict['Page Title'] if e.isalnum())
    if dict['Page Subtitle'] is None:
        page_subtitle_clean = ''
    else: 
        page_subtitle_clean = ''.join(e for e in dict['Page Subtitle'] if e.isalnum())

    key_prefix = f'{page_title_clean}_{page_subtitle_clean}'

    cleaned_dict['PageName'] = key_prefix

    for k, v in dict.items():        
        if (k == 'Page Title' or k=='Page Subtitle'):
            continue
        if k is None:
            continue
        if k == 'Serial':
            cleaned_dict['Serial'] = v
        else:
            cleaned_key = ''.join(e for e in k if e.isalnum())
            combined_key = f'{key_prefix}_{cleaned_key}'
            cleaned_dict[combined_key] = v

    return cleaned_dict

def clean_pandas_columns(df):
    ### Clean up the column names
    ## Remove weird characters
    df.columns = [str(colname).encode(encoding="ascii", errors="ignore").decode() for colname in df.columns]
    ## Remove punctuation, except the @symbol and - symbol
    punct = string.punctuation.replace('@','').replace('-','')
    df.columns = ["".join([ch for ch in colname if ch not in punct]) for colname in df.columns]
    ## Remove white spaces
    df.columns = [str(colname).replace(' ', '') for colname in df.columns]
    ## Make all the column names uppercase
    df.columns = [str(colname).upper() for colname in df.columns]

    ### Rename columns mis-read by FR
    cleaning_col_names = {
        'HYSTERESI':'HYSTERESIS',
        'HYSTEREI':'HYSTERESIS',
        'OLLTEMP':'OILTEMP',
        'CI':'C1',
        'OLITEMP':'OILTEMP',
        'OITTEMP':'OILTEMP',
        '800M':'800MA',
        'CZ':'C2',
        'OIITEMP':'OILTEMP',
        'RSULTANT':'RESULTANT',
        'CI-C2':'C1-C2',
        '22':'C2',
        '1-C2': 'C1-C2',
        'C1C2': 'C1-C2'
    }

    df = df.rename(columns=cleaning_col_names)

    ## COMBINE/COALESCE THE RENAMED COLUMNS INTO A SINGLE COLUMN
    print(f'Removing duplicate columns from {len(df.columns)}')

    ## Get a list of the target columns wiht no duplicates
    col_list = []
    for col in df.columns:
        if col not in col_list:
            col_list.append(col)

    for col in col_list: 
        ## If there are more than one column by that name
        num_columns_with_name = len(df[col].shape)
        if num_columns_with_name > 1:
            ## create a temp dataframe to merge values
            col_df = pd.DataFrame()        
            ## merge each column into the temp dataframe
            for i in range(num_columns_with_name):
                col_df = col_df.combine_first(df[col].iloc[:, [i]])

            ## drop the columns from the original dataframe, then reassign as a combined column
            df.drop([col], axis=1, inplace=True)
            df[col] = col_df[col]

    print(f'Removed duplicates. {len(df.columns)} columns remain')
    return df


#if __name__ == '__main__':

## Get a list of all the form recognizer outputs
result_path_list = [str(result) for result in Path(folder_path).rglob('*.json')]

## For each file, extract the field information
print(f'Parsing results from results files.')
excluded_files = []
for file in result_path_list:
    values_dict = {}
    values_dict['source_file'] = os.path.normpath(file).split(os.sep)[-2]
    values_dict['file_name'] = file
    

    with open(file, encoding="utf8") as json_file:
        data = json.load(json_file)

    if data['form_type_confidence'] < 0.79:
    ## If the form confidence is low, it probalby means this wasn't one of the target pages, so let's skip it. 
        excluded_files.append(file)
        continue
    
    fields_dict = data['fields']
    for key, value in fields_dict.items():
        parsed_dict = get_value_with_type(key, value)
        values_dict.update(parsed_dict)

    clean_results.append(values_dict)

print(f'Finished processing {len(result_path_list)} files; {len(excluded_files)} excluded.')
print(f'Writing excluded forms list to file')
with open('excluded_form_results.txt', 'w') as f:
    f.write(str(excluded_files))

df = pd.DataFrame.from_dict(clean_results)


## Get a list of the documents that had weird values for further training. 

weird_columns = ['file_name', 'Hysteresiş', 'Hystereşiş', '.@8.00 mA', 'Oll Temp','CI', None, 'OlI Temp', '· Null Bias', 'Oit Temp', '@-8.00 mÂ', '· mA Domain', 'CZ', 'P.SI Span', 'OII Temp', 'mA:Domain', 'PSI.range', 'P.SID', 'c1', 'mA. Domain', '.PSI range', 'OIl Temp', ':Return', '.mA Domain', 'P.SI range', 'Oil. Temp', 'Résultant', '@-10.00:mA', '@10:00 mA',   '· Linearity', 'mA-Domain', 'Ci-C2', 'PSI .Span', 'Low P.SI', 'Low: PSI', '22', '·mA Domain','.Low PSI',':mA Domain',':@10.00 mA','C1 C2','Null Biaş','.mA Span','.@-8.00 mA','Ć1-C2', 'Null, Bias','\' PSID']
weird_files = df[weird_columns].dropna(thresh=2)
weird_files
from pprint import pprint
pprint(weird_files['file_name'].to_list())






clean_df = clean_pandas_columns(df)

clean_df.to_csv('new_combined_results.csv', index_label=False, index=False, encoding="utf8")

## TODO: PIVOT COLUMNS TO PREPEND PAGE NAME TO COLUMNS
## GETTING SOME ERRORS WHEN TRYING TO PIVOT

# pivot_columns = ['SOURCEFILE', 'FILENAME', 'SERIAL', 'PAGETITLE','PAGESUBTITLE']
# unpivoted_df = clean_df.melt(id_vars=pivot_columns, var_name='Attribute', value_name='Value')
# unpivoted_df
# unpivoted_df['PageName'] = unpivoted_df['PAGETITLE'].str.cat(unpivoted_df['PAGESUBTITLE'], sep='|')
# unpivoted_df['ModAttribute'] = unpivoted_df['PageName'].str.cat(unpivoted_df['Attribute'], sep="|")
# ## drop the uncessary columns
# unpivoted_df = unpivoted_df[['SERIAL', 'ModAttribute', 'Value']]

# pivoted_df = unpivoted_df.pivot(index='SERIAL', columns=['ModAttribute'], values=['Value'])