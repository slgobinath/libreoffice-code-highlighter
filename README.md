# libreoffice-code-highlighter
Code snippet highlighter for LibreOffice Writer and Impress.

## Installation
Install libreoffice-script-provider-python
```
sudo apt-get install libreoffice-script-provider-python
```

Install pygments for Python 3:
```
sudo pip3 install pygments
```

Open LibreOffice, go to `Tools` -> `Extension Manager...` and add the extension `codehighlighter.oxt`

## Assign keyboard shortcut to selected languages
Open the LibreOffice Writer and goto Tools -> Customize -> Keyboard
- Select the LibreOffice option button (Available on top left corner)
- Select any desired shortcut
- Select `user/codehighlighter.oxt/highlight/highlight_<language-name>_default` under the `LibreOffice Macros` Category
- Click on the Modify button to set the shortcut
<p align="center">
<img src="https://raw.githubusercontent.com/slgobinath/libreoffice-code-highlighter/master/screenshots/code-highlighter-shortcut.png" align="center" width="600">
</p>

## Usage
- Open LibreOffice.
- Insert a Text Box (Insert -> Text Box).
- Copy and paste any code snippet into that Text Box.
- Select the Text Box.
- Tools -> Highlight Code -> Select the language (Or use the shortcut key)

<p align="center">
<img src="https://raw.githubusercontent.com/slgobinath/libreoffice-code-highlighter/master/screenshots/code-highlighter-menu.png" align="center" width="600">
</p>
