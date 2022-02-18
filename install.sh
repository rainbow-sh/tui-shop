#!/bin/sh

echo "Installing..."
pip install -r ./requirements.txt # Install pip modules
cp ./tui-shop.py /usr/bin/tui-shop # Copy bin
chmod +x /usr/bin/tui-shop # Make install file executable

echo "Cleaning up..."
cd ../ # Cd out of the directory
rm -r tui-shop

echo "Done!"