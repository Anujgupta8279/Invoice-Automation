from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET])

from kivy.uix.webview import WebView

class MyWebApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        box = BoxLayout(orientation='vertical')
        webview = WebView(url='http://your_public_or_local_streamlit_url:8501')
        box.add_widget(webview)
        return box

if _name_ == '_main_':
    MyWebApp().run()