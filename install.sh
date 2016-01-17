if [ -d "dist" ]; then
    sudo cp -r dist/fastnote /opt;
    sudo ln -s /opt/fastnote/fastnote /usr/bin/fastnote;
    echo "installed successfully";
else
    echo "the program is not packed";
fi
