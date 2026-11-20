# xfreerdp3 /v:IP /u:Administrator /sec:rdp /bpp:16 /cert:ignore
# xfreerdp3 /v:IP /u:Administrator /sec:rdp /tls:seclevel:0 /cert:ignore
# xfreerdp3 /v:IP /u:Administrator /tls:seclevel:0 /cert:ignore
# xfreerdp3 /v:IP /u:Administrator /sec:nla /dynamic-resolution +clipboard /cert:tofu

#/v is ip, /u is username, /p is passwd

import subprocess

print("Server Addr. (FQDN/IPv4/IPv6)")
srv_addr = input()
subprocess.run([clear])

print("User Name\n")
usr_name = input()
print("Password\n")
usr_passwd = input
subprocess.run([clear])

print("""Security Level
(R) RDP Layer
(T) TLS Security
(N) NLA / Network Level Authentication (CredSSP)
[Not Support In Script](E) EXT / Extended NLA
[Not Support In Script](A) AAD / Entra ID / Azure AD""")
sec_lv = input().upper()

if sec_lv == "R":
    sec_lv = "rdp"
elif sec_lv == "T":
    tls_min = input("Min. TLS Version: ")
    tls_max = input("Max. TLS Version: ")
    sec_lv = "tls"
elif sec_lv == "N":
    sec_lv = "nla"

#WIP