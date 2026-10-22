"""Register a physical ESP32 and its controlled load in IREOS's existing DB.

Example:
  python register_physical_esp32.py --house-id HSE-XXXXXX

The generated device secret is displayed once; copy it into the private firmware
configuration, do not commit it, and treat it as a password.
"""

import argparse

import db_manager as db


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a physical IREOS ESP32 device")
    parser.add_argument("--house-id", required=True, help="Existing HSE-... ID from the registered account")
    parser.add_argument("--device-name", default="IREOS Physical ESP32")
    parser.add_argument("--appliance-name", default="IREOS Controlled Load")
    parser.add_argument("--appliance-type", default="generic")
    parser.add_argument("--rated-power-w", type=float, default=500.0)
    parser.add_argument("--mac-address", help="Optional ESP32 Wi-Fi MAC address")
    args = parser.parse_args()

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT house_id FROM houses WHERE house_id = ?;", (args.house_id,))
    house_exists = cursor.fetchone() is not None
    conn.close()
    if not house_exists:
        parser.error(f"House {args.house_id!r} does not exist in the configured database")

    device = db.create_device(
        args.house_id,
        "ESP32",
        args.device_name,
        mac_address=args.mac_address,
    )
    appliance = db.create_appliance(
        args.house_id,
        device["device_id"],
        args.appliance_name,
        args.appliance_type,
        args.rated_power_w,
    )

    print("IREOS physical ESP32 registered in the existing device/appliance tables.")
    print(f"House ID:       {args.house_id}")
    print(f"Device ID:      {device['device_id']}")
    print(f"Device secret:  {device['device_secret']}")
    print(f"Appliance ID:   {appliance['id']}")
    print("Copy the device ID, secret, appliance ID, and house ID into the marked firmware constants.")
    print("The secret is shown only at registration; store it securely and do not commit it.")


if __name__ == "__main__":
    main()
