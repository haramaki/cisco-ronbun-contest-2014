import json
import requests


class APICController(object):

    def __init__(self, apic_ip):
        self.base_url = 'https://%s/api' % (apic_ip)

    def login(self, name, pwd):
        name_pwd = json.dumps(
        {'aaaUser': {'attributes': {'name': name, 'pwd': pwd}}})
        login_url = '%s/aaaLogin.json' % (self.base_url)
        # need login error handling
        post_response = requests.post(login_url, data=name_pwd, verify=False)
        # get token from login response structure
        auth = json.loads(post_response.text)
        login_attributes = auth['imdata'][0]['aaaLogin']['attributes']
        return login_attributes['token']

    def get_port_health(self, auth_token, switch):
        cookies = {}
        # set cookie
        cookies['APIC-cookie'] = auth_token
        # create health score URI
        request_url = '%s/mo/topology' % (self.base_url)
        if 'pod' in switch:
            request_url = '%s/pod-%s' % (request_url,switch['pod'])
        if 'node' in switch:
            request_url = '%s/node-%s' % (request_url,switch['node'])
        if 'slot' in switch:
            request_url = '%s/sys/ch/lcslot-%s' % (request_url,switch['slot'])
        if 'port' in switch:
            request_url = '%s/lc/leafport-%s' % (request_url,switch['port'])
        request_url = '%s/health.json' % (request_url)
        get_response = requests.get(request_url, cookies=cookies, verify=False) # return json data
        return get_response.json()

class OpenStackController(object):
    def __init__(self, os_ip):
        self.base_url='http://%s' % (os_ip)

    def login(self, name, pwd):
        login_url='%s:5000/v2.0/tokens/' % (self.base_url)
        name_pwd= {'auth': {'tenantName': 'admin', 'passwordCredentials': {'username': name, 'password': pwd}}}
        json_credentials = json.dumps(name_pwd)
        headers = {'content-type': 'application/json','accept':'application/json'}
        login_response = requests.post(login_url, data=json_credentials, headers=headers) auth = json.loads(login_response.text)
        token = auth['access']['token']['id']
        return token

    def post_sample(self,token,sample):
        post_headers={'X-Auth-Token':token,'content-type':'application/json',''
                                                                             'accept':'application/json'}
        json_data = json.dumps(sample)
        post_url = '%s:8777/v2/meters/healthscore' % (self.base_url)
        post_response = requests.post(post_url, data=json_data, headers=post_headers)
        return post_response.json()


def main():
    apic_info = {'ip': IPADDRESS, 'user': USER, 'pwd': PASSWORD}
    switch = {'pod': '1', 'node': '101', 'slot': '1', 'port': '1'}
    os_info = {'ip':IPADDRESS, 'user':USER,'pwd':PASSWORD} apic= APICController(apic_info['ip'])
    token = apic.login(apic_info['user'],apic_info['pwd']) json_data= apic.get_port_health(token,switch)
    score = json_data["imdata"][0]["healthInst"]["attributes"]["twScore"] openstack= OpenStackController(os_info['ip'])
    token = openstack.login(os_info['user'],os_info['pwd'])
    sample = [{'counter_name': 'healthscore','counter_type': 'gauge',
               'counter_unit': '%','counter_volume': float(score),
               'project_id': '9f8e3513a1fd4d9e9c60201d8b30e4d6',
               'resource_id': 'osp5com01.noslab.com',
               'user_id':'4a5e1a2207924fe7b4803e2d32d2aaa1'}]
    response = openstack.post_sample(token, sample)

    if __name__ == "__main__":
        main()
