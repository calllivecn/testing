#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-23 17:09:01
# author calllivecn <calllivecn@outlook.com>

from ldap3 import Server, Connection, ALL, SUBTREE, ServerPool

LDAP_SERVER_POOL = ["192.168.0.30"]
LDAP_SERVER_PORT = 389
ADMIN_DN = "xu.zhang"
ADMIN_PASSWORD = "zx4@1597530.x"
SEARCH_BASE = "dc=b-and-qchina,dc=com"


def ldap_auth(username, password):
    ldap_server_pool = ServerPool(LDAP_SERVER_POOL)
    conn = Connection(ldap_server_pool, user=ADMIN_DN, password=ADMIN_PASSWORD, check_names=True, lazy=False, raise_exceptions=False)
    conn.open()
    conn.bind()

    res = conn.search( 
        search_base = SEARCH_BASE,
        search_filter = '(sAMAccountName={})'.format(username),
        search_scope = SUBTREE,
        attributes = ['cn', 'givenName', 'mail', 'sAMAccountName'],
        paged_size = 5
    )

    if res:
        entry = conn.response[0]
        dn = entry['dn']  
        attr_dict = entry['attributes']

        # check password by dn
        try:
            conn2 = Connection(ldap_server_pool, user=dn, password=password, check_names=True, lazy=False, raise_exceptions=False)
            conn2.bind() 
            if conn2.result["description"] == "success":
                print((True, attr_dict["mail"], attr_dict["sAMAccountName"], attr_dict["givenName"]))
                return (True, attr_dict["mail"], attr_dict["sAMAccountName"], attr_dict["givenName"])
            else:
                print("auth fail")
                return (False, None, None, None)
        except Exception as e:
            print("auth fail")
            return (False, None, None, None)
    else:
        return (False, None, None, None)


if __name__ == "__main__":
    print(ldap_auth(ADMIN_DN, ADMIN_PASSWORD))

