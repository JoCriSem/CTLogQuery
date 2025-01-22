import requests
import json
import csv
import datetime

# Input and output file paths
INPUT_FILE = "domains.txt"
OUTPUT_FILE = "certificate_issuers.csv"

# Function to query crt.sh for certificates of a given domain
def query_certificates(domain):
    url = f"https://crt.sh/?q={domain}&output=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data for domain {domain}: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Error querying crt.sh for domain {domain}: {e}")
        return []

# Function to filter active certificates and extract details
def extract_active_cert_details(certificates):
    active_cert_details = []
    current_date = datetime.datetime.utcnow()
    for cert in certificates:
        if 'not_after' in cert:
            not_after = datetime.datetime.strptime(cert['not_after'], "%Y-%m-%dT%H:%M:%S")
            if not_after > current_date:  # Exclude expired certificates
                not_before = datetime.datetime.strptime(cert['not_before'], "%Y-%m-%dT%H:%M:%S") if 'not_before' in cert else None
                common_name = cert.get('common_name', '')
                identities = common_name + ", " + ", ".join(cert.get('name_value', '').split("\n"))
                active_cert_details.append({
                    "issuer": cert['issuer_name'],
                    "not_before": not_before,
                    "not_after": not_after,
                    "common_name": common_name,
                    "identities": identities
                })
    return active_cert_details

# Main script
if __name__ == "__main__":
    with open(INPUT_FILE, "r") as file:
        domains = [line.strip() for line in file.readlines()]

    results = []
    for domain in domains:
        print(f"Querying certificates for domain: {domain}")
        certificates = query_certificates(domain)
        active_cert_details = extract_active_cert_details(certificates)
        if active_cert_details:
            print(f"Found {len(active_cert_details)} active certificate(s) for domain: {domain}")
        else:
            print(f"No active certificates found for domain: {domain}")
        for cert_detail in active_cert_details:
            results.append({
                "domain": domain,
                "issuer": cert_detail['issuer'],
                "not_before": cert_detail['not_before'],
                "not_after": cert_detail['not_after'],
                "common_name": cert_detail['common_name'],
                "identities": cert_detail['identities']
            })

    # Write results to a CSV file
    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        fieldnames = ["domain", "issuer", "not_before", "not_after", "common_name", "identities"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {OUTPUT_FILE}")
