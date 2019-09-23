# libreoffice-code-highlighter
Code snippet highlighter for LibreOffice Writer and Impress.

## INSTALLATION

### Install Dependencies
**Note: Close all the LibreOffice products before installing the dependencies**

#### Linux Users
Install libreoffice-script-provider-python
```
sudo apt-get install libreoffice-script-provider-python
```
The above command is for Ubuntu and its derivatives. Other Linux users, may not need this package.
If you encounter any problems after installing the extension, please check whether you have this or similar pacakge.

Install pygments for Python 3:
```
sudo pip3 install pygments
```

#### Windows Users
Windows users can install `pygments` using the following command
```
pip3 install pygments
```
After installation, set the environment variable: `PYTHONPATH` pointing to: `C:\Users\<UserName>\AppData\Local\Programs\Python\Python<PythonVersion>\Lib\site-packages`.
Here `<UserName>` must be replaced by your Windows username.

Check this [StackOverflow Answer](https://stackoverflow.com/a/4855685/4382663) to see how to set `PYTHONPATH` on Windows.

### Install Extension
Open LibreOffice, go to `Tools` -> `Extension Manager...` and add the extension `codehighlighter.oxt`

You can download the extension either from the official LibreOffice extensions page or from [releases](https://github.com/slgobinath/libreoffice-code-highlighter/releases).
If you have downloaded the `codehighlighter.oxt.zip` file from GitHub releases, extract it before adding to the LibreOffice.

## USAGE
- Open LibreOffice.
- Insert a Text Box (Insert -> Text Box).
- Copy and paste any code snippet into that Text Box.
- Select the Text Box.
- Tools -> Highlight Code
  - In the Dialog: Select the language and style
- Alternatively: Tools -> Highlight Code (previous settings)
  - Does not open a Dialog, but applies previous settings (persistent also between restarts of LO)

![Menu](screenshots/code-highlighter-menu.png?raw=true "Menu")
![Dialog](screenshots/code-highlighter-dialog.png?raw=true "Dialog")
![Result](screenshots/code-highlighter-result.png?raw=true "Result")

### Assign keyboard shortcuts (Optional)
Open the LibreOffice Writer and goto Tools -> Customize -> Keyboard
- Select the LibreOffice option button (Available on top left corner)
- Select any desired shortcut
- Select `user/codehighlighter.oxt/highlight/create_dialog` or `user/codehighlighter.oxt/highlight/apply_previous_settings` under the `LibreOffice Macros` Category
- Click on the Modify button to set the shortcut

![Shortcut](screenshots/code-highlighter-shortcut.png?raw=true "Shortcut")

## LICENSE
 - GPL v3
