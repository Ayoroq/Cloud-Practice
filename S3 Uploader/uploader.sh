#!/bin/bash
# Title:         Uploader
# Description:   The main purpose is to upload file to s3
# Author:        Rqoeeb <ayoroq@gmail.com>
# Date:          2024-01-13
# Version:       1.0.0

# Exit codes
# ==========
# 0   no error
# 1   script interrupted
# 2   error description

#This is still a test in my bash scrippting exercise
#the end goal is to connect to the amazon s3 bulk and upload a given file

# function to delete a file in a specified

uploader() {

# This function upload  the specified file to the specified bucket.
# Parameters:
        #$1 - The path of the file to upload
        #$2 - The URI for the bucket to upload to
          if [ ! -f "$1" ]; then
            echo "ERROR: The file to upload is not present" # checking to see if the first arguement is present
            return 1
          elif [ ! "$2" ]; then
            echo "ERROR: There was no bucket specfied" # checking to see if the second arguement is present
            return 1
          else
              if ! aws s3 cp "$1" "$2"; then # The aws arguement to upload the files  ]
                 echo  "The file was not uploaded successfully"
              fi
          fi
}

uploader "$1" "$2"
