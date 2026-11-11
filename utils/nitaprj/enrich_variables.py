import argparse
import ipaddress
from pathlib import Path

import yaml


def load_mapping(path):
    with path.open(encoding="utf-8") as source:
        value = yaml.safe_load(source)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def primary_loopback(payload):
    addresses = []
    for interface in payload.get("interfaces", {}).get("interface", []):
        if interface.get("name") != "lo0":
            continue
        for unit in interface.get("unit", []):
            if str(unit.get("name")) == "0":
                addresses.extend(
                    address["name"]
                    for address in unit.get("family", {}).get("inet", {}).get("address", [])
                )
    if len(addresses) > 1:
        raise ValueError("Multiple IPv4 addresses on lo0.0; set loopback_ip explicitly")
    if not addresses:
        return None
    address = ipaddress.ip_interface(addresses[0])
    if address.version != 4:
        raise ValueError("Expected an IPv4 address on lo0.0")
    return str(address.ip)


def management_interface(payload, interface_name):
    addresses = []
    for interface in payload.get("interfaces", {}).get("interface", []):
        if interface.get("name") != interface_name:
            continue
        for unit in interface.get("unit", []):
            if str(unit.get("name")) == "0":
                addresses.extend(
                    address["name"]
                    for address in unit.get("family", {}).get("inet", {}).get("address", [])
                )
    if not addresses:
        return None
    if len(addresses) != 1:
        raise ValueError(f"Expected exactly one IPv4 address on {interface_name}.0")
    if not isinstance(addresses[0], str) or "/" not in addresses[0]:
        raise ValueError(f"Expected an IPv4 CIDR address on {interface_name}.0")
    address = ipaddress.ip_interface(addresses[0])
    if address.version != 4:
        raise ValueError(f"Expected an IPv4 address on {interface_name}.0")
    return {"int": interface_name, "ip": str(address.ip), "mask": address.network.prefixlen}


def enrich_variables(project):
    metadata_path = project / "variable_metadata.yaml"
    metadata = load_mapping(metadata_path) if metadata_path.exists() else None
    shared_path = project / "group_vars" / "all.yaml"
    shared = load_mapping(shared_path)
    updates = []
    if metadata is not None:
        connection = metadata["connection"]
        required = {"netconf_user", "netconf_passwd", "netconf_port"}
        if set(connection) != required:
            raise ValueError(f"connection must contain exactly {sorted(required)}")
        port = connection["netconf_port"]
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("netconf_port must be an integer between 1 and 65535")
        if not all(isinstance(connection[key], str) for key in ("netconf_user", "netconf_passwd")):
            raise ValueError("netconf_user and netconf_passwd must be strings")
        updates.append((shared_path, {**shared, **connection}))

    host_paths = sorted(
        path for path in (project / "host_vars").iterdir()
        if path.is_file() and path.suffix in {".yaml", ".yml"}
    )
    for path in host_paths:
        host = load_mapping(path)
        host_metadata = metadata["hosts"].get(path.stem, {}) if metadata is not None else {}
        summary = {}
        if metadata is not None:
            summary = {
                "OS_version": host_metadata.get("OS_version") or host.get("version") or shared.get("version"),
                "leaf_type": host_metadata.get("leaf_type"),
                "loopback_ip": host_metadata.get("loopback_ip") or primary_loopback(host) or primary_loopback(shared),
            }
            if any(value is None or value == "" for value in summary.values()):
                raise ValueError(f"Missing host summary values for {path.stem}: {summary}")
        try:
            interface_name = host_metadata.get("management_interface", {}).get("int", "em0")
            if not isinstance(interface_name, str) or not interface_name:
                raise ValueError("management_interface.int must be a nonempty string")
            management = management_interface(host, interface_name)
            if management is None:
                management = management_interface(shared, interface_name)
            if management is None:
                raise ValueError(f"Missing IPv4 management address on {interface_name}.0")
        except ValueError as error:
            raise ValueError(f"{path.stem}: {error}") from error
        summary["management_interface"] = management
        updates.append((path, {**host, **summary}))

    for path, payload in updates:
        if payload != load_mapping(path):
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Restore project metadata after JTAF variable generation")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        enrich_variables(args.project)
    except (KeyError, ValueError, OSError, yaml.YAMLError) as error:
        parser.exit(1, f"Variable enrichment failed: {error}\n")


if __name__ == "__main__":
    main()