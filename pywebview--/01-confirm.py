import webview

if __name__ == '__main__':
    # Create a standard webview window
    webview.create_window(
        '确认退出?', 'https://pywebview.flowrl.com/hello', confirm_close=True
    )
    webview.start()

