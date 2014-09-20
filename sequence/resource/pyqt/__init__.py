"""Contain the pyqt resources generated from ui and qrc files."""

# Build resources
import build_ui
build_ui.build()

# Include build directory
import build
__path__.extend(build.__path__)
