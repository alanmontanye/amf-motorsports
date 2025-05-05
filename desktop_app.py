import sys
import webbrowser
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
import subprocess
import os
import signal
import psutil

class AMFDesktopApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.flask_process = None
        
        # Create system tray icon
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("app/static/img/icon.png"))
        self.tray.setVisible(True)
        
        # Create tray menu
        self.menu = QMenu()
        
        # Add menu items
        self.open_action = self.menu.addAction("Open AMF Motorsports")
        self.open_action.triggered.connect(self.open_app)
        
        # Add quick links submenu
        self.quick_links = self.menu.addMenu("Quick Links")
        self.add_quick_link("Financial Reports", "reports/financial")
        self.add_quick_link("Inventory Reports", "reports/inventory")
        self.add_quick_link("Parts List", "atv/parts")
        self.add_quick_link("Storage", "atv/storage")
        self.add_quick_link("Admin", "admin")
        
        # Add separator and quit action
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        
        # Attach menu to tray icon
        self.tray.setContextMenu(self.menu)
        
        # Start Flask server
        self.start_flask_server()
        
        # Show startup notification
        self.tray.showMessage(
            "AMF Motorsports",
            "App is running! Click the tray icon to access quick links.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def add_quick_link(self, name, path):
        """Add a quick link to the menu"""
        action = self.quick_links.addAction(name)
        action.triggered.connect(lambda: self.open_app(f"http://localhost:5000/{path}"))

    def start_flask_server(self):
        """Start the Flask development server"""
        env = os.environ.copy()
        env["FLASK_APP"] = "wsgi.py"
        env["FLASK_DEBUG"] = "1"
        
        # Start Flask server as a subprocess
        self.flask_process = subprocess.Popen(
            ["python", "-m", "flask", "run"],
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Give the server a moment to start
        QTimer.singleShot(2000, lambda: self.check_server_status())

    def check_server_status(self):
        """Check if the Flask server started successfully"""
        if self.flask_process and self.flask_process.poll() is None:
            # Server is running
            self.tray.setToolTip("AMF Motorsports - Server Running")
        else:
            # Server failed to start
            self.tray.showMessage(
                "AMF Motorsports - Error",
                "Failed to start server. Please check the console for errors.",
                QSystemTrayIcon.MessageIcon.Critical,
                3000
            )

    def open_app(self, url="http://localhost:5000"):
        """Open the app in default browser"""
        webbrowser.open(url)

    def quit_app(self):
        """Clean shutdown of the app"""
        # Stop Flask server
        if self.flask_process:
            # Kill the Flask process and all its children
            parent = psutil.Process(self.flask_process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.kill()
            parent.kill()
        
        # Quit Qt application
        self.app.quit()

    def run(self):
        """Run the desktop app"""
        # Start the Qt event loop
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = AMFDesktopApp()
    app.run()
