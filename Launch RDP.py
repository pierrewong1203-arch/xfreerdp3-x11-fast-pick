import getpass
import shutil
import subprocess
import sys


def clear_screen():
  subprocess.run(["clear"])


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


def main():
  # Auto-detect FreeRDP 3 vs FreeRDP 2 binary
  binary = "xfreerdp3" if shutil.which("xfreerdp3") else "xfreerdp"
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
(R) RDP Layer (Standard RDP - Win2k / Server 2003)
(T) TLS Security (SSL/TLS - Server 2003 R2 / 2008 R2 / 2028)
(N) NLA / Network Level Authentication (CredSSP - Server 2008 R2 / 2028)
(E) EXT / Extended NLA (Server 2012+)
[Not Supported In Script] (A) AAD / Entra ID / Azure AD""")
  sec_choice = ask("Choice [R/T/N/E]", "N").upper()

  if sec_choice == "R":
    cmd.append("/sec:rdp")
  elif sec_choice in ("T", "N", "E"):
    sec_map = {"T": "tls", "N": "nla", "E": "ext"}
    cmd.append(f"/sec:{sec_map[sec_choice]}")

    print("\nTLS Protocol Bounds (Supported: 1.0, 1.1, 1.2, 1.3)")
    print("  - Server 2003 R2: 1.0")
    print("  - Server 2008 R2: 1.0 (unpatched) to 1.2 (patched)")
    print("  - Server 2028   : 1.2 to 1.3")
    tls_min = ask("Min. TLS Version", "1.0")
    tls_max = ask("Max. TLS Version", "1.3")

    default_seclevel = "0" if tls_min in ("1.0", "1.1") else "2"
    tls_seclevel = ask(
        "OpenSSL TLS Security Level (0=Legacy 1.0/1.1, 1=Medium, 2=Modern)",
        default_seclevel,
    )

    if binary == "xfreerdp3":
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
(I) Ignore  (/cert:ignore) - Bypass all cert errors (Best for Win2k / 2003 / 2008 R2)
(T) TOFU    (/cert:tofu)   - Trust-On-First-Use (Best for Server 2028 / Modern)
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
(F) Fixed Resolution (Required for Win2k & Server 2003 R2)
(D) Dynamic Resolution (Resizes with window - Server 2008 R2+)
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

  bpp = ask("Color Depth / BPP (16 for Win2k, 24, 32)", "32")
  cmd.append(f"/bpp:{bpp}")

  scale = ask("Desktop Scaling % (100, 125, 150, 200)", "100")
  if scale != "100":
    cmd.append(f"/scale:{scale}")

  if ask_bool("Enable Modern Graphics Pipeline / AVC (/gfx)?", False):
    cmd.append("/gfx")
  if ask_bool("Enable Font Smoothing / ClearType (+fonts)?", True):
    cmd.append("+fonts")
  if ask_bool("Enable Desktop Composition / Aero (+aero)?", False):
    cmd.append("+aero")
  if ask_bool("Show Wallpaper (+wallpaper)?", False):
    cmd.append("+wallpaper")

  # 6. Clipboard & Connection Behavior
  clear_screen()
  print("""=== 6. CLIPBOARD & CONNECTION BEHAVIOR ===
Clipboard Support Notes:
  - Windows NT 3.1   : Not supported (No native RDP)
  - Windows 2000     : Text & images ONLY (No file copy-paste)
  - Server 2003 R2+  : Full support (Text, images, and file copy-paste)""")
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

  # 7. Review & Execute
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
