# Discord Token Checker

A high-performance asynchronous Discord token checker with payment method verification. Built with modern Python featuring TLS spoofing and proxy support.

## Features

- ⚡ **Asynchronous Processing**: Multi-threaded architecture for fast token checking
- 🔒 **TLS Spoofing**: Advanced browser fingerprint emulation
- 🌐 **Proxy Support**: Rotating proxy support with authentication
- 💳 **Payment Method Detection**: Identifies accounts with registered payment methods
- 🎨 **Colored Output**: Clear, color-coded console output for easy monitoring
- 📁 **Organized Results**: Automatic result saving with timestamp-based folders

## Showcase

![image](https://github.com/user-attachments/assets/6f055f8d-5aa5-4bcb-b972-18077853ffc2)


## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/discord-token-checker
cd discord-token-checker
```

2. Install required packages
```bash
pip install -r requirements.txt
```

## Required Dependencies

- tls-client
- aiofiles
- colorama

## Setup

1. Create `input.txt` with your tokens in one of these formats:
```
email:password:token
token
```

2. Create `proxies.txt` with your proxies in one of these formats:
```
ip:port
user:pass@ip:port
```

## Usage

Run the script with optional thread count:
```bash
python main.py --threads 5
```

### Command Line Arguments

- `--threads`: Number of concurrent checking threads (default: 5)

## Output Format

The script provides real-time color-coded console output:
- 🟢 Green: Valid tokens with payment methods
- 🔴 Red: Invalid tokens or those without payment methods

Results are saved in `output/timestamp/hits.txt` with detailed information about each valid account.

## Output Structure

```
output/
└── 2024-02-15 12-30-45/
    └── hits.txt
```

## Features in Detail

### Proxy Management
- Automatic proxy rotation
- Support for both authenticated and non-authenticated proxies
- Concurrent proxy usage

### Token Verification
- Account validity checking
- Payment method detection
- Username and ID extraction
- Billing information verification

### Result Management
- Automatic timestamp-based folder creation
- Detailed hit logging
- Organized output structure

## Notes

- This tool is for educational purposes only
- Use responsibly and in accordance with Discord's Terms of Service
- Proxies are required to avoid rate limiting

## Contributing

Feel free to submit issues and enhancement requests!

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and Discord's Terms of Service.
