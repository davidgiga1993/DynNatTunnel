# DynNatTunnel
Dynamic target NAT tunneling using socat.

This python utility uses socat to tunnel tcp/udp ports from one host to another.
It supports ipv4/6 and was designed to tunnel from ipv4 to ipv6, but other combinations are possible as well.

It supports changing DNS entries (for example dyndns) and will automatically re-start the tunnel with the correct target ip.


## Usage
Edit the sample `config.json`

```json
{
  "dest": "my-ipv6-home-address.com",
  "forward": [
	{
	  "prot": "tcp",
	  "src": {
		"stack": 4,
		"port": 32400
	  },
	  "dst": {
		"stack": 6,
		"port": 32400
	  }
	}
  ]
}
```

| Param | Description |
| --- | --- |
| prot | Protocol, can be tcp or udp |
| dest | Destination host where the packets should be tunneled to |
| forward | The src/dest ports which should be tunneled |
| stack | 4 or 6 depending if the src/target is ipv4 or 6 |
| port | The source / destionation port |


Run 
`python3 tunnel.py`


## Disclaimer
This utility was developed for my own personal needs. Feel free to make changes.
