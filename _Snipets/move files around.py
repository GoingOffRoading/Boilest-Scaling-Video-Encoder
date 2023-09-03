Saving for later

    if os.path.exists('/boil_hold/' + file_name) AND os.path.exists(input_file):
        print('Original and Encoded Files Exists')
        time.sleep(2)
        print('Renaming the original file')
        os.rename(input_file, 'original_' + file) 
        time.sleep(2)
        print('Moving the encoded file')
        os.rename('./boil_hold/' + file, file)
        time.sleep(2)
        print('Deleting the original file')
        os.remove('original_' + file)
        time.sleep(2)
        print ('Done')    
    else:
         print("The file does not exist")