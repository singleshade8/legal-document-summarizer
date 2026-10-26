"""One-time setup for OFFLINE translation (no rate limits, no internet needed during your demo).

    pip install argostranslate "networkx==3.3"
    python install_offline_translation.py

Downloads the Argos Translate language packs for English <-> Hindi and English <-> Tamil
(~100 MB each, needs internet only now). Hindi <-> Tamil works automatically through English.
If a pack is not offered in your Argos index the script says so and carries on.
"""
import sys

try:
    import argostranslate.package as pkg
except ImportError:
    sys.exit("Please run:  pip install argostranslate   and then re-run this script.")

PAIRS = [("en", "hi"), ("hi", "en"), ("en", "ta"), ("ta", "en")]

pkg.update_package_index()
available = pkg.get_available_packages()
for src, tgt in PAIRS:
    match = next((p for p in available if p.from_code == src and p.to_code == tgt), None)
    if not match:
        print(f"[skip] no Argos pack for {src} -> {tgt}")
        continue
    print(f"[install] {src} -> {tgt} ...")
    try:
        pkg.install_from_path(match.download())
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"\nInstall failed: {type(exc).__name__}: {exc}\n"
                 "If the error mentions networkx / stanza / 'nx-loopback', run:\n"
                 "    pip install \"networkx==3.3\"\n"
                 "and run this script again. (The app itself works without offline translation.)")
print("Done. Restart the app; the Output language dropdown now works offline for the installed pairs.")
