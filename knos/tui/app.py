from textual.app import App
from textual.binding import Binding

from .screens.dashboard import DashboardScreen
from .screens.drill_queue import DrillQueueScreen


class StudyApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "Study Companion"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())


class DrillApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "Drill Queue"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DrillQueueScreen())


class ReaderApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "Reader"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        from knos.reader.screens import SelectMaterialScreen
        self.push_screen(SelectMaterialScreen())


if __name__ == "__main__":
    app = StudyApp()
    app.run()
