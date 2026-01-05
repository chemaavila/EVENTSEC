Quick Links → Google Wizard
flowchart TD
  Q[Quick Link click] --> W[Open Wizard/Form]
  W --> P[Prefill from context (alert/case) if available]
  P --> V{Validate}
  V -- ok --> S[Generate Google/Gmail/Drive links]
  S --> UI[Render buttons + copyable queries]
  V -- error --> ERR[Show inline errors]
