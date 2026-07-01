import webview, sys
def on_closed(): sys.exit(0)
if __name__ == '__main__':
    window = webview.create_window('MISO OS [DIAGNOSTIC]', 'http://159.223.186.21:8000', maximized=True)
    window.events.closed += on_closed
    webview.start(debug=True)
