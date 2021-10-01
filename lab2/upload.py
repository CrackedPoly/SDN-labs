import json
import requests


def jsonfy_rule(protocol, vSwitch, in_port, out_ports: list):
    global type
    if protocol == "arp":
        type = 2054
    elif protocol == "ip":
        type = 2048

    rule = """
            {
                "flow": {
                    "id": "%s-stp-s%s-%s",
                    "priority": 200,
                    "table_id": 0,
                    "match": {
                        "in-port": "openflow:%s:%s",
                        "ethernet-match": {
                            "ethernet-type": {
                                "type": %s
                            }
                        }
                    },
                    "instructions": {
                        "instruction": [
                            {
                                "order": 0,
                                "apply-actions": {
                                    "action": [
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
	        """ \
           % (protocol, vSwitch, in_port, vSwitch, in_port, type)
    json_obj = json.loads(rule)
    for i in range(len(out_ports)):
        json_obj['flow']['instructions']['instruction'][0]['apply-actions']['action'].append(json.loads(
            """
                {
                    "order": %s,
                    "output-action": {
                        "output-node-connector": "openflow:%s:%s"
                    }
                }
            """ % (i, vSwitch, out_ports[int(i)])
        ))
    return json_obj


def put_flow(protocol, vSwitch, in_port, out_ports: list):
    rule = jsonfy_rule(protocol=protocol, vSwitch=vSwitch, in_port=in_port, out_ports=out_ports)
    url = f"http://172.16.86.1:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:{vSwitch}/table/0/flow/{protocol}-stp-s{vSwitch}-{in_port}"
    requests.put(auth=("admin", "admin"), json=rule, url=url)
