#!/bin/bash
# Installs the two launchd jobs: evening chain at 23:15 on weekdays (after the 22:30 collector), morning send at 07:00.
set -e
R="$HOME/Documents/PaperTrading/book"
for job in evening:23:15 morning:07:00; do
  name=${job%%:*}; hh=$(echo $job | cut -d: -f2); mm=$(echo $job | cut -d: -f3)
  cat > "$HOME/Library/LaunchAgents/com.yasanji.book.$name.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.yasanji.book.$name</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$R/$name.sh</string></array>
  <key>StartCalendarInterval</key><array>
$(for d in 1 2 3 4 5; do echo "    <dict><key>Weekday</key><integer>$d</integer><key>Hour</key><integer>$((10#$hh))</integer><key>Minute</key><integer>$((10#$mm))</integer></dict>"; done)
  </array>
</dict></plist>
PL
  launchctl unload "$HOME/Library/LaunchAgents/com.yasanji.book.$name.plist" 2>/dev/null || true
  launchctl load "$HOME/Library/LaunchAgents/com.yasanji.book.$name.plist"
  echo "loaded com.yasanji.book.$name ($hh:$mm weekdays)"
done
