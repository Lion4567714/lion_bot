#!/bin/bash

echo "THIS ISNT WORKING YET"
exit

if [ $# -ne 1 ]; then
    echo "Invalid number of arguments"
    echo "Usage: ./push_to_repo.sh [COMMIT MESSAGE]"
    exit
fi

git add -A
git commit -m $1
echo "Added and commited!"

read -n 1 -p "Are you sure you want to push to GitHub repo? [Y/N]: " input
echo ""

echo $input
if [ "$input" != "y" ] && [ "$input" != "Y" ]; then
    exit
fi

echo "Uploading changes to GitHub repo..."
git push
echo "Done!"
