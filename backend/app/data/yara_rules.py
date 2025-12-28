"""Curated YARA rules referenced from the public Yara-Rules and InQuest/awesome-yara collections.

The intent is not to redistribute the full rule sets, but to ship a representative
excerpt that we can reference from the sandbox UI/tests without making outbound
network calls.
"""

YARA_RULES = [
    {
        "id": "yara-rules/ransomware/RANSOM_WANNACRY_GENERIC",
        "name": "Ransom_WannaCry_Generic",
        "source": "Yara-Rules",
        "author": "Yara-Rules maintainers",
        "description": "Detects artifacts related to the WannaCry ransomware family.",
        "reference": "https://github.com/Yara-Rules/rules",
        "tags": ["ransomware", "worm", "wannacry"],
        "rule": """
rule Ransom_WannaCry_Generic {
    meta:
        description = "Detects WannaCry binaries"
        author = "Yara-Rules"
        reference = "https://github.com/Yara-Rules/rules"
    strings:
        $a1 = "Global\\MsWinZonesCacheCounterMutexA" wide ascii
        $a2 = "taskdl.exe" ascii wide
        $a3 = "Please download `tas.exe` first!" wide
    condition:
        uint16(0) == 0x5A4D and 2 of ($a*)
}
""".strip(),
    },
    {
        "id": "yara-rules/phishing/PHISHING_DOC_MACRO",
        "name": "Office_Macro_Phishing_Lure",
        "source": "Yara-Rules",
        "author": "Yara-Rules maintainers",
        "description": "Detects Office documents weaponised with suspicious macros used in phishing kits.",
        "reference": "https://github.com/Yara-Rules/rules",
        "tags": ["phishing", "macro", "office"],
        "rule": """
rule Office_Macro_Phishing_Lure {
    meta:
        description = "Generic detection for macro phishing lures"
    strings:
        $s1 = "AutoOpen" ascii wide
        $s2 = "CreateObject(\\"Wscript.Shell\\")" ascii wide
        $s3 = "cmd.exe /c start" ascii wide
    condition:
        filesize < 5MB and 2 of ($s*)
}
""".strip(),
    },
    {
        "id": "inquest/awesome-yara/apt/SCARLET_MIMIKATZ",
        "name": "Scarlet Mimikat Credential Dumper",
        "source": "InQuest awesome-yara",
        "author": "InQuest contributors",
        "description": "Detects a credential theft tool leveraged by multiple APT groups.",
        "reference": "https://github.com/InQuest/awesome-yara",
        "tags": ["apt", "credential-dump", "mimikatz"],
        "rule": """
rule Scarlet_Mimikat_Credential_Dumper {
    meta:
        description = "Credential theft utilities related to Scarlet Mimikat"
        reference = "https://github.com/InQuest/awesome-yara"
    strings:
        $mz = { 4D 5A }
        $fn = "sekurlsa::logonpasswords" ascii wide
        $svc = "lsass.exe" ascii wide
    condition:
        $mz at 0 and all of ($fn,$svc)
}
""".strip(),
    },
    {
        "id": "yara-rules/crypto/Big_Numbers0",
        "name": "Big_Numbers0",
        "source": "Yara-Rules crypto",
        "author": "_pusher_",
        "description": "Detects 20-hex-length constants often used in crypto material",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/crypto",
        "tags": ["crypto", "constants"],
        "rule": """
rule Big_Numbers0
{
    meta:
        author = "_pusher_"
        description = "Looks for big numbers 20:sized"
        date = "2016-07"
    strings:
        $c0 = /[0-9a-fA-F]{20}/ fullword ascii
    condition:
        $c0
}
""".strip(),
    },
    {
        "id": "yara-rules/cve_rules/CVE-2017-11882",
        "name": "potential_CVE_2017_11882",
        "source": "Yara-Rules cve_rules",
        "author": "ReversingLabs",
        "description": "Detects Equation Editor exploit CVE-2017-11882",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/cve_rules",
        "tags": ["cve-2017-11882", "exploit", "office"],
        "rule": """
rule potential_CVE_2017_11882
{
    meta:
      author = "ReversingLabs"
      reference = "https://www.reversinglabs.com/newsroom/news/reversinglabs-yara-rule-detects-cobalt-strike-payload-exploiting-cve-2017-11882.html"
    strings:
        $docfilemagic = { D0 CF 11 E0 A1 B1 1A E1 }
        $equation1 = "Equation Native" wide ascii
        $equation2 = "Microsoft Equation 3.0" wide ascii
        $mshta = "mshta"
        $http  = "http://"
        $https = "https://"
        $cmd   = "cmd"
        $pwsh  = "powershell"
        $exe   = ".exe"
        $address = { 12 0C 43 00 }
    condition:
        $docfilemagic at 0 and any of ($mshta, $http, $https, $cmd, $pwsh, $exe) and any of ($equation1, $equation2) and $address
}
""".strip(),
    },
    {
        "id": "yara-rules/email/Email_Generic_Phishing",
        "name": "Email_Generic_Phishing",
        "source": "Yara-Rules email",
        "author": "Tyler <@InfoSecTyler>",
        "description": "Generic phishing email detector",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/email",
        "tags": ["email", "phishing"],
        "rule": """
rule Email_Generic_Phishing : email
{
  meta:
        Author = "Tyler <@InfoSecTyler>"
        Description ="Generic rule to identify phishing emails"
  strings:
    $eml_1="From:"
    $eml_2="To:"
    $eml_3="Subject:"
    $greeting_1="Hello sir/madam" nocase
    $greeting_2="Attention" nocase
    $greeting_3="Dear user" nocase
    $greeting_4="Account holder" nocase
    $url_1="Click" nocase
    $url_2="Confirm" nocase
    $url_3="Verify" nocase
    $url_4="Here" nocase
    $url_5="Now" nocase
    $url_6="Change password" nocase 
    $lie_1="Unauthorized" nocase
    $lie_2="Expired" nocase
    $lie_3="Deleted" nocase
    $lie_4="Suspended" nocase
    $lie_5="Revoked" nocase
    $lie_6="Unable" nocase
  condition:
    all of ($eml*) and
    any of ($greeting*) and
    any of ($url*) and
    any of ($lie*)
}
""".strip(),
    },
    {
        "id": "yara-rules/exploit_kits/AnglerEKredirector",
        "name": "AnglerEKredirector",
        "source": "Yara-Rules exploit_kits",
        "author": "adnan.shukor@gmail.com",
        "description": "Detects Angler exploit kit redirector",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/exploit_kits",
        "tags": ["exploit-kit", "angler"],
        "rule": """
rule AnglerEKredirector : EK
{
   meta:
      description = "Angler Exploit Kit Redirector"
      ref = "http://blog.xanda.org/2015/08/28/yara-rule-for-angler-ek-redirector-js/"
      author = "adnan.shukor@gmail.com"
      date = "08-July-2015"
      impact = "5"
      version = "1"
   strings:
      $ekr1 = "<script>var date = new Date(new Date().getTime() + 60*60*24*7*1000);" fullword
      $ekr2 = "document.cookie=\"PHP_SESSION_PHP="
      $ekr3 = "path=/; expires=\"+date.toUTCString();</script>" fullword
      $ekr4 = "<iframe src=" fullword
      $ekr5 = "</iframe></div>" fullword
   condition:
      all of them
}
""".strip(),
    },
    {
        "id": "yara-rules/maldocs/Maldoc_APT10_MenuPass",
        "name": "Maldoc_APT10_MenuPass",
        "source": "Yara-Rules maldocs",
        "author": "Colin Cowie",
        "description": "Detects APT10 MenuPass phishing documents",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/maldocs",
        "tags": ["maldoc", "apt10", "phishing"],
        "rule": """
import "hash"

rule Maldoc_APT10_MenuPass {
   meta:
      description = "Detects APT10 MenuPass Phishing"
      author = "Colin Cowie"
      reference = "https://www.fireeye.com/blog/threat-research/2018/09/apt10-targeting-japanese-corporations-using-updated-ttps.html"
      date = "2018-09-13"
   strings:
      $s1 = "C:\\\\ProgramData\\\\padre1.txt"
      $s2 = "C:\\\\ProgramData\\\\padre2.txt"
      $s3 = "C:\\\\ProgramData\\\\padre3.txt"
      $s5 = "C:\\\\ProgramData\\\\libcurl.txt"
      $s6 = "C:\\\\ProgramData\\\\3F2E3AB9"
   condition:
      any of them or
      hash.md5(0, filesize) == "4f83c01e8f7507d23c67ab085bf79e97" or
      hash.md5(0, filesize) == "f188936d2c8423cf064d6b8160769f21" or
      hash.md5(0, filesize) == "cca227f70a64e1e7fcf5bccdc6cc25dd"
}
""".strip(),
    },
    {
        "id": "yara-rules/malware/Emotets",
        "name": "Emotets",
        "source": "Yara-Rules malware",
        "author": "pekeinfo",
        "description": "Detects Emotet binaries",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/malware",
        "tags": ["malware", "emotet"],
        "rule": """
rule Emotets{
meta:
  author = "pekeinfo"
  date = "2017-10-18"
  description = "Emotets"
strings:
  $mz = { 4d 5a }
  $cmovnz={ 0f 45 fb 0f 45 de }
  $mov_esp_0={ C7 04 24 00 00 00 00 89 44 24 0? }
  $_eax={ 89 E? 8D ?? 24 ?? 89 ?? FF D0 83 EC 04 }
condition:
  ($mz at 0 and $_eax in( 0x2854..0x4000)) and ($cmovnz or $mov_esp_0)
}
""".strip(),
    },
    {
        "id": "yara-rules/packers/generic_javascript_obfuscation",
        "name": "generic_javascript_obfuscation",
        "source": "Yara-Rules packers",
        "author": "Josh Berry",
        "description": "Detects common JavaScript obfuscation patterns",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/packers",
        "tags": ["packer", "javascript", "obfuscation"],
        "rule": """
rule generic_javascript_obfuscation
{
meta:
    author = "Josh Berry"
    date = "2016-06-26"
    description = "JavaScript Obfuscation Detection"
    sample_filetype = "js-html"
strings:
    $string0 = /eval\\(([\\s]+)?(unescape|atob)\\(/ nocase
    $string1 = /var([\\s]+)?([a-zA-Z_$])+([a-zA-Z0-9_$]+)?([\\s]+)?=([\\s]+)?\\[([\\s]+)?\\"\\\\x[0-9a-fA-F]+/ nocase
    $string2 = /var([\\s]+)?([a-zA-Z_$])+([a-zA-Z0-9_$]+)?([\\s]+)?=([\\s]+)?eval;/
condition:
    any of them
}
""".strip(),
    },
    {
        "id": "yara-rules/utils/contains_base64",
        "name": "contains_base64",
        "source": "Yara-Rules utils",
        "author": "Jaume Martin",
        "description": "Detects presence of base64 blobs",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/utils",
        "tags": ["base64", "utils"],
        "rule": """
rule contains_base64 : Base64
{
    meta:
        author = "Jaume Martin"
        description = "This rule finds for base64 strings"
        version = "0.2"
        notes = "https://github.com/Yara-Rules/rules/issues/153"
    strings:
        $a = /([A-Za-z0-9+\\/]{4}){3,}([A-Za-z0-9+\\/]{2}==|[A-Za-z0-9+\\/]{3}=)?/
    condition:
        $a
}
""".strip(),
    },
    {
        "id": "yara-rules/webshells/webshell_ChinaChopper_aspx",
        "name": "webshell_ChinaChopper_aspx",
        "source": "Yara-Rules webshells",
        "author": "Ryan Boyle",
        "description": "Detects China Chopper ASPX webshell",
        "reference": "https://github.com/Yara-Rules/rules/tree/master/webshells",
        "tags": ["webshell", "china-chopper"],
        "rule": """
rule webshell_ChinaChopper_aspx
{
  meta:
    author      = "Ryan Boyle randomrhythm@rhythmengineering.com"
    date        = "2020/10/28"
    description = "Detect China Chopper ASPX webshell"
    reference1  = "https://www.fireeye.com/blog/threat-research/2013/08/breaking-down-the-china-chopper-web-shell-part-i.html"
    filetype    = "aspx"
  strings:
    $ChinaChopperASPX = {25 40 20 50 61 67 65 20 4C 61 6E 67 75 61 67 65 3D ?? 4A 73 63 72 69 70 74 ?? 25 3E 3C 25 65 76 61 6C 28 52 65 71 75 65 73 74 2E 49 74 65 6D 5B [1-100] 75 6E 73 61 66 65}
  condition:
    $ChinaChopperASPX
}
""".strip(),
    },
]

