#!/bin/bash

# Get arguments from user	
args=("$@")
# You can get the number of arguments from the special parameter $#
echo "Arguments passed: $#"

# Count the number of files in given directory that have the chosen file type
# Intuitively:
# 1) list all files of args[0] type in given directory
# 2) 2> /dev/null command redirects all error messages to the specified path
# 3) pipe the matching files with the “wc” command to count the number of files
# 4) save as "n"
n=$(ls *.${args[0]} 2> /dev/null | wc -l)
echo "Number of matching files: $n"

# Check if the particular number of arguments is satisfied
if (($# < 2)); then
	echo "Not enough arguments were passed. Please enter 2 distinct file types: 1 = current file type, 2 = conversion file type."
	exit
elif (($n == 0)); then
	echo "There are no files of .${args[0]} type in the current directory. Please respecify your targeted file type."
	exit
elif (($# > 2)); then
	echo "Too many arguments passed. Please only enter 2 distinct file types: 1 = current file type, 2 = conversion file type."
	exit
fi

# Iterate through each file of type 1 within current directory
for f in *.${args[0]}; do

	# Get basename of current file
	name=$(basename $f .${args[0]})

	# Convert the type of the targeted file
       	mv $f $name.${args[1]}

       	echo "Successfully change $f to $name.${args[1]}"

done
