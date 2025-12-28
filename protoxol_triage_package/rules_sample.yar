/*
Sample YARA rules (demo). Adjust for your own use cases.
*/
rule Suspicious_PowerShell_EncodedCommand
{
  meta:
    description = "Detects PowerShell commands with -enc / -EncodedCommand"
  strings:
    $s1 = "-enc" nocase
    $s2 = "-encodedcommand" nocase
    $s3 = "FromBase64String" nocase
  condition:
    any of them
}

rule Suspicious_URL_Dropper_Strings
{
  meta:
    description = "Flags patterns common in dropper URLs"
  strings:
    $u1 = "http://" nocase
    $u2 = "https://" nocase
    $u3 = "powershell" nocase
    $u4 = "curl" nocase
    $u5 = "wget" nocase
  condition:
    3 of them
}


