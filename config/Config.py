from typing import Dict, List


class PortConfig:
    def __init__(self, data: Dict[str, any]):
        self.stack: int = data['stack']
        """
        IP stack (4 or 6)
        """

        self.port: int = data['port']
        """
        Port
        """


class ForwardConfig:
    """
    Single forward config
    """

    def __init__(self, data: Dict[str, any]):
        self.prot: str = data['prot']
        """
        Protocol (tcp or udp)
        """
        self.src = PortConfig(data['src'])
        self.dest = PortConfig(data['dest'])


class Config:
    def __init__(self, data: Dict[str, any]):
        self.dest_addr: str = data['dest']
        """
        Destination host 
        """

        self.forwarders: List[ForwardConfig] = [ForwardConfig(cfg) for cfg in data['forward']]
