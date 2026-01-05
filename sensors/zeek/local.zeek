@load policy/tuning/json-logs

# Enable common protocols for IDS visibility.
redef LogAscii::use_json = T;
