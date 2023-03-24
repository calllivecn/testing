#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-24 01:12:36
# author calllivecn <c-all@qq.com>

#import re


class WireGuardConfig:
    def __init__(self, config):
        self.config = config
        self.interfaces = []
        self.parse_config()

    def parse_config(self):
        # interface_re = re.compile(r'\[Interface\]\nPrivateKey = (\S+)\nAddress = (\S+)(?:\nDNS = (\S+))?')
        # peer_re = re.compile(r'\[Peer\]\nPublicKey = (\S+)\nAllowedIPs = (\S+)(?:\nEndpoint = (\S+))?')
        current_interface = None
        for line in self.config.split('\n'):
            if line.startswith('#') or line == "":
                continue
            if line.startswith('[Interface]'):
                current_interface = {'private_key': None, 'address': None, 'dns': None, 'peers': []}
            elif line.startswith('[Peer]'):
                current_peer = {'public_key': None, 'allowed_ips': None, 'endpoint': None}
                current_interface['peers'].append(current_peer)
            elif line.startswith('PrivateKey = '):
                current_interface['private_key'] = line.split('PrivateKey = ')[1]
            elif line.startswith('Address = '):
                current_interface['address'] = line.split('Address = ')[1]
            elif line.startswith('DNS = '):
                current_interface['dns'] = line.split('DNS = ')[1]
            elif line.startswith('PublicKey = '):
                current_peer['public_key'] = line.split('PublicKey = ')[1]
            elif line.startswith('AllowedIPs = '):
                current_peer['allowed_ips'] = line.split('AllowedIPs = ')[1]
            elif line.startswith('Endpoint = '):
                current_peer['endpoint'] = line.split('Endpoint = ')[1]
            elif line.strip() == '':
                if current_interface is not None:
                    self.interfaces.append(current_interface)
                    current_interface = None
            elif current_interface is not None:
                if line.startswith('ListenPort = '):
                    current_interface['listen_port'] = line.split('ListenPort = ')[1]
                elif line.startswith('MTU = '):
                    current_interface['mtu'] = line.split('MTU = ')[1]
                elif line.startswith('PreUp = '):
                    current_interface['pre_up'] = line.split('PreUp = ')[1]
                elif line.startswith('PostUp = '):
                    current_interface['post_up'] = line.split('PostUp = ')[1]
                elif line.startswith('PreDown = '):
                    current_interface['pre_down'] = line.split('PreDown = ')[1]
                elif line.startswith('PostDown = '):
                    current_interface['post_down'] = line.split('PostDown = ')[1]
        if current_interface is not None:
            self.interfaces.append(current_interface)

    def __str__(self):
        return str(self.interfaces)



def test():
    import pprint

    with open('wg-ten.conf', 'r') as f:
        config = f.read()
	
    wg_config = WireGuardConfig(config)
    print("="*40)
    pprint.pprint(wg_config.interfaces, sort_dicts=False)

if __name__ == "__main__":
    test()
