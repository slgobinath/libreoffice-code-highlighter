# libreoffice-code-highlighter
Code snippet highlighter for LibreOffice Writer and Impress.

## Installation
Install libreoffice-script-provider-python
```
sudo apt-get install libreoffice-script-provider-python
```

Install pygments for Python 3:
```
sudo pip3 install python3-pygments
```

Copy the Highlight.py to /usr/lib/libreoffice/share/Scripts/python/
```
sudo cp Highlight.py /usr/lib/libreoffice/share/Scripts/python/
```

Set the Read-Only permission to the script.
```
sudo chmod 0444 /usr/lib/libreoffice/share/Scripts/python/Highlight.py
```

Open the LibreOffice Writer and goto Tools -> Customize -> Keyboard
- Select the LibreOffice option button (Available on top left corner)
- Select any desired shortcut
- Select *share/Highlight/Highlight_source_code* under the Functions Category
- Click on the Modify button to set the shortcut

<img src="https://raw.githubusercontent.com/slgobinath/libreoffice-code-highlighter/master/Screenshots/Assign_Keyboard_Shortcut.png" width="600">

## Usage
### LibreOffice Impress
- Open LibreOffice Impress.
- Insert a Text Box (Insert -> Text Box).
- Copy and paste any code snippet into that Text Box.
- Create a new Style (Right click on an existing style -> New...)
- Name the Style as code-\<language\>
- Apply the style to your code snippet Text Box.
- Select the Text Box.
- Use your shortcut keys to execute the macro.

<img src="https://github.com/slgobinath/libreoffice-code-highlighter/blob/master/Screenshots/Impress_New_Style.png" width="600">

<img src="https://github.com/slgobinath/libreoffice-code-highlighter/blob/master/Screenshots/Impress_Apply_Style.png" width="600">

### LibreOffice Writer/Calc
- Open LibreOffice Writer/Calc.
- Insert a Text Box (Insert -> Text Box).
- Copy and paste any code snippet into that Text Box.
- Right click on the Text Box and select 'Description'.
- Add a description in the following format: code-\<language\>
- Select the Text Box
- Use your shortcut keys to execute the macro.

<img src="https://github.com/slgobinath/libreoffice-code-highlighter/blob/master/Screenshots/Writter_Add_Description.png" width="600">

## Credits
This macro is developed using the following two sources:
- [impress-code-highlighter](https://github.com/stummjr/impress-code-highlighter)
- [Python Syntax Highlighting in OpenOffice Impress](http://code.activestate.com/recipes/576796-python-syntax-highlighting-in-openoffice-impress)