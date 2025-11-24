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
]

