import getpass
import os
import shutil
import subprocess
import sys


def clear_screen():
  os.system("cls" if os.name == "nt" else "clear")


def ask(prompt, default=None):
  suffix = f" [{default}]" if default is not None else ""
  val = input(f"{prompt}{suffix}: ").strip()
  return val if val else default


def ask_bool(prompt, default=True):
  hint = "Y/n" if default else "y/N"
  val = input(f"{prompt} ({hint}): ").strip().lower()
  if not val:
    return default
  return val in ("y", "yes", "1", "true")


PRESETS = {
    "windows": {
        "1": {
            "name": "Windows NT 3.1 / 3.5 / 3.51 Workstation (No RDP)",
            "supported": False,
            "note": (
                "No native RDP server exists in NT 3.x. Use a guest VNC server"
                " or VM console."
            ),
        },
        "2": {
            "name": "Windows NT 4.0 Workstation (No native RDP)",
            "supported": False,
            "note": (
                "Standard NT 4.0 Workstation lacks RDP (only NT 4.0 Terminal"
                " Server Edition had RDP)."
            ),
        },
        "3": {
            "name": "Windows 2000 Professional",
            "supported": True,
            "note": (
                "RDP 5.0: Standard RDP RC4 encryption (/sec:rdp), max 16-bit"
                " color, text-only clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:16",
                "/size:1024x768",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "4": {
            "name": "Windows XP Professional (RTM / SP1 / SP2)",
            "supported": True,
            "note": (
                "RDP 5.1: Standard RDP security (/sec:rdp), 24-bit color, full"
                " file & text clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:24",
                "/size:1280x800",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "5": {
            "name": "Windows XP Professional SP3 (Standard RDP)",
            "supported": True,
            "note": (
                "RDP 6.1: Standard RDP security (/sec:rdp), 24-bit color, full"
                " clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:24",
                "/size:1280x800",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "6": {
            "name": "Windows XP Professional SP3 (CredSSP / NLA Enabled)",
            "supported": True,
            "note": (
                "RDP 6.1: NLA over TLS 1.0 (requires registry CredSSP enabled"
                " on XP SP3 + seclevel:0)."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.0",
                "/tls:seclevel:0",
                "/bpp:24",
                "/size:1280x800",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "7": {
            "name": "Windows Vista (No Aero / Basic Theme)",
            "supported": True,
            "note": (
                "RDP 6.0: NLA over TLS 1.0 (seclevel:0), Desktop Composition"
                " disabled."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.0",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "8": {
            "name": "Windows Vista (Have Aero / Glass Enabled)",
            "supported": True,
            "note": (
                "RDP 6.0: NLA over TLS 1.0 (seclevel:0), Desktop Composition"
                " enabled (+aero)."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.0",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+aero",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "9": {
            "name": "Windows 7 (No Aero / Basic Theme)",
            "supported": True,
            "note": "RDP 7.1: NLA over TLS 1.0-1.2 (seclevel:0), Aero disabled.",
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "10": {
            "name": "Windows 7 (Have Aero / Glass Enabled)",
            "supported": True,
            "note": (
                "RDP 7.1: NLA over TLS 1.0-1.2 (seclevel:0), Aero enabled"
                " (+aero)."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+aero",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "11": {
            "name": "Windows 8 / 8.1 Pro & Enterprise",
            "supported": True,
            "note": (
                "RDP 8.0/8.1: Extended NLA (/sec:ext) over TLS 1.2 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.2",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "12": {
            "name": "Windows 10 (1507 - 22H2)",
            "supported": True,
            "note": (
                "RDP 10.x: Extended NLA (/sec:ext) over TLS 1.2 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.2",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "13": {
            "name": "Windows 11 (21H2 - 24H2+)",
            "supported": True,
            "note": (
                "RDP 10.x+: Extended NLA (/sec:ext) over TLS 1.2-1.3 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.3",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
    },
    "windows_server": {
        "1": {
            "name": "Windows NT 3.1 / 3.5 / 3.51 Advanced Server (No RDP)",
            "supported": False,
            "note": (
                "No native RDP server exists in NT 3.x Server. Use VNC or"
                " hypervisor console."
            ),
        },
        "2": {
            "name": "Windows NT 4.0 Server (Standard / Enterprise - No RDP)",
            "supported": False,
            "note": (
                "Regular NT 4.0 Server lacks RDP; only NT 4.0 Terminal Server"
                " Edition includes RDP."
            ),
        },
        "3": {
            "name": "Windows NT 4.0 Server Terminal Server Edition (TSE)",
            "supported": True,
            "note": (
                "RDP 4.0: Legacy RC4 encryption (/sec:rdp), 16-bit color,"
                " text-only clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:16",
                "/size:1024x768",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "4": {
            "name": "Windows 2000 Server / Advanced Server / Datacenter",
            "supported": True,
            "note": (
                "RDP 5.0: Standard RDP RC4 encryption (/sec:rdp), 16-bit color,"
                " text-only clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:16",
                "/size:1024x768",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "5": {
            "name": "Windows Server 2003 / 2003 R2 / SBS 2003 (Standard RDP)",
            "supported": True,
            "note": (
                "RDP 5.2: Default non-TLS layer (/sec:rdp), fixed resolution,"
                " full file & text clipboard."
            ),
            "flags": [
                "/sec:rdp",
                "/bpp:24",
                "/size:1280x800",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "6": {
            "name": "Windows Server 2003 / 2003 R2 / SBS 2003 (TLS 1.0 Layer)",
            "supported": True,
            "note": (
                "RDP 5.2: SSL/TLS layer (/sec:tls) pinned to TLS 1.0 with"
                " seclevel:0, full clipboard."
            ),
            "flags": [
                "/sec:tls",
                "/tls:min-version:1.0",
                "/tls:max-version:1.0",
                "/tls:seclevel:0",
                "/bpp:24",
                "/size:1280x800",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "7": {
            "name": "Windows Server 2008 / SBS 2008 (No Aero / Classic Theme)",
            "supported": True,
            "note": (
                "RDP 6.1: NLA over TLS 1.0-1.2 (seclevel:0), Desktop"
                " Composition disabled."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "8": {
            "name": (
                "Windows Server 2008 / SBS 2008 (Have Aero / Desktop"
                " Experience)"
            ),
            "supported": True,
            "note": (
                "RDP 6.1: NLA over TLS 1.0-1.2 (seclevel:0), Desktop"
                " Composition enabled (+aero)."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+aero",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "9": {
            "name": (
                "Windows Server 2008 R2 / SBS 2011 (No Aero / Classic Theme)"
            ),
            "supported": True,
            "note": (
                "RDP 7.1: NLA over TLS 1.0-1.2 (seclevel:0 for unpatched"
                " hosts), Aero disabled."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "10": {
            "name": (
                "Windows Server 2008 R2 / SBS 2011 (Have Aero / Desktop"
                " Experience)"
            ),
            "supported": True,
            "note": (
                "RDP 7.1: NLA over TLS 1.0-1.2 (seclevel:0 for unpatched"
                " hosts), Aero enabled (+aero)."
            ),
            "flags": [
                "/sec:nla",
                "/tls:min-version:1.0",
                "/tls:max-version:1.2",
                "/tls:seclevel:0",
                "/bpp:32",
                "/dynamic-resolution",
                "+aero",
                "+fonts",
                "+clipboard",
                "/cert:ignore",
            ],
        },
        "11": {
            "name": "Windows Server 2012 / 2012 R2 / Essentials",
            "supported": True,
            "note": (
                "RDP 8.0/8.1: Extended NLA (/sec:ext) over TLS 1.2 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.2",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "12": {
            "name": "Windows Server 2016",
            "supported": True,
            "note": (
                "RDP 10.0: Extended NLA (/sec:ext) over TLS 1.2 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.2",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "13": {
            "name": "Windows Server 2019",
            "supported": True,
            "note": (
                "RDP 10.6: Extended NLA (/sec:ext) over TLS 1.2 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.2",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "14": {
            "name": "Windows Server 2022",
            "supported": True,
            "note": (
                "RDP 10.x: Extended NLA (/sec:ext) over TLS 1.2-1.3 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.3",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
        "15": {
            "name": "Windows Server 2025",
            "supported": True,
            "note": (
                "RDP 10.x+: Extended NLA (/sec:ext) over TLS 1.2-1.3 with /gfx"
                " pipeline."
            ),
            "flags": [
                "/sec:ext",
                "/tls:min-version:1.2",
                "/tls:max-version:1.3",
                "/tls:seclevel:2",
                "/bpp:32",
                "/dynamic-resolution",
                "/gfx",
                "+fonts",
                "+clipboard",
                "/cert:tofu",
            ],
        },
    },
}


def adapt_flags_for_binary(flags, binary):
  """Converts FreeRDP 3 flags to FreeRDP 2 syntax if xfreerdp3 is not installed."""
  if "xfreerdp3" in binary:
    return flags
  adapted = []
  for f in flags:
    if f.startswith("/tls:min-version:") or f.startswith("/tls:max-version:"):
      continue
    elif f.startswith("/tls:seclevel:"):
      lvl = f.split(":")[-1]
      adapted.append(f"/tls-seclevel:{lvl}")
    else:
      adapted.append(f)
  return adapted


def run_preset_mode(binary):
  clear_screen()
  print("""=== PRESET MODE: CHOOSE OS TYPE ===
(1) Windows (Client / Workstation Editions)
(2) Windows Server (All Server Editions)""")
  type_choice = ask("Choice [1/2]", "2")
  if type_choice == "1":
    category = "windows"
    title = "WINDOWS (CLIENT EDITIONS)"
  elif type_choice == "2":
    category = "windows_server"
    title = "WINDOWS SERVER (ALL SERVER EDITIONS)"
  else:
    print("Invalid OS type choice.")
    sys.exit(1)

  clear_screen()
  print(f"=== {title} ===")
  for key, item in PRESETS[category].items():
    print(f"({key.rjust(2)}) {item['name']}")

  ver_choice = ask("\nSelect Version Number")
  selected = PRESETS[category].get(ver_choice)
  if not selected:
    print("Invalid version selection.")
    sys.exit(1)

  clear_screen()
  print(f"Selected: {selected['name']}")
  print(f"Details : {selected['note']}\n")
  if not selected["supported"]:
    print("Cannot launch xfreerdp for this OS version.")
    sys.exit(0)

  # Target & Authentication Prompts
  srv_addr = ask("Server Addr. (FQDN/IPv4/IPv6)")
  if not srv_addr:
    print("Server address is required.")
    sys.exit(1)
  srv_port = ask("Port", "3389")
  domain = ask("Domain (leave blank for local account)", "")
  usr_name = ask("User Name", "Administrator")
  usr_passwd = getpass.getpass("Password (leave blank to prompt later): ")

  cmd = [binary, f"/v:{srv_addr}:{srv_port}"]
  if domain:
    cmd.append(f"/d:{domain}")
  if usr_name:
    cmd.append(f"/u:{usr_name}")
  if usr_passwd:
    cmd.append(f"/p:{usr_passwd}")

  if category == "windows_server" and ask_bool(
      "Connect to Admin / Console Session (/admin)?", False
  ):
    cmd.append("/admin")

  # Append preset flags (adapted for v2 or v3)
  cmd.extend(adapt_flags_for_binary(selected["flags"], binary))

  extra_flags = ask(
      "Any extra raw xfreerdp flags to append/override (optional)", ""
  )
  if extra_flags:
    cmd.extend(extra_flags.split())

  return cmd


def run_manual_mode(binary):
  cmd = [binary]

  # 1. Target & Gateway
  clear_screen()
  print("=== 1. TARGET SERVER & GATEWAY ===")
  srv_addr = ask("Server Addr. (FQDN/IPv4/IPv6)")
  if not srv_addr:
    print("Server address is required.")
    sys.exit(1)
  srv_port = ask("Port", "3389")
  cmd.append(f"/v:{srv_addr}:{srv_port}")

  if ask_bool("Use RD Gateway?", False):
    gw_host = ask("Gateway Hostname/IP")
    gw_port = ask("Gateway Port", "443")
    gw_user = ask("Gateway Username (leave blank to reuse RDP user)", "")
    cmd.append(f"/g:{gw_host}:{gw_port}")
    if gw_user:
      gw_pass = getpass.getpass("Gateway Password: ")
      cmd.extend([f"/gu:{gw_user}", f"/gp:{gw_pass}"])

  # 2. Authentication & Session
  clear_screen()
  print("=== 2. AUTHENTICATION & SESSION ===")
  domain = ask("Domain (leave blank for local account)", "")
  usr_name = ask("User Name", "Administrator")
  usr_passwd = getpass.getpass("Password (leave blank to prompt later): ")
  if domain:
    cmd.append(f"/d:{domain}")
  if usr_name:
    cmd.append(f"/u:{usr_name}")
  if usr_passwd:
    cmd.append(f"/p:{usr_passwd}")
  if ask_bool("Connect to Admin / Console Session (/admin)?", False):
    cmd.append("/admin")
  if ask_bool("Enable Restricted Admin Mode (/restricted-admin)?", False):
    cmd.append("/restricted-admin")

  # 3. Security & TLS Layer
  clear_screen()
  print("""=== 3. SECURITY & TLS LAYER ===
(R) RDP Layer (Standard RDP - NT4 / Win2k / XP / Server 2003)
(T) TLS Security (SSL/TLS - Server 2003 R2 / 2008 R2)
(N) NLA / Network Level Authentication (CredSSP - Vista+ / Server 2008+)
(E) EXT / Extended NLA (Win8+ / Server 2012+)""")
  sec_choice = ask("Choice [R/T/N/E]", "N").upper()
  if sec_choice == "R":
    cmd.append("/sec:rdp")
  elif sec_choice in ("T", "N", "E"):
    sec_map = {"T": "tls", "N": "nla", "E": "ext"}
    cmd.append(f"/sec:{sec_map[sec_choice]}")
    print("\nTLS Protocol Bounds (Supported: 1.0, 1.1, 1.2, 1.3)")
    print("  - Server 2003 R2        : 1.0")
    print("  - Vista / 7 / 2008 (R2) : 1.0 (unpatched) to 1.2 (patched)")
    print("  - Win11 / Server 2025   : 1.2 to 1.3")
    tls_min = ask("Min. TLS Version", "1.0")
    tls_max = ask("Max. TLS Version", "1.3")
    default_seclevel = "0" if tls_min in ("1.0", "1.1") else "2"
    tls_seclevel = ask(
        "OpenSSL TLS Security Level (0=Legacy 1.0/1.1, 1=Medium, 2=Modern)",
        default_seclevel,
    )
    if "xfreerdp3" in binary:
      cmd.extend([
          f"/tls:min-version:{tls_min}",
          f"/tls:max-version:{tls_max}",
          f"/tls:seclevel:{tls_seclevel}",
      ])
    else:
      cmd.append(f"/tls-seclevel:{tls_seclevel}")
  else:
    print("Invalid or unsupported security level selected.")
    sys.exit(1)

  # 4. Certificate Verification Options
  clear_screen()
  print("""=== 4. CERTIFICATE OPTIONS ===
(I) Ignore  (/cert:ignore) - Bypass all cert errors (Best for legacy OS)
(T) TOFU    (/cert:tofu)   - Trust-On-First-Use (Best for Win10/11 & Server 2012-2025)
(D) Deny    (/cert:deny)   - Strict validation (Fails on self-signed/expired certs)""")
  cert_choice = ask("Choice [I/T/D]", "I").upper()
  cert_map = {"I": "/cert:ignore", "T": "/cert:tofu", "D": "/cert:deny"}
  cmd.append(cert_map.get(cert_choice, "/cert:ignore"))
  cert_name = ask(
      "Override Expected Certificate CN/Hostname (optional, /cert:name:...)", ""
  )
  if cert_name:
    cmd.append(f"/cert:name:{cert_name}")

  # 5. Display & Graphics
  clear_screen()
  print("""=== 5. DISPLAY & GRAPHICS ===
Window Size Mode:
(F) Fixed Resolution (Required for NT4 / Win2k / XP / Server 2003)
(D) Dynamic Resolution (Resizes with window - Vista+ / Server 2008+)
(S) Fullscreen (/f)
(M) Multi-Monitor Fullscreen (/multimon)""")
  win_mode = ask("Choice [F/D/S/M]", "D").upper()
  if win_mode == "F":
    res = ask("Resolution (WIDTHxHEIGHT)", "1024x768")
    cmd.append(f"/size:{res}")
  elif win_mode == "D":
    cmd.append("/dynamic-resolution")
  elif win_mode == "S":
    cmd.append("/f")
  elif win_mode == "M":
    cmd.append("/multimon")

  bpp = ask(
      "Color Depth / BPP (16 for Win2k, 24 for XP/2003, 32 for Vista+)", "32"
  )
  cmd.append(f"/bpp:{bpp}")

  scale = ask("Desktop Scaling % (100, 125, 150, 200)", "100")
  if scale != "100":
    cmd.append(f"/scale:{scale}")

  if ask_bool(
      "Enable Modern Graphics Pipeline / AVC (/gfx - Win8+/2012+)?", False
  ):
    cmd.append("/gfx")
  if ask_bool("Enable Font Smoothing / ClearType (+fonts)?", True):
    cmd.append("+fonts")
  if ask_bool(
      "Enable Desktop Composition / Aero (+aero - Vista/7/2008/2008R2)?", False
  ):
    cmd.append("+aero")
  if ask_bool("Show Wallpaper (+wallpaper)?", False):
    cmd.append("+wallpaper")

  # 6. Clipboard & Connection Behavior
  clear_screen()
  print("""=== 6. CLIPBOARD & CONNECTION BEHAVIOR ===
Clipboard Support Notes:
- Windows NT 3.1         : Not supported (No native RDP)
- NT 4.0 TSE / Win2k     : Text & images ONLY (No file copy-paste)
- XP / Server 2003 R2+   : Full support (Text, images, and file copy-paste)""")
  if ask_bool("Enable Clipboard Pass-through (+clipboard)?", True):
    cmd.append("+clipboard")
  else:
    cmd.append("-clipboard")

  net_type = ask(
      "Network Hint (modem, broadband, lan, auto - blank to skip)", ""
  )
  if net_type:
    cmd.append(f"/network:{net_type}")

  if ask_bool("Enable Auto-Reconnect (+auto-reconnect)?", True):
    cmd.append("+auto-reconnect")

  extra_flags = ask("Any extra raw xfreerdp flags (optional)", "")
  if extra_flags:
    cmd.extend(extra_flags.split())

  return cmd


def main():
  binary = shutil.which("xfreerdp3") or shutil.which("xfreerdp")
  if not binary:
    print(
        "Error: Neither 'xfreerdp3' nor 'xfreerdp' was found in your system"
        " PATH."
    )
    sys.exit(1)

  clear_screen()
  print(f"""=== XFREERDP LAUNCHER ({os.path.basename(binary)}) ===
Select Mode:
(M) Manual Mode (Configure every parameter step-by-step)
(P) Preset Mode (Choose Windows or Windows Server -> Select exact version)""")
  mode = ask("Choice [M/P]", "P").upper()
  if mode == "M":
    cmd = run_manual_mode(binary)
  elif mode == "P":
    cmd = run_preset_mode(binary)
  else:
    print("Invalid mode selection.")
    sys.exit(1)

  # Review & Execute
  clear_screen()
  preview = [
      arg
      if not (arg.startswith("/p:") or arg.startswith("/gp:"))
      else f"{arg.split(':')[0]}:********"
      for arg in cmd
  ]
  print("=== EXECUTING COMMAND ===")
  print(" ".join(preview))
  print("=" * 25 + "\n")
  subprocess.run(cmd)


if __name__ == "__main__":
  main()