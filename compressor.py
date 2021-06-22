import os
import zipfile
 
# get files
def retrieve_file_paths(dir_name):
    file_paths = []
   
    for root, directories, files in os.walk(dir_name):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_paths.append(file_path)
         
    return file_paths
 
 
# compress files
def compress(dir_name):
    file_paths = retrieve_file_paths(dir_name)
   
    print('The following list of files will be compressed:')
    
    for file_name in file_paths:
        print(file_name)
     
    zip_file = zipfile.ZipFile(dir_name+'.zip', 'w')
    with zip_file:
        for obj in file_paths:
            zip_file.write(obj)
       
    print(zip_file.filename + " created successfully.")
    
    return zip_file
