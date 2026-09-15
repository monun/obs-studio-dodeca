"""OBS Python script for repeatable Qt checks in a disposable test profile.

Requires PyQt6 built against the same Qt as OBS. Communicates using local JSON
files under the directory in the script's `directory` setting. Never load this
test script in a production OBS profile.
"""

import json
import traceback
from pathlib import Path

import obspython as obs
from PyQt6.QtCore import QObject, QTimer, QMetaObject, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QAbstractButton, QComboBox, QLineEdit, QSpinBox, QDialogButtonBox, QWidget, QListWidget, QTabWidget, QLabel, QMessageBox, QScrollArea, QGroupBox

timer = None
directory = None
last_id = None


def find(name):
    if "/" in name:
        parent, child = name.split("/", 1)
        widget = find(parent).findChild(QObject, child)
        assert widget is not None, name
        return widget
    if name == "buttonBox":
        return find("OBSBasicSettings").findChild(QDialogButtonBox, name)
    for top in QApplication.topLevelWidgets():
        if top.objectName() == name:
            return top
        widget = top.findChild(QObject, name)
        if widget is not None:
            return widget
    raise AssertionError(f"Widget not found: {name}")


def snapshot(names):
    values = {}
    for name in names:
        widget = find(name)
        entry = {"class": widget.metaObject().className()}
        if isinstance(widget, QWidget):
            entry.update(enabled=widget.isEnabled(), visible=widget.isVisible(),
                         accessible=widget.accessibleName(), width=widget.width(), height=widget.height(),
                         focus_policy=int(widget.focusPolicy()), focused=widget.hasFocus(),
                         minimum_width=widget.minimumSizeHint().width(),
                         exposed=widget.visibleRegion().boundingRect().contains(widget.rect()),
                         scale=widget.devicePixelRatioF())
            if isinstance(widget.parentWidget(), QGroupBox):
                entry["group_title"] = widget.parentWidget().title()
        if isinstance(widget, QAbstractButton):
            entry.update(checked=widget.isChecked(), text=widget.text())
        elif isinstance(widget, QComboBox):
            entry.update(text=widget.currentText(), value=widget.currentData(), count=widget.count())
        elif isinstance(widget, QLineEdit):
            entry["text"] = widget.text()
        elif hasattr(widget, "text"):
            entry["text"] = widget.text()
        values[name] = entry
    return values


def poll():
    global last_id
    request = directory / "ui-request.json"
    if not request.exists():
        return
    command = json.loads(request.read_text())
    if command["id"] == last_id:
        return
    last_id = command["id"]
    response = {"id": last_id}
    try:
        action = command["action"]
        if action == "invoke":
            QMetaObject.invokeMethod(find(command["object"]), command["method"], Qt.ConnectionType.QueuedConnection)
        elif action == "set":
            for name, value in command["values"].items():
                widget = find(name)
                if isinstance(widget, QAbstractButton):
                    if widget.isChecked() != value:
                        widget.setChecked(value)
                        widget.clicked.emit(value)
                elif isinstance(widget, QComboBox):
                    index = widget.findData(value)
                    if index < 0:
                        index = widget.findText(str(value))
                    if index < 0:
                        index = next((i for i in range(widget.count()) if widget.itemText(i).startswith(str(value) + " -")), -1)
                    assert index >= 0, (name, value)
                    widget.setCurrentIndex(index)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QListWidget):
                    widget.setCurrentRow(value)
                elif isinstance(widget, QTabWidget):
                    widget.setCurrentIndex(value)
                else:
                    raise AssertionError(f"Unsupported widget {name}")
        elif action == "button":
            widget = find(command["object"])
            if isinstance(widget, QDialogButtonBox):
                button = widget.button(getattr(QDialogButtonBox.StandardButton, command["button"]))
                QTimer.singleShot(0, button.click)
            else:
                QTimer.singleShot(0, widget.click)
        elif action == "snapshot":
            response["widgets"] = snapshot(command["names"])
        elif action == "items":
            widget = find(command["object"])
            response["items"] = [widget.itemText(i) for i in range(widget.count())]
        elif action == "index":
            find(command["object"]).setCurrentIndex(command["index"])
        elif action == "ensure_visible":
            widget = find(command["object"])
            parent = widget.parentWidget()
            while parent is not None:
                if isinstance(parent, QScrollArea):
                    parent.ensureWidgetVisible(widget)
                parent = parent.parentWidget()
        elif action == "labels":
            response["labels"] = [{"name": w.objectName(), "text": w.text()} for w in
                                  find(command["object"]).findChildren(QLabel) if w.isVisible()]
        elif action == "key":
            widget = find(command["object"])
            QApplication.setActiveWindow(widget.window())
            widget.setFocus()
            QTest.keyClick(widget, getattr(Qt.Key, command["key"]))
            focused = QApplication.focusWidget()
            response["focus"] = focused.objectName() if focused else None
        elif action == "table":
            model = find(command["object"]).model()
            for cell in command.get("cells", []):
                assert model.setData(model.index(cell["row"], cell["column"]), cell["value"], Qt.ItemDataRole.EditRole)
            response["rows"] = [[str(model.data(model.index(r, c), Qt.ItemDataRole.DisplayRole)) for c in range(model.columnCount())]
                                for r in range(model.rowCount())]
        elif action == "messages":
            boxes = [w for w in QApplication.topLevelWidgets() if isinstance(w, QMessageBox) and w.isVisible()]
            response["messages"] = [{"title": w.windowTitle(), "text": w.text()} for w in boxes]
            if command.get("dismiss"):
                for box in boxes:
                    QTimer.singleShot(0, box.accept)
        elif action == "windows":
            response["windows"] = [{"name": w.objectName(), "title": w.windowTitle(), "visible": w.isVisible()}
                                   for w in QApplication.topLevelWidgets()]
        elif action == "outputs":
            response["outputs"] = {}
            for name, getter in [("record", obs.obs_frontend_get_recording_output),
                                 ("replay", obs.obs_frontend_get_replay_buffer_output),
                                 ("stream", obs.obs_frontend_get_streaming_output)]:
                output = getter()
                encoders = []
                if output:
                    for index in range(12):
                        encoder = obs.obs_output_get_audio_encoder(output, index)
                        if encoder:
                            settings = obs.obs_encoder_get_settings(encoder)
                            encoders.append({"slot": index, "mix": obs.obs_encoder_get_mixer_index(encoder),
                                             "name": obs.obs_encoder_get_name(encoder),
                                             "bitrate": obs.obs_data_get_int(settings, "bitrate")})
                            obs.obs_data_release(settings)
                    obs.obs_output_release(output)
                response["outputs"][name] = encoders
        elif action == "screenshot":
            find(command["object"]).grab().save(str(directory / command["file"]))
        elif action == "close":
            QTimer.singleShot(0, find(command["object"]).close)
        else:
            raise AssertionError(action)
        response["success"] = True
    except Exception:
        response.update(success=False, error=traceback.format_exc())
    target = directory / "ui-response.json"
    temporary = directory / "ui-response.tmp"
    temporary.write_text(json.dumps(response, indent=2))
    temporary.replace(target)


def script_load(settings):
    global timer, directory, last_id
    directory = Path(obs.obs_data_get_string(settings, "directory"))
    directory.mkdir(parents=True, exist_ok=True)
    request = directory / "ui-request.json"
    last_id = json.loads(request.read_text())["id"] if request.exists() else None
    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(100)


def script_unload():
    global timer
    if timer is not None:
        timer.stop()
        timer = None
