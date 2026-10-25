"""Execute real Streamlit reruns and inspect the widget state."""

import unittest

from streamlit.testing.v1 import AppTest

from habitat2050.paths import PROJECT_ROOT


class AppTests(unittest.TestCase):
    def make_app(self):
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=45)
        app.run()
        self.assertEqual(list(app.exception), [])
        return app

    def test_chinese_default_and_english_toggle(self):
        app = self.make_app()
        self.assertEqual(app.title[0].value, "栖息地 2050")
        app.radio(key="ui_language").set_value("English").run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.title[0].value, "Habitat 2050")
        self.assertGreaterEqual(len(app.metric), 9)
        self.assertTrue(any("ROC-AUC" == metric.label for metric in app.metric))

    def test_views_cell_selection_and_threshold(self):
        app = self.make_app()
        initial_area = app.metric[0].value
        for view in ("future", "change", "classes", "current"):
            app.radio(key="map_view").set_value(view).run()
            self.assertEqual(list(app.exception), [])
        app.selectbox(key="grid_id").set_value("G2268").run()
        self.assertEqual(app.session_state["grid_id"], "G2268")
        app.slider(key="threshold").set_value(0.8).run()
        self.assertNotEqual(app.metric[0].value, initial_area)
        app.toggle(key="records").set_value(False).run()
        app.toggle(key="extrapolation").set_value(True).run()
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.session_state["grid_id"], "G2268")


if __name__ == "__main__":
    unittest.main()
