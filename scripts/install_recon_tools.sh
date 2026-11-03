#!/bin/sh
# Installs the optional Go recon tools into a Debian-based image, from pinned release
# archives checked against pinned SHA-256 hashes. Docker runs this when RECON_TOOLS=true.
set -eu

arch=$(dpkg --print-architecture)
case "$arch" in
  amd64|arm64) ;;
  *) echo "No pinned recon tools for $arch" >&2; exit 1 ;;
esac

# tool version amd64-sha256 arm64-sha256
TOOLS="
nuclei 3.11.1 ea63d4ae232808cd7c6bc00d0142428e231fab59dae01042246097d195835ab6 8044e3d9768ba0a744b2872c1a87e813006f013da97ca9f50f7661a4203bec07
katana 1.8.0 cb027ae99d0757061b70c07a15c7a80f62c5a535ab52c4a329f80c4b0a7309d2 80e269210727a855511ffac8dfb01297b2344742acec71a35e8ba4a67a90f0f2
subfinder 2.17.0 a39c3e5c7a26ef3c430915c4d6cbf7716a00f26769a75e9405aba796142eba37 24913d49dddc1d3a5e99a4a7580da5be980959b9415b96f52c4f7f4124392190
naabu 2.7.0 0cc77c0ca32d2f519ffbaa7665bb0e7c88c40753ab22f03551d453a1a823e9f0 e88af9bbfd777e2ffab6f84696747ba74de98fafeda882c078d158a610dbd86e
tlsx 1.4.0 05628cec246e292e2f9afc6e7bc5de95aaa0fbe78fd556d5ad220b9f4702d364 b757125d94c7d0e1f1f109534f0ed88d2a4b1c3856e1fa35efc1ef9e36781b0e
"

# naabu links against libpcap and needs a raw socket, like nmap.
apt-get update
apt-get install -y --no-install-recommends libpcap0.8
rm -rf /var/lib/apt/lists/*

work=$(mktemp -d)
echo "$TOOLS" | while read -r tool version amd64 arm64; do
  [ -n "$tool" ] || continue
  if [ "$arch" = "amd64" ]; then sha=$amd64; else sha=$arm64; fi
  archive="${tool}_${version}_linux_${arch}.zip"
  curl -fsSL -o "$work/$archive" \
    "https://github.com/projectdiscovery/$tool/releases/download/v$version/$archive"
  echo "$sha  $work/$archive" | sha256sum -c -
  python -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extract(sys.argv[2], "/usr/local/bin")' \
    "$work/$archive" "$tool"
  chmod 0755 "/usr/local/bin/$tool"
  rm -f "$work/$archive"
done
rm -rf "$work"

setcap cap_net_raw+eip /usr/local/bin/naabu
