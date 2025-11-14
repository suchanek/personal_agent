#!/bin/bash
################################################################################
# Create Ollama Login App
#
# This script creates an Application that can be added to Login Items
# to automatically start Ollama when you log in.
################################################################################

set -e

APP_NAME="StartOllama"
APP_DIR="$HOME/Applications"
APP_PATH="$APP_DIR/${APP_NAME}.app"
STARTUP_SCRIPT="$HOME/.local/bin/start_ollama.sh"

echo "Creating ${APP_NAME}.app in ~/Applications..."

# Create app bundle structure
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

# Create the executable script
cat > "${APP_PATH}/Contents/MacOS/${APP_NAME}" <<'EOF'
#!/bin/bash
# Start Ollama service
nohup "$HOME/.local/bin/start_ollama.sh" > "$HOME/Library/Logs/ollama/startup.log" 2>&1 &
EOF

chmod +x "${APP_PATH}/Contents/MacOS/${APP_NAME}"

# Create Info.plist
cat > "${APP_PATH}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.user.${APP_NAME}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "✓ Created ${APP_PATH}"
echo ""
echo "To make Ollama start automatically at login:"
echo "1. Open System Settings > General > Login Items"
echo "2. Click the '+' button"
echo "3. Navigate to ~/Applications and select ${APP_NAME}.app"
echo "4. Click 'Add'"
echo ""
echo "Or run this command to add it now:"
echo "osascript -e 'tell application \"System Events\" to make login item at end with properties {path:\"${APP_PATH}\", hidden:false}'"
